from fastapi import APIRouter, HTTPException
import lazop
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from ...utils.lazada.latest_access_token import get_latest_access_token_from_db

router = APIRouter(
    prefix='/lazada',
    tags=['Lazada']
)

load_dotenv()

LAZADA_URL = "https://api.lazada.co.th/rest"
# Thailand is UTC+7
THAI_OFFSET = timedelta(hours=7)
THAI_TIMEZONE = timezone(THAI_OFFSET)

def validate_environment() -> tuple[str, str]:
    """Validate required environment variables."""
    appkey = os.getenv("LAZ_KEY")
    appSecret = os.getenv("LAZ_SECRET")
    
    if not appkey or not appSecret:
        raise HTTPException(
            status_code=500,
            detail="Missing Lazada API credentials in environment variables"
        )
    
    return appkey, appSecret

def create_lazada_client() -> tuple[lazop.LazopClient, str]:
    """Create Lazada client with proper configuration."""
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

@router.get("/get_orders")
def laz_get_orders() -> Dict[str, Any]:
    """
    Fetch orders from Lazada API with ready_to_ship status for the last 15 days.
    Returns JSON response with order details.
    """
    try:
        client, access_token = create_lazada_client()
        
        # Create request for orders
        request = lazop.LazopRequest('/orders/get', 'GET')
        
        # Set parameters
        request.add_api_param('offset', '0')
        request.add_api_param('limit', '10')
        
        # Calculate 15 days ago in Thai timezone
        current_time = datetime.now(THAI_TIMEZONE)
        fifteen_days_ago = current_time - timedelta(days=15)
        formatted_time = fifteen_days_ago.strftime('%Y-%m-%dT%H:%M:%S+07:00')
        request.add_api_param('update_after', formatted_time)
        
        request.add_api_param('sort_by', 'created_at')
        request.add_api_param('status', 'ready_to_ship')
        
        # Execute request
        response = client.execute(request, access_token)
        
        if not response or not response.body:
            raise HTTPException(
                status_code=404,
                detail="No orders found or empty response from Lazada"
            )
            
        return response.body
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch orders from Lazada: {str(e)}"
        )