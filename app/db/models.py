from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy import Column, String # type: ignore

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False)
