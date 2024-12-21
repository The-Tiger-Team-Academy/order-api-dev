from fastapi import APIRouter, HTTPException
import lazop
from dotenv import load_dotenv
import os
from typing import Dict, Any
from ...utils.lazada.latest_access_token import get_latest_access_token_from_db

router = APIRouter(
    prefix='/lazada',
    tags=['Lazada']
)

load_dotenv()

LAZADA_URL = "https://api.lazada.co.th/rest"

def validate_environment() -> tuple[str, str]:
    appkey = os.getenv("LAZ_KEY")
    appSecret = os.getenv("LAZ_SECRET")
    
    if not appkey or not appSecret:
        raise HTTPException(
            status_code=500,
            detail="Missing Lazada API credentials in environment variables"
        )
    
    return appkey, appSecret

def create_lazada_client() -> tuple[lazop.LazopClient, str]:
    try:
        appkey, appSecret = validate_environment()
        access_token = get_latest_access_token_from_db()
        
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired access token"
            )
        
        client = lazop.LazopClient(LAZADA_URL, appkey, appSecret)
        return client, access_token
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Lazada client: {str(e)}"
        )

@router.get("/get_order_detail")
def laz_get_order_detail(order_id: str) -> Dict[str, Any]:
    try:
        if not order_id:
            raise HTTPException(
                status_code=400,
                detail="Order ID is required"
            )

        client, access_token = create_lazada_client()
        
        # Create request for order details
        request = lazop.LazopRequest('/order/items/get', 'GET')
        request.add_api_param('order_id', order_id)
        
        # Execute request
        response = client.execute(request, access_token)
        
        if not response or not response.body:
            raise HTTPException(
                status_code=404,
                detail=f"No details found for order ID: {order_id}"
            )
            
        return response.body
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch order details from Lazada: {str(e)}"
        )