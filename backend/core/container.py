"""
Service bindings — the single place to swap implementations.

Equivalent to Laravel's AppServiceProvider::register(). Each function
is a FastAPI dependency: routes declare what they need via Depends(),
and this module decides which concrete class they get.

    # To switch the export writer to plain text:
    def get_export_writer() -> WriterProtocol:
        return TextWriter()

    # To switch all repositories to a different database:
    def get_customer_repo(db: Session = Depends(get_db)) -> CustomerRepositoryProtocol:
        return MongoCustomerRepository(db)
"""

from sqlalchemy.orm import Session
from fastapi import Depends

from core.database import get_db
from writers.interfaces.writer import WriterProtocol
from writers.excel import ExcelWriter
from repositories.interfaces.customer import CustomerRepositoryProtocol
from repositories.interfaces.product import ProductRepositoryProtocol
from repositories.interfaces.order import OrderRepositoryProtocol
from repositories.interfaces.reports import ReportsRepositoryProtocol
from repositories.interfaces.job import JobRepositoryProtocol
from repositories.interfaces.user import UserRepositoryProtocol
from repositories.postgres.customer import PostgresCustomerRepository
from repositories.postgres.product import PostgresProductRepository
from repositories.postgres.order import PostgresOrderRepository
from repositories.postgres.reports import PostgresReportsRepository
from repositories.postgres.job import PostgresJobRepository
from repositories.postgres.user import PostgresUserRepository


def get_export_writer() -> WriterProtocol:
    return ExcelWriter()


def get_customer_repo(db: Session = Depends(get_db)) -> CustomerRepositoryProtocol:
    return PostgresCustomerRepository(db)


def get_product_repo(db: Session = Depends(get_db)) -> ProductRepositoryProtocol:
    return PostgresProductRepository(db)


def get_order_repo(db: Session = Depends(get_db)) -> OrderRepositoryProtocol:
    return PostgresOrderRepository(db)


def get_reports_repo(db: Session = Depends(get_db)) -> ReportsRepositoryProtocol:
    return PostgresReportsRepository(db)


def get_job_repo(db: Session = Depends(get_db)) -> JobRepositoryProtocol:
    return PostgresJobRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepositoryProtocol:
    return PostgresUserRepository(db)
