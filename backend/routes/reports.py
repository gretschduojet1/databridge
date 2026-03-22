from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from repositories.postgres.reports import PostgresReportsRepository
from repositories.interfaces.reports import ReportsRepositoryProtocol
from schemas.reports import SalesByRegionRow, MonthlyRevenueRow, LowStockRow, SummaryRow

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> ReportsRepositoryProtocol:
    return PostgresReportsRepository(db)


@router.get("/sales/by-region", response_model=list[SalesByRegionRow])
def sales_by_region(repo: ReportsRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    return repo.sales_by_region()


@router.get("/sales/monthly", response_model=list[MonthlyRevenueRow])
def sales_monthly(
    year: int | None = None,
    repo: ReportsRepositoryProtocol = Depends(get_repo),
    _: User = Depends(get_current_user),
):
    return repo.monthly_revenue(year=year)


@router.get("/inventory/low-stock", response_model=list[LowStockRow])
def low_stock(repo: ReportsRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    return repo.low_stock()


@router.get("/summary", response_model=SummaryRow)
def summary(repo: ReportsRepositoryProtocol = Depends(get_repo), _: User = Depends(get_current_user)):
    return repo.summary()
