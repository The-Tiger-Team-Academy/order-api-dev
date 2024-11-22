import requests
from dotenv import load_dotenv
import os
from requests.auth import HTTPBasicAuth
from fastapi import HTTPException

load_dotenv()

STOREHUB_API_BASE_URL = "http://api.storehubhq.com"
STOREHUB_API_USERNAME = os.getenv("STOREHUB_API_USERNAME")
STOREHUB_API_PASSWORD = os.getenv("STOREHUB_API_PASSWORD")


def getAllProducts():
    """
    Fetch all products from StoreHub.
    """
    try:
        response = requests.get(
            f"{STOREHUB_API_BASE_URL}/products",
            auth=HTTPBasicAuth(STOREHUB_API_USERNAME, STOREHUB_API_PASSWORD),
        )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch products from StoreHub.",
            )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")
