import requests
from requests.auth import HTTPBasicAuth
from fastapi import HTTPException
from os import getenv
from dotenv import load_dotenv

# โหลด environment variables
load_dotenv()

# ดึงค่า BASE URL และข้อมูลการตรวจสอบสิทธิ์จาก environment variables
STOREHUB_API_BASE_URL = getenv("STOREHUB_API_BASE_URL")
STOREHUB_API_USERNAME = getenv("STOREHUB_API_USERNAME")
STOREHUB_API_PASSWORD = getenv("STOREHUB_API_PASSWORD")

def check_sku_in_stores(sku: str):
    """
    ค้นหา SKU ในทุก store และตรวจสอบว่าสินค้านั้นมีในสต็อกของ store ไหนบ้าง
    """
    try:
        if not STOREHUB_API_BASE_URL or not STOREHUB_API_USERNAME or not STOREHUB_API_PASSWORD:
            raise HTTPException(
                status_code=500,
                detail="STOREHUB_API_BASE_URL, STOREHUB_API_USERNAME, or STOREHUB_API_PASSWORD is not defined in .env file"
            )

        # ใช้ HTTPBasicAuth สำหรับการตรวจสอบสิทธิ์
        auth = HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD)

        # Step 1: Fetch all stores
        stores_response = requests.get(f"{STOREHUB_API_BASE_URL}/stores", auth=auth)
        if stores_response.status_code != 200:
            raise HTTPException(
                status_code=stores_response.status_code,
                detail=f"Failed to fetch stores: {stores_response.text}"
            )
        
        stores_data = stores_response.json()
        store_inventory = {}

        # Step 2: Iterate through each store to check inventory
        for store in stores_data:
            store_id = store.get("id")
            store_name = store.get("name")

            # Fetch inventory for the current store
            inventory_response = requests.get(f"{STOREHUB_API_BASE_URL}/inventory/{store_id}", auth=auth)
            if inventory_response.status_code != 200:
                continue  # Skip store if inventory API fails
            
            inventory_data = inventory_response.json()

            # Check if SKU exists in inventory
            for item in inventory_data:
                if item["productId"] == sku:
                    store_inventory[store_name] = {
                        "store_id": store_id,
                        "quantityOnHand": item["quantityOnHand"]
                    }
                    break

        # Step 3: Return result
        if not store_inventory:
            return {
                "message": f"SKU {sku} not found in any store.",
                "store_inventory": store_inventory
            }

        return {
            "message": f"SKU {sku} found in the following stores.",
            "store_inventory": store_inventory
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check SKU in stores: {str(e)}")
