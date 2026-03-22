from fastapi import FastAPI
from routes import customers, products, orders

app = FastAPI(
    title="Databridge API",
    description="Multi-source data viewer and reporting API",
    version="0.1.0",
)

app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
