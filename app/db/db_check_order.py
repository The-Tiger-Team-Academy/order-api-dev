from sqlalchemy.ext.declarative import declarative_base  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore
from dotenv import load_dotenv  # type: ignore
import os
from sqlalchemy import create_engine  # type: ignore
from urllib.parse import quote_plus

load_dotenv() 

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PASSWORD = "{5$HxHG3F@V6"
DB_HOST = os.getenv("DB_HOST")
DB_PORT = (os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")

DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

DATABASE_URL = f"postgresql://postgres:{DB_PASSWORD_ENCODED}@119.59.103.15:5432/orderhub_warehouse"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()