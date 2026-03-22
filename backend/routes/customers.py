from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from repositories.postgres.customer import PostgresCustomerRepository
from repositories.interfaces.customer import CustomerRepositoryProtocol
from schemas.customer import CustomerCreate, CustomerRead

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> CustomerRepositoryProtocol:
    return PostgresCustomerRepository(db)


@router.get("/", response_model=list[CustomerRead])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    region: str | None = None,
    repo: CustomerRepositoryProtocol = Depends(get_repo),
):
    return repo.get_all(skip=skip, limit=limit, region=region)


@router.get("/{id}", response_model=CustomerRead)
def get_customer(id: int, repo: CustomerRepositoryProtocol = Depends(get_repo)):
    customer = repo.get_by_id(id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/", response_model=CustomerRead, status_code=201)
def create_customer(body: CustomerCreate, repo: CustomerRepositoryProtocol = Depends(get_repo)):
    return repo.create(body)
