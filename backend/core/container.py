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

from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from mailers.interfaces.mailer import MailerProtocol
from mailers.smtp import SmtpMailer
from repositories.interfaces.customer import CustomerRepositoryProtocol
from repositories.interfaces.job import JobRepositoryProtocol
from repositories.interfaces.order import OrderRepositoryProtocol
from repositories.interfaces.product import ProductRepositoryProtocol
from repositories.interfaces.reports import ReportsRepositoryProtocol
from repositories.interfaces.store import StoreRepositoryProtocol
from repositories.interfaces.user import UserRepositoryProtocol
from repositories.postgres.customer import PostgresCustomerRepository
from repositories.postgres.job import PostgresJobRepository
from repositories.postgres.order import PostgresOrderRepository
from repositories.postgres.product import PostgresProductRepository
from repositories.postgres.reports import PostgresReportsRepository
from repositories.postgres.store import PostgresStoreRepository
from repositories.postgres.user import PostgresUserRepository
from writers.excel import ExcelWriter
from writers.interfaces.writer import WriterProtocol


def get_export_writer() -> WriterProtocol:
    return ExcelWriter()


def get_mailer() -> MailerProtocol:
    return SmtpMailer()


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


def get_store_repo(db: Session = Depends(get_db)) -> StoreRepositoryProtocol:
    return PostgresStoreRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepositoryProtocol:
    return PostgresUserRepository(db)
