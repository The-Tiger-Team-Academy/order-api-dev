from fastapi import HTTPException  # type: ignore
from dotenv import load_dotenv  # type: ignore
import os
import requests  # type: ignore
from requests.auth import HTTPBasicAuth  # type: ignore

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()

# StoreHub API Base URL และ Credentials จาก .env
STOREHUB_API_BASE_URL = "http://api.storehubhq.com"
STOREHUB_API_USERNAME = os.getenv("STOREHUB_API_USERNAME")
STOREHUB_API_PASSWORD = os.getenv("STOREHUB_API_PASSWORD")


def getSkuByStore(store_id: str):
    """
    ดึง SKU ของสินค้าที่มี `quantityOnHand > 0` ใน store ที่ระบุ
    """
    try:
        # เรียกข้อมูล inventory ของ store
        inventory_response = requests.get(
            f"{STOREHUB_API_BASE_URL}/inventory/{store_id}",
            auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
        )

        if inventory_response.status_code != 200:
            raise HTTPException(
                status_code=inventory_response.status_code,
                detail=f"Failed to fetch inventory for store ID {store_id}.",
            )

        inventory_data = inventory_response.json()

        # กรองเฉพาะสินค้าที่มี quantityOnHand > 0
        available_products = [
            product["productId"]
            for product in inventory_data
            if product["quantityOnHand"] > 0
        ]

        if not available_products:
            return {"message": "No products available in the store.", "skus": []}

        # ดึง SKU สำหรับ productId ที่มีสินค้าใน stock
        skus = []
        for product_id in available_products:
            product_response = requests.get(
                f"{STOREHUB_API_BASE_URL}/products/{product_id}",
                auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
            )
            if product_response.status_code == 200:
                product_data = product_response.json()
                skus.append(product_data["sku"])

        return {"store_id": store_id, "skus": skus}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch SKUs: {str(e)}")
