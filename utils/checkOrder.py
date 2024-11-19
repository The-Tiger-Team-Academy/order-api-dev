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

def checkOrders(access_token: str):
    """
    Check inventory for all orders within today and tomorrow.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        orders_response = getAllOrder(
            start_date=today,
            end_date=tomorrow,
            access_token=access_token,
        )

        if not orders_response.order_detail:
            raise HTTPException(status_code=404, detail="No orders found.")

        store_response = requests.get(
            f"{STOREHUB_API_BASE_URL}/stores",
            auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
        )
        if store_response.status_code != 200:
            raise HTTPException(
                status_code=store_response.status_code,
                detail="Failed to fetch store data.",
            )

        stores = store_response.json()
        inventory_status = []

        for order in orders_response.order_detail:
            for item in order["item_list"]:
                model_sku = item["model_sku"]

                for store in stores:
                    store_id = store["id"]
                    inventory_response = requests.get(
                        f"{STOREHUB_API_BASE_URL}/inventory/{store_id}",
                        auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
                    )
                    if inventory_response.status_code != 200:
                        continue

                    inventory_data = inventory_response.json()
                    matching_inventory = next(
                        (i for i in inventory_data if i["productId"] == model_sku), None
                    )

                    if matching_inventory:
                        product_response = requests.get(
                            f"{STOREHUB_API_BASE_URL}/products/{matching_inventory['productId']}",
                            auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
                        )
                        product_data = (
                            product_response.json()
                            if product_response.status_code == 200
                            else {}
                        )

                        inventory_status.append(
                            {
                                "order_sn": order["order_sn"],
                                "model_sku": model_sku,
                                "store_name": store["name"],
                                "quantity_on_hand": matching_inventory["quantityOnHand"],
                                "product_name": product_data.get("name", "Details unavailable"),
                                "product_sku": product_data.get("sku", model_sku),
                            }
                        )

        return {"inventory_status": inventory_status}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
