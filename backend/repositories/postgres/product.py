from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from models.product import Product
from schemas.product import ProductCreate

SORTABLE_FIELDS = {"name", "sku", "category", "stock_qty", "updated_at"}


class PostgresProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 25, category: str | None = None, sort_by: str | None = None, sort_order: str = "asc") -> list[Product]:
        q = self.db.query(Product)
        if category:
            q = q.filter(Product.category == category)
        if sort_by and sort_by in SORTABLE_FIELDS:
            col = getattr(Product, sort_by)
            q = q.order_by(asc(col) if sort_order == "asc" else desc(col))
        return q.offset(skip).limit(limit).all()

    def count(self, category: str | None = None) -> int:
        q = self.db.query(Product)
        if category:
            q = q.filter(Product.category == category)
        return q.count()

    def get_by_id(self, id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == id).first()

    def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def export_all(self) -> tuple[list[str], list]:
        columns = ["ID", "SKU", "Name", "Category", "Stock", "Reorder At", "Updated"]
        rows = (
            self.db.query(Product.id, Product.sku, Product.name, Product.category, Product.stock_qty, Product.reorder_level, Product.updated_at)
            .order_by(Product.name)
            .all()
        )
        return columns, rows
