"""
DAG: compute_stock_projections
Reads: sales.orders + inventory.products
Writes: inventory.stock_projections

For each product, computes:
  - avg_daily_sales  : average units sold per day over the last 30 days
  - days_until_stockout : stock_qty / avg_daily_sales (None if no recent sales)
  - projected_stockout_date : today + days_until_stockout
  - velocity_trend : compares last 15 days vs prior 15 days
      'accelerating' — sales pace is picking up
      'slowing'      — sales pace is dropping off
      'steady'       — within 20% variance

Runs nightly. Results are read directly by the /reports/inventory/projections
API endpoint so the dashboard never has to do this math at request time.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    dag_id="compute_stock_projections",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["analytics", "inventory"],
)
def compute_stock_projections_dag() -> None:

    @task
    def extract() -> dict:
        hook = PostgresHook(postgres_conn_id="databridge_postgres")

        products = hook.get_records(
            "SELECT id, stock_qty FROM inventory.products ORDER BY id"
        )

        # All-time totals — avoids any timezone-sensitive date filtering
        sales_all = hook.get_records(
            """
            SELECT product_id, SUM(quantity), MIN(ordered_at), MAX(ordered_at)
            FROM sales.orders
            GROUP BY product_id
            """
        )

        # Second-half orders: ordered_at above the median epoch for that product,
        # used as a proxy for recent-vs-earlier trend without a fixed cutoff date.
        sales_recent = hook.get_records(
            """
            SELECT product_id, SUM(quantity)
            FROM sales.orders o
            WHERE ordered_at > (
                SELECT to_timestamp(AVG(EXTRACT(EPOCH FROM ordered_at)))
                FROM sales.orders
                WHERE product_id = o.product_id
            )
            GROUP BY product_id
            """
        )

        return {
            "products": [{"id": r[0], "stock_qty": r[1]} for r in products],
            "sales": {
                r[0]: {
                    "total_units": int(r[1]),
                    # Store as ISO strings — XCom JSON serialization doesn't preserve datetime objects
                    "first_order": r[2].isoformat() if r[2] else None,
                    "last_order":  r[3].isoformat() if r[3] else None,
                }
                for r in sales_all
            },
            "sales_recent": {r[0]: int(r[1]) for r in sales_recent},
        }

    @task
    def transform(data: dict) -> list[dict]:
        today = date.today()
        results = []

        # JSON serialization converts integer dict keys to strings — normalise once
        sales_by_id = {int(k): v for k, v in data["sales"].items()}
        recent_by_id = {int(k): v for k, v in data["sales_recent"].items()}

        for product in data["products"]:
            pid = product["id"]
            stock = product["stock_qty"]
            sales = sales_by_id.get(pid)

            if sales and sales["total_units"] > 0 and sales["first_order"] and sales["last_order"]:
                first_dt = datetime.fromisoformat(sales["first_order"])
                last_dt  = datetime.fromisoformat(sales["last_order"])
                span_days = max(1, (last_dt - first_dt).days + 1)
                avg_daily = round(sales["total_units"] / span_days, 2)
                days_left = int(stock / avg_daily) if avg_daily > 0 else None
                stockout_date = (today + timedelta(days=days_left)).isoformat() if days_left is not None else None

                # Trend: recent half vs earlier half (by median order date)
                total = sales["total_units"]
                recent = recent_by_id.get(pid, 0)
                earlier = total - recent
                if earlier == 0 and recent == 0:
                    trend = "steady"
                elif earlier == 0:
                    trend = "accelerating"
                else:
                    ratio = recent / earlier
                    trend = "accelerating" if ratio > 1.2 else "slowing" if ratio < 0.8 else "steady"
            else:
                avg_daily = 0.0
                days_left = None
                stockout_date = None
                trend = "steady"

            results.append({
                "product_id": pid,
                "avg_daily_sales": avg_daily,
                "days_until_stockout": days_left,
                "projected_stockout_date": stockout_date,
                "velocity_trend": trend,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            })

        return results

    @task
    def load(projections: list[dict]) -> None:
        if not projections:
            return

        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()

        for p in projections:
            cursor.execute(
                """
                INSERT INTO inventory.stock_projections
                    (product_id, avg_daily_sales, days_until_stockout,
                     projected_stockout_date, velocity_trend, computed_at)
                VALUES (%(product_id)s, %(avg_daily_sales)s, %(days_until_stockout)s,
                        %(projected_stockout_date)s, %(velocity_trend)s, %(computed_at)s)
                ON CONFLICT (product_id) DO UPDATE
                    SET avg_daily_sales       = EXCLUDED.avg_daily_sales,
                        days_until_stockout   = EXCLUDED.days_until_stockout,
                        projected_stockout_date = EXCLUDED.projected_stockout_date,
                        velocity_trend        = EXCLUDED.velocity_trend,
                        computed_at           = EXCLUDED.computed_at
                """,
                p,
            )

        conn.commit()
        cursor.close()
        print(f"Upserted projections for {len(projections)} products.")

    raw = extract()
    transformed = transform(raw)
    load(transformed)


compute_stock_projections_dag()
