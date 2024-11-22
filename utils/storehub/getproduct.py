import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.db import SessionLocal, Base 
from sqlalchemy import Column, String
from sqlalchemy.exc import IntegrityError
from requests.auth import HTTPBasicAuth

from db.models import Product
import os

load_dotenv()

STOREHUB_API_BASE_URL = "http://api.storehubhq.com"
STOREHUB_API_USERNAME = os.getenv("STOREHUB_API_USERNAME")
STOREHUB_API_PASSWORD = os.getenv("STOREHUB_API_PASSWORD")


# Define the Product model for the database
class StoreHubProduct(Base):
    __tablename__ = "storehub_products"
    id = Column(String, primary_key=True)  # StoreHub Product ID
    name = Column(String, nullable=False)  # Product Name
    sku = Column(String, unique=True, nullable=False)  # SKU

# Ensure the table is created in the database
Base.metadata.create_all(bind=SessionLocal().bind)


def fetch_products_from_storehub():
    """
    Fetch all products from StoreHub API.
    """
    try:
        response = requests.get(
            f"{STOREHUB_API_BASE_URL}/products",
            auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch products from StoreHub."
            )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")


def fetch_and_store_products():
    try:
        # Fetch products from StoreHub API
        response = requests.get(
            f"{STOREHUB_API_BASE_URL}/products",
            auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch products from StoreHub.",
            )

        products = response.json()

        # Filter valid products (must have id and sku)
        filtered_products = [
            {"id": product.get("id"), "name": product.get("name"), "sku": product.get("sku")}
            for product in products
            if product.get("id") and product.get("sku")
        ]

        # Batch size
        batch_size = 100  # Adjust this size based on your database capacity

        # Save products to database in batches
        with SessionLocal() as session:
            for i in range(0, len(filtered_products), batch_size):
                batch = filtered_products[i:i + batch_size]
                session.bulk_insert_mappings(Product, batch)
                session.commit()

        return {"message": "Products fetched and stored successfully.", "count": len(filtered_products)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching or storing products: {str(e)}")

def get_products_from_db(db: Session):
    """
    ดึงข้อมูลผลิตภัณฑ์ทั้งหมดจากฐานข้อมูล PostgreSQL
    """
    try:
        products = db.query(Product).all()
        return {"products": [product.__dict__ for product in products]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")
