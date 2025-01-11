from fastapi import APIRouter
import lazop
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from ...utils.lazada.latest_access_token import get_latest_access_token_from_db

router = APIRouter(
    prefix='/lazada',
    tags=['Lazada']
)

load_dotenv()

def get_lazada_client():
    url = "https://api.lazada.co.th/rest"
    appkey = os.getenv("LAZ_KEY")
    appSecret = os.getenv("LAZ_SECRET")
    return lazop.LazopClient(url, appkey, appSecret)

def fetch_orders(client: Any, access_token: str, status: str) -> Dict:
    current_time = datetime.utcnow() + timedelta(hours=8)
    day = current_time - timedelta(days=10)
    update_after = day.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    request = lazop.LazopRequest('/orders/get', 'GET')
    request.add_api_param('offset', '0')
    request.add_api_param('limit', '100')
    request.add_api_param('update_after', update_after)
    request.add_api_param('sort_by', 'created_at')
    request.add_api_param('status', status)
    response = client.execute(request, access_token)
    return response.body

def fetch_order_details(client: Any, access_token: str, order_id: str) -> Dict:
    request = lazop.LazopRequest('/order/items/get', 'GET')
    request.add_api_param('order_id', order_id)
    response = client.execute(request, access_token)
    return response.body

def filter_order_info(order: Dict) -> Dict:
    billing_address = order.get("address_billing", {})
    
    return {
        "order_number": order.get("order_number", ""),
        "total_price": str(order.get("price", "0.00")),
        "payment_method": order.get("payment_method", ""),
        "created_at": order.get("created_at", ""),
        "items_count": str(order.get("items_count", "0")),
        "statuses": order.get("statuses", []),
        "billing_first_name": billing_address.get("first_name", "")
    }

def filter_item_info(item: Dict) -> Dict:
    return {
        "product_id": item.get("product_id", ""),
        "sku": item.get("sku", ""),
        "fulfillment_sla": item.get("fulfillment_sla", ""),
        "order_type": item.get("order_type", ""),
        "product_main_image": item.get("product_main_image", ""),
        "paid_price": str(item.get("paid_price", "0.00")),
        "item_price": str(item.get("item_price", "0.00")),
        "shipping_fee_discount_platform": str(item.get("shipping_fee_discount_platform", "0.00")),
    }

@router.get("/get_orders_with_details")
async def get_orders_with_details(status: str):
    try:
        access_token = get_latest_access_token_from_db()
        client = get_lazada_client()
        
        orders_response = fetch_orders(client, access_token, status)
        
        if orders_response.get('code') != '0':
            return {"error": "Failed to fetch orders", "details": orders_response}
        
        orders = orders_response.get('data', {}).get('orders', [])
        combined_orders = []
        
        for order in orders:
            order_id = str(order['order_id'])
            order_details = fetch_order_details(client, access_token, order_id)
            
            if order_details.get('code') == '0':
                order_info = filter_order_info(order)
                filtered_items = [
                    filter_item_info(item) 
                    for item in order_details.get('data', [])
                ]
                
                combined_order = {
                    **order_info,  
                    "items": filtered_items 
                }
                combined_orders.append(combined_order)
        
        return {
            "code": "0",
            "data": {
                "count": str(len(combined_orders)),
                "countTotal": str(orders_response.get('data', {}).get('countTotal', "0")),
                "orders": combined_orders
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to process orders: {str(e)}"}