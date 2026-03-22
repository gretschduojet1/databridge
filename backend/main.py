from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from core.middleware import SecurityHeadersMiddleware
from routes import customers, products, orders, auth, reports, jobs
import tasks.reports   # noqa: F401 — registers event handlers
import tasks.exports   # noqa: F401
import tasks.sweeper   # noqa: F401

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Databridge API",
    description="Multi-source data viewer and reporting API",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
