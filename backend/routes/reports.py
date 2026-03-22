from fastapi import APIRouter, Depends

from core.container import get_reports_repo
from core.dependencies import get_current_user
from models.user import User
from repositories.interfaces.reports import ReportsRepositoryProtocol
from schemas.reports import LowStockRow, MonthlyRevenueRow, SalesByRegionRow, SummaryRow

router = APIRouter()


@router.get("/sales/by-region", response_model=list[SalesByRegionRow])
def sales_by_region(
    repo: ReportsRepositoryProtocol = Depends(get_reports_repo), _: User = Depends(get_current_user)
) -> list[SalesByRegionRow]:
    return repo.sales_by_region()


@router.get("/sales/monthly", response_model=list[MonthlyRevenueRow])
def sales_monthly(
    year: int | None = None,
    repo: ReportsRepositoryProtocol = Depends(get_reports_repo),
    _: User = Depends(get_current_user),
) -> list[MonthlyRevenueRow]:
    return repo.monthly_revenue(year=year)


@router.get("/inventory/low-stock", response_model=list[LowStockRow])
def low_stock(
    repo: ReportsRepositoryProtocol = Depends(get_reports_repo), _: User = Depends(get_current_user)
) -> list[LowStockRow]:
    return repo.low_stock()


@router.get("/summary", response_model=SummaryRow)
def summary(
    repo: ReportsRepositoryProtocol = Depends(get_reports_repo), _: User = Depends(get_current_user)
) -> SummaryRow:
    return repo.summary()
