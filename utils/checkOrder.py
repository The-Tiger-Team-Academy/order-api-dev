from datetime import datetime
import logging
from fastapi import HTTPException
from typing import Optional
from utils.getAllOrder import getAllOrder
import requests
from requests.auth import HTTPBasicAuth
import os
import time

STOREHUB_API_BASE_URL = "http://api.storehubhq.com"
STOREHUB_API_USERNAME = os.getenv("STOREHUB_API_USERNAME")
STOREHUB_API_PASSWORD = os.getenv("STOREHUB_API_PASSWORD")

def checkOrders(
    access_token: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    try:
        logging.debug(f"Received start_date: {start_date}, end_date: {end_date}")

        # Validate start_date and end_date
        if not isinstance(start_date, str) or not isinstance(end_date, str):
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date must be strings in 'YYYY-MM-DD' format.",
            )

        # Start timing the order fetching process
        start_time = time.time()

        # Fetch orders
        logging.debug("Fetching orders...")
        orders_response = getAllOrder(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )
        logging.debug(f"Orders response: {orders_response}")

        fetch_orders_time = time.time() - start_time
        logging.info(f"Time taken to fetch orders: {fetch_orders_time:.2f} seconds")

        # Extract and validate order details
        order_details_container = orders_response.get("order_details", {})
        if not isinstance(order_details_container, dict):
            raise HTTPException(
                status_code=500,
                detail=f"Invalid order_details format: {order_details_container}",
            )
        order_details = order_details_container.get("order_details", [])
        if not isinstance(order_details, list):
            raise HTTPException(
                status_code=500,
                detail=f"Invalid order_details structure: {order_details}",
            )

        if not order_details:
            raise HTTPException(status_code=404, detail="No orders found.")

        # Fetch stores
        logging.debug("Fetching stores...")
        start_fetch_stores_time = time.time()

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
        logging.debug(f"Stores fetched: {stores}")

        fetch_stores_time = time.time() - start_fetch_stores_time
        logging.info(f"Time taken to fetch stores: {fetch_stores_time:.2f} seconds")

        inventory_status = []

        for order in order_details:
            for item in order.get("item_list", []):
                model_sku = item.get("model_sku")
                item_name = item.get("item_name")
                if not model_sku:
                    logging.warning(f"Item missing model_sku: {item}")
                    continue

                item_found = False
                start_inventory_time = time.time()

                for store in stores:
                    store_id = store.get("id")
                    store_name = store.get("name")
                    if not store_id:
                        logging.warning(f"Store missing ID: {store}")
                        continue

                    # Fetch inventory
                    inventory_response = requests.get(
                        f"{STOREHUB_API_BASE_URL}/inventory/{store_id}",
                        auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
                    )
                    if inventory_response.status_code != 200:
                        logging.warning(f"Failed to fetch inventory for store {store_id}")
                        continue

                    inventory_data = inventory_response.json()
                    if not isinstance(inventory_data, list):
                        logging.warning(f"Invalid inventory data for store {store_id}")
                        continue

                    # Find matching inventory
                    matching_inventory = next(
                        (i for i in inventory_data if i.get("productId") == model_sku), None
                    )

                    if matching_inventory:
                        item_found = True
                        inventory_status.append(
                            {
                                "order_sn": order.get("order_sn"),
                                "item_name": item_name,
                                "model_sku": model_sku,
                                "store_name": store_name,
                                "quantity_on_hand": matching_inventory.get("quantityOnHand"),
                            }
                        )

                inventory_fetch_time = time.time() - start_inventory_time
                logging.info(f"Time taken to fetch inventory for item {item_name}: {inventory_fetch_time:.2f} seconds")

                if not item_found:
                    inventory_status.append(
                        {
                            "order_sn": order.get("order_sn"),
                            "item_name": item_name,
                            "model_sku": model_sku,
                            "store_name": None,
                            "quantity_on_hand": 0,
                            "status": "Item not found in inventory",
                        }
                    )

        return {"inventory_status": inventory_status}

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
