from fastapi import APIRouter, Depends, HTTPException, Query

from core.container import get_customer_repo
from core.dependencies import get_current_user
from models.customer import Customer
from models.user import User
from repositories.interfaces.customer import CustomerRepositoryProtocol
from schemas.customer import CustomerCreate, CustomerRead
from schemas.pagination import Page

router = APIRouter()


@router.get("/", response_model=Page[CustomerRead])
def list_customers(
    skip: int = 0,
    limit: int = Query(default=25, le=200),
    region: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    repo: CustomerRepositoryProtocol = Depends(get_customer_repo),
    _: User = Depends(get_current_user),
) -> Page[CustomerRead]:
    return Page(
        items=repo.get_all(skip=skip, limit=limit, region=region, sort_by=sort_by, sort_order=sort_order),
        total=repo.count(region=region),
        skip=skip,
        limit=limit,
    )


@router.get("/{id}", response_model=CustomerRead)
def get_customer(
    id: int,
    repo: CustomerRepositoryProtocol = Depends(get_customer_repo),
    _: User = Depends(get_current_user),
) -> Customer:
    customer = repo.get_by_id(id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/", response_model=CustomerRead, status_code=201)
def create_customer(
    body: CustomerCreate,
    repo: CustomerRepositoryProtocol = Depends(get_customer_repo),
    _: User = Depends(get_current_user),
) -> Customer:
    return repo.create(body)
