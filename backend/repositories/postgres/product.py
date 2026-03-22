from sqlalchemy.orm import Session
from models.product import Product
from schemas.product import ProductCreate


class PostgresProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100, category: str | None = None) -> list[Product]:
        q = self.db.query(Product)
        if category:
            q = q.filter(Product.category == category)
        return q.offset(skip).limit(limit).all()

    def get_by_id(self, id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == id).first()

    def create(self, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
