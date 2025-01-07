from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from ...utils.lazada.latest_access_token import get_latest_access_token_from_db as get_lazada_token
from ...utils.shopee.latest_access_token import get_latest_access_token_from_db as get_shopee_token
from ...routers.lazada.all_orders import get_orders_with_details as get_lazada_orders
from ...routers.shopee.get_all_order import get_all_order as get_shopee_orders
from ...routers.shopee.refresh_token_shopee import refreshToken

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/marketplace',
    tags=['Marketplace Orders']
)

def normalize_order_structure(orders: List[Dict], source: str) -> List[Dict]:
    normalized_orders = []
    if source == 'lazada':
        for order in orders:
            normalized_order = {
                'marketplace': 'Lazada',
                'order_number': order.get('order_number', ''),
                'total_price': order.get('total_price', '0.00'),
                'payment_method': order.get('payment_method', ''),
                'items_count': order.get('items_count', '0'),
                'status': order.get('statuses', [''])[0] if order.get('statuses') else '',
                'customer_name': order.get('billing_first_name', ''),
                'create_time': order.get('created_at', ''),
                'items': [
                    {
                        'product_id': item.get('product_id', ''),
                        'sku': item.get('sku', ''),
                        'product_main_image': item.get('product_main_image', ''),
                        'paid_price': item.get('paid_price', '0.00'),
                        'item_price': item.get('item_price', '0.00'),
                        'fulfillment_sla': item.get('fulfillment_sla', ''),
                    } for item in order.get('items', [])
                ]
            }
            normalized_orders.append(normalized_order)
    
    elif source == 'shopee':
        for order in orders:
            normalized_order = {
                'marketplace': 'Shopee',
                'order_number': order.get('order_sn', ''),
                'total_price': str(sum(item.get('model_discounted_price', 0) for item in order.get('item_list', []))),
                'payment_method': order.get('payment_method', ''),
                'items_count': str(len(order.get('item_list', []))),
                'status': order.get('order_status', ''),
                'customer_name': order.get('buyer_username', ''),
                'create_time': order.get('create_time', ''),
                'items': [
                    {
                        'product_id': str(item.get('item_id', '')),
                        'sku': item.get('model_sku', ''),
                        'product_main_image': item.get('image_info', {}).get('image_url', ''),
                        'paid_price': str(item.get('model_discounted_price', '0.00')),
                        'item_price': str(item.get('model_original_price', '0.00')),
                        'fulfillment_sla': f"Ship by {datetime.fromtimestamp(order.get('ship_by_date', 0)).strftime('%Y-%m-%d')}"
                    } for item in order.get('item_list', [])
                ]
            }
            normalized_orders.append(normalized_order)
    
    return normalized_orders

async def safe_get_lazada_orders(status: str):
    try:
        lazada_response = await get_lazada_orders(status)
        if lazada_response.get('code') == '0':
            return lazada_response
        else:
            logger.error(f"Lazada order fetch failed: {lazada_response}")
            return {'data': {'orders': []}}
    except Exception as e:
        logger.error(f"Error fetching Lazada orders: {str(e)}")
        return {'data': {'orders': []}}

async def safe_get_shopee_orders(start_date: str, end_date: str, status: str):
    try:
        status = status.upper()
        
        logger.info(f"Attempting to fetch Shopee orders - Status: {status}, Date Range: {start_date} to {end_date}")
        
        try:
            access_token = get_shopee_token()
            logger.info("Successfully retrieved Shopee access token")
        except Exception as token_err:
            logger.error(f"Failed to retrieve Shopee access token: {str(token_err)}")
            return {'order_details': []}

        try:
            shopee_response = await get_shopee_orders(
                order_status=status,
                start_date=start_date,
                end_date=end_date
            )
            
            logger.info(f"Shopee response type: {type(shopee_response)}")
            logger.info(f"Shopee response keys: {shopee_response.keys() if isinstance(shopee_response, dict) else 'N/A'}")
        except Exception as fetch_err:
            logger.error(f"Exception during Shopee order fetch: {str(fetch_err)}")
            refreshToken()
            return {'order_details': []}
        
        if isinstance(shopee_response, dict):
            if 'order_details' in shopee_response:
                logger.info(f"Successfully retrieved {len(shopee_response.get('order_details', []))} Shopee orders")
                return shopee_response
            elif 'error' in shopee_response:
                logger.error(f"Shopee order fetch error: {shopee_response.get('error', 'Unknown error')}")
                return {'order_details': []}
            else:
                logger.warning(f"Unexpected Shopee response structure: {shopee_response}")
                return {'order_details': []}
        else:
            logger.error(f"Invalid Shopee response type: {type(shopee_response)}")
            return {'order_details': []}
    
    except Exception as e:
        logger.error(f"Unexpected error in safe_get_shopee_orders: {str(e)}")
        return {'order_details': []}
    
@router.get("/get_all_orders")
async def get_unified_marketplace_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status_shopee: Optional[str] = "READY_TO_SHIP",
    status_lazada: Optional[str] = "ready_to_ship",
) -> Dict[str, Any]:
    try:
        if not start_date or not end_date:
            today = datetime.now()
            end_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            start_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")

        lazada_response = await safe_get_lazada_orders(status_lazada)
        shopee_response = await safe_get_shopee_orders(start_date, end_date, status_shopee)

        lazada_orders = lazada_response.get('data', {}).get('orders', [])
        shopee_orders = shopee_response.get('order_details', [])

        logger.info(f"Fetched {len(lazada_orders)} Lazada orders")
        logger.info(f"Fetched {len(shopee_orders)} Shopee orders")

        try:
            normalized_lazada = normalize_order_structure(lazada_orders, 'lazada')
            normalized_shopee = normalize_order_structure(shopee_orders, 'shopee')
        except Exception as normalize_err:
            logger.error(f"Error normalizing orders: {str(normalize_err)}")
            normalized_lazada = []
            normalized_shopee = []

        all_orders = normalized_lazada + normalized_shopee

        return {
            "total_orders": len(all_orders),
            "orders": all_orders
        }

    except Exception as e:
        logger.error(f"Unexpected error in get_unified_marketplace_orders: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching marketplace orders: {str(e)}")