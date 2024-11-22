from fastapi import HTTPException  # type: ignore
from dotenv import load_dotenv  # type: ignore
import os
import requests  # type: ignore
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth  # type: ignore
from utils.getAllOrder import getAllOrder  # Import the function



load_dotenv()

STOREHUB_API_BASE_URL = "http://api.storehubhq.com"
STOREHUB_API_USERNAME = os.getenv("STOREHUB_API_USERNAME")
STOREHUB_API_PASSWORD = os.getenv("STOREHUB_API_PASSWORD")


def compareOrdersWithStoreProducts(access_token: str, start_date: str, end_date: str):
    try:
        # Step 1: ดึงข้อมูล SKU จาก Shopee Orders
        orders_response = getAllOrder(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )

        # ดึง SKU จาก Order
        if "order_details" not in orders_response or not isinstance(orders_response["order_details"], list):
            return {"message": "No order details found.", "matched_items": [], "unmatched_items": []}

        order_details = orders_response["order_details"]
        order_skus = set(item["model_sku"] for order in order_details for item in order.get("item_list", []))

        if not order_skus:
            return {"message": "No SKUs found in orders.", "matched_items": [], "unmatched_items": []}

        # Step 2: ดึงข้อมูลสินค้าจาก StoreHub (Batch Processing)
        storehub_response = requests.get(
            f"{STOREHUB_API_BASE_URL}/products",
            auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
        )

        if storehub_response.status_code != 200:
            raise HTTPException(status_code=storehub_response.status_code, detail="Failed to fetch StoreHub products.")

        storehub_products = storehub_response.json()
        storehub_skus = set(product["sku"] for product in storehub_products)

        # Step 3: เปรียบเทียบ SKU
        matched_items = [{"sku": sku} for sku in order_skus if sku in storehub_skus]
        unmatched_items = [{"sku": sku} for sku in order_skus if sku not in storehub_skus]

        return {
            "message": "Comparison complete.",
            "matched_items": matched_items,
            "unmatched_items": unmatched_items,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare orders: {str(e)}")



def compareStoreOrders(access_token: str, store_id: str, start_date: str, end_date: str):
    """
    Compare orders from Shopee with SKUs available in a specific StoreHub store.
    """
    try:
        # Step 1: Fetch orders from Shopee
        orders_response = getAllOrder(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )

        # Validate the orders_response structure
        if not isinstance(orders_response, dict):
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from getAllOrder."
            )

        # Check if there are order details
        if "order_details" not in orders_response or not isinstance(orders_response["order_details"], list):
            return {
                "message": "No order details found in the specified date range.",
                "matched_items": [],
                "unmatched_items": [],
            }

        order_details = orders_response["order_details"]

        # Step 2: Fetch SKUs from the StoreHub API for the given store
        store_skus = getSkuByStore(store_id)  # ใช้ฟังก์ชัน getSkuByStore เพื่อดึงเฉพาะ SKU

        # Validate the StoreHub SKU response
        if not isinstance(store_skus, list):
            raise HTTPException(
                status_code=500,
                detail="Invalid response format from StoreHub SKU API."
            )

        # Convert StoreHub SKUs to a set for quick lookup
        store_sku_set = set(store_skus)

        # Step 3: Compare SKUs in orders with StoreHub SKUs
        matched_items = []
        unmatched_items = []

        for order in order_details:
            if "item_list" not in order or not isinstance(order["item_list"], list):
                continue

            for item in order["item_list"]:
                if "model_sku" not in item:
                    continue

                order_sku = item["model_sku"]

                # Check if the SKU exists in StoreHub inventory
                if order_sku in store_sku_set:
                    matched_items.append({
                        "order_sn": order.get("order_sn", "Unknown"),
                        "model_sku": order_sku,
                        "quantity_ordered": item.get("model_quantity_purchased", 0),
                    })
                else:
                    unmatched_items.append({
                        "order_sn": order.get("order_sn", "Unknown"),
                        "model_sku": order_sku,
                        "quantity_ordered": item.get("model_quantity_purchased", 0),
                    })

        return {
            "message": "Comparison complete.",
            "matched_items": matched_items,
            "unmatched_items": unmatched_items,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare orders: {str(e)}")