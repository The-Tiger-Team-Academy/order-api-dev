from sqlalchemy.ext.declarative import declarative_base  # type: ignore
from sqlalchemy import Column, String, DateTime # type: ignore

Base = declarative_base()

class TokenShopee(Base):
    __tablename__ = "token_shopee"
    access_token = Column(String, primary_key=True)
    refresh_token = Column(String, nullable=False)
    expiry_time = Column(DateTime, nullable=False)