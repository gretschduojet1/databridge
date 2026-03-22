from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from repositories.postgres.product import PostgresProductRepository
from repositories.interfaces.product import ProductRepositoryProtocol
from schemas.product import ProductCreate, ProductRead
from schemas.pagination import Page

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> ProductRepositoryProtocol:
    return PostgresProductRepository(db)


@router.get("/", response_model=Page[ProductRead])
def list_products(
    skip: int = 0,
    limit: int = Query(default=25, le=200),
    category: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    repo: ProductRepositoryProtocol = Depends(get_repo),
    _: User = Depends(get_current_user),
):
    return Page(
        items=repo.get_all(skip=skip, limit=limit, category=category, sort_by=sort_by, sort_order=sort_order),
        total=repo.count(category=category),
        skip=skip,
        limit=limit,
    )


@router.get("/{id}", response_model=ProductRead)
def get_product(id: int, repo: ProductRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    product = repo.get_by_id(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductRead, status_code=201)
def create_product(body: ProductCreate, repo: ProductRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    return repo.create(body)
