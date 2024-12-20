from sqlalchemy.ext.declarative import declarative_base  # type: ignore
from sqlalchemy import Column, String, DateTime # type: ignore

Base = declarative_base()

class TokenLaz(Base):
    __tablename__ = "token_lazada"
    __table_args__ = {'schema': 'orderhub'}
    expiry_time = Column(DateTime, nullable=False)
    access_token = Column(String, primary_key=True)
    refresh_token = Column(String, nullable=False)

