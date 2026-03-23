from fastapi import APIRouter, Depends, HTTPException, Query

from core.container import get_store_repo
from core.dependencies import get_current_user
from models.user import User
from repositories.interfaces.store import StoreRepositoryProtocol
from schemas.pagination import Page
from schemas.store import StoreDetail, StoreSummary

router = APIRouter()


@router.get("/", response_model=Page[StoreSummary])
def list_stores(
    skip: int = 0,
    limit: int = Query(default=25, le=200),
    region: str | None = None,
    search: str | None = None,
    low_stock_only: bool = False,
    repo: StoreRepositoryProtocol = Depends(get_store_repo),
    _: User = Depends(get_current_user),
) -> Page[StoreSummary]:
    return Page(
        items=repo.get_all(skip=skip, limit=limit, region=region, search=search, low_stock_only=low_stock_only),
        total=repo.count(region=region, search=search, low_stock_only=low_stock_only),
        skip=skip,
        limit=limit,
    )


@router.get("/{id}", response_model=StoreDetail)
def get_store(
    id: int,
    repo: StoreRepositoryProtocol = Depends(get_store_repo),
    _: User = Depends(get_current_user),
) -> StoreDetail:
    store = repo.get_by_id(id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store
