from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from repositories.postgres.order import PostgresOrderRepository
from repositories.interfaces.order import OrderRepositoryProtocol
from schemas.order import OrderCreate, OrderRead
from schemas.pagination import Page

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> OrderRepositoryProtocol:
    return PostgresOrderRepository(db)


@router.get("/", response_model=Page[OrderRead])
def list_orders(
    skip: int = 0,
    limit: int = Query(default=25, le=200),
    customer_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    repo: OrderRepositoryProtocol = Depends(get_repo),
    _: User = Depends(get_current_user),
):
    return Page(
        items=repo.get_all(skip=skip, limit=limit, customer_id=customer_id, date_from=date_from, date_to=date_to, sort_by=sort_by, sort_order=sort_order),
        total=repo.count(customer_id=customer_id, date_from=date_from, date_to=date_to),
        skip=skip,
        limit=limit,
    )


@router.get("/{id}", response_model=OrderRead)
def get_order(id: int, repo: OrderRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    order = repo.get_by_id(id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderRead, status_code=201)
def create_order(body: OrderCreate, repo: OrderRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    return repo.create(body)
