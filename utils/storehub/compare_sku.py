from sqlalchemy.orm import Session
from fastapi import HTTPException
from db.db import SessionLocal, Product
import requests


def fetch_and_compare_skus(access_token: str, start_date: str, end_date: str):
    """
    Fetch orders from Shopee API, then compare item_sku from orders with SKUs in the database.
    """
    try:
        # Step 1: Fetch orders from Shopee API
        response = requests.get(
            "http://localhost:8000/get_all_orders",
            params={
                "access_token": access_token,
                "start_date": start_date,
                "end_date": end_date,
                "order_status": "READY_TO_SHIP",
                "response_optional_fields": "buyer_username,pay_time,item_list"
            }
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch orders: {response.text}"
            )

        # Parse response JSON
        order_data = response.json()
        if "order_details" not in order_data or not order_data["order_details"].get("order_details", []):
            raise HTTPException(status_code=404, detail="No order details found.")

        # Step 2: Fetch products from the database
        db: Session = SessionLocal()
        products_in_db = db.query(Product.id, Product.sku, Product.name).all()
        db.close()

        # Transform products into a dictionary for quick lookup
        product_map = {sku: {"id": id_, "name": name} for id_, sku, name in products_in_db}

        # Step 3: Extract item_sku from orders
        order_details = order_data["order_details"]["order_details"]
        order_skus = [
            {"item_sku": item["item_sku"], "item_name": item.get("item_name", "")}
            for order in order_details
            for item in order.get("item_list", [])
            if "item_sku" in item
        ]

        # Step 4: Compare SKUs and return enriched data
        matched_items = []
        unmatched_items = []

        for order_sku in order_skus:
            sku = order_sku["item_sku"]
            if sku in product_map:
                matched_items.append({
                    "id": product_map[sku]["id"],
                    "sku": sku,
                    "name": product_map[sku]["name"],
                })
            else:
                unmatched_items.append({
                    "sku": sku,
                    "name": order_sku["item_name"]
                })

        return {
            "message": "Comparison complete.",
            "matched_items": matched_items,
            "unmatched_items": unmatched_items,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare SKUs: {str(e)}")
