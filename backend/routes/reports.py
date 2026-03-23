from fastapi import APIRouter, Depends

from core.container import get_reports_repo
from core.dependencies import get_current_user
from models.user import User
from repositories.interfaces.reports import ReportsRepositoryProtocol
from schemas.reports import (
    LowStockRow,
    MonthlyRevenueRow,
    SalesByRegionRow,
    StockAlertRow,
    StockHealthRow,
    StockProjectionRow,
    SummaryRow,
)

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


@router.get("/inventory/stock-alerts", response_model=list[StockAlertRow])
def stock_alerts(
    limit: int = 10,
    repo: ReportsRepositoryProtocol = Depends(get_reports_repo),
    _: User = Depends(get_current_user),
) -> list[StockAlertRow]:
    return repo.stock_alerts(limit=limit)


@router.get("/inventory/stock-health", response_model=list[StockHealthRow])
def stock_health(
    limit: int = 10,
    repo: ReportsRepositoryProtocol = Depends(get_reports_repo),
    _: User = Depends(get_current_user),
) -> list[StockHealthRow]:
    return repo.stock_health(limit=limit)


@router.get("/inventory/projections", response_model=list[StockProjectionRow])
def stock_projections(
    repo: ReportsRepositoryProtocol = Depends(get_reports_repo), _: User = Depends(get_current_user)
) -> list[StockProjectionRow]:
    return repo.stock_projections()


@router.get("/summary", response_model=SummaryRow)
def summary(
    repo: ReportsRepositoryProtocol = Depends(get_reports_repo), _: User = Depends(get_current_user)
) -> SummaryRow:
    return repo.summary()
