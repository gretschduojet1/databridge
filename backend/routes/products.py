from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from repositories.postgres.product import PostgresProductRepository
from repositories.interfaces.product import ProductRepositoryProtocol
from schemas.product import ProductCreate, ProductRead

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> ProductRepositoryProtocol:
    return PostgresProductRepository(db)


@router.get("/", response_model=list[ProductRead])
def list_products(
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    repo: ProductRepositoryProtocol = Depends(get_repo),
    _: User = Depends(get_current_user),
):
    return repo.get_all(skip=skip, limit=limit, category=category)


@router.get("/{id}", response_model=ProductRead)
def get_product(id: int, repo: ProductRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    product = repo.get_by_id(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductRead, status_code=201)
def create_product(body: ProductCreate, repo: ProductRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    return repo.create(body)
