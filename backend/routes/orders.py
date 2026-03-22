from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from repositories.postgres.order import PostgresOrderRepository
from repositories.interfaces.order import OrderRepositoryProtocol
from schemas.order import OrderCreate, OrderRead

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> OrderRepositoryProtocol:
    return PostgresOrderRepository(db)


@router.get("/", response_model=list[OrderRead])
def list_orders(
    skip: int = 0,
    limit: int = 100,
    customer_id: int | None = None,
    repo: OrderRepositoryProtocol = Depends(get_repo),
):
    return repo.get_all(skip=skip, limit=limit, customer_id=customer_id)


@router.get("/{id}", response_model=OrderRead)
def get_order(id: int, repo: OrderRepositoryProtocol = Depends(get_repo)):
    order = repo.get_by_id(id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderRead, status_code=201)
def create_order(body: OrderCreate, repo: OrderRepositoryProtocol = Depends(get_repo)):
    return repo.create(body)
