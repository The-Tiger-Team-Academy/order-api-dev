from sqlalchemy.ext.declarative import declarative_base  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore
from sqlalchemy import create_engine, Column, String, DateTime# type: ignore
from dotenv import load_dotenv  # type: ignore
import os

load_dotenv() 

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = (os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Define the Token model
class Token(Base):
    __tablename__ = "tokens"
    access_token = Column(String, primary_key=True)
    refresh_token = Column(String, nullable=False)
    expiry_time = Column(DateTime, nullable=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=False)

# Ensure the table exists
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()