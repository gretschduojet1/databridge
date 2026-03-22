from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import customers, products, orders

app = FastAPI(
    title="Databridge API",
    description="Multi-source data viewer and reporting API",
    version="0.1.0",
)

# Allow the Svelte dev server to call the API from the browser.
# In production this would be locked down to the actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
