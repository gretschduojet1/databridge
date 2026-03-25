from datetime import UTC, datetime

from models.customer import Customer
from repositories.interfaces.connection import DataConnectionProtocol
from schemas.customer import CustomerCreate

SORTABLE_FIELDS = {"name", "email", "region", "created_at"}


class PostgresCustomerRepository:
    def __init__(self, conn: DataConnectionProtocol):
        self.conn = conn

    def get_all(
        self,
        skip: int = 0,
        limit: int = 25,
        region: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ) -> list[Customer]:
        conditions = []
        params: dict = {"limit": limit, "skip": skip}

        if region:
            conditions.append("region = :region")
            params["region"] = region

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        order_col = sort_by if sort_by and sort_by in SORTABLE_FIELDS else "name"
        order_dir = "DESC" if sort_order == "desc" else "ASC"

        sql = f"""
            SELECT id, name, email, region, created_at
            FROM customers.customers
            {where}
            ORDER BY {order_col} {order_dir}
            LIMIT :limit OFFSET :skip
        """  # noqa: S608 — order_col is whitelisted, where uses only literal strings
        return [Customer(**row) for row in self.conn.fetch_all(sql, params)]

    def count(self, region: str | None = None) -> int:
        params: dict = {}
        where = ""
        if region:
            where = "WHERE region = :region"
            params["region"] = region
        result = self.conn.fetch_one(
            f"SELECT COUNT(*) AS count FROM customers.customers {where}",  # noqa: S608
            params,
        )
        return int(result["count"]) if result else 0

    def get_by_id(self, id: int) -> Customer | None:
        row = self.conn.fetch_one(
            "SELECT id, name, email, region, created_at FROM customers.customers WHERE id = :id",
            {"id": id},
        )
        return Customer(**row) if row else None

    def create(self, data: CustomerCreate) -> Customer:
        params = {**data.model_dump(), "created_at": datetime.now(UTC)}
        row = self.conn.fetch_one(
            """
            INSERT INTO customers.customers (name, email, region, created_at)
            VALUES (:name, :email, :region, :created_at)
            RETURNING id, name, email, region, created_at
            """,
            params,
        )
        self.conn.commit()
        return Customer(**row)  # type: ignore[arg-type]

    def export_all(self) -> tuple[list[str], list]:
        columns = ["ID", "Name", "Email", "Region", "Joined"]
        rows = self.conn.fetch_all(
            "SELECT id, name, email, region, created_at FROM customers.customers ORDER BY name"
        )
        return columns, [(r["id"], r["name"], r["email"], r["region"], r["created_at"]) for r in rows]
