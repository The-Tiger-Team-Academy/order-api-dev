from fastapi import Depends, HTTPException, APIRouter #type: ignore
from sqlalchemy.orm import Session #type: ignore
from typing import Dict, Any, Optional
from ..storehub.inventory_check import check_all_branches_inventory
from ...utils.shopee.get_order_detail import get_order_detiail
from ...utils.shopee.get_order_list import get_order_list
from datetime import datetime
from app.db.db_check_order import get_db
import traceback

router = APIRouter(
    prefix='/orders',
    tags=['Orders with Stock']
)

@router.get("/all_orders_with_stock")
def get_orders_with_stock(
    access_token: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    order_status: str = "READY_TO_SHIP",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    try:
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="Both start_date and end_date are required.")
        
        start_time = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

        if start_time > end_time:
            raise HTTPException(status_code=400, detail="start_date must be earlier than or equal to end_date.")

        order_list = get_order_list(order_status, start_time, end_time, access_token)
        if not order_list:
            return {"message": "No orders found.", "orders_with_stock": []}

        order_sn_list = ",".join([order["order_sn"] for order in order_list])
        order_details = get_order_detiail(
            order_sn_list=order_sn_list,
            access_token=access_token,
            response_optional_fields="buyer_username,pay_time,item_list"
        )

        if isinstance(order_details, dict) and 'order_details' in order_details:
            order_details = order_details['order_details']

        all_skus = list(set(
            item['model_sku'].strip() 
            for order in order_details 
            for item in order.get('item_list', []) 
            if item.get('model_sku')
        ))

        valid_skus = [sku for sku in all_skus if sku]
        if not valid_skus:
            raise HTTPException(status_code=400, detail="No valid SKUs found.")

        sku_str = ",".join(valid_skus)

        inventory_response = check_all_branches_inventory(sku=sku_str, db=db)

        inventory_data = inventory_response.get('inventory', [])
        if not inventory_data:
            print("Error: Inventory data is missing or empty.")
            raise HTTPException(status_code=500, detail="Error fetching inventory data.")

        inventory_dict = {
            inv['barcode']: inv
            for inv in inventory_data
        }

        for order in order_details:
            for item in order.get('item_list', []):
                sku = item.get('model_sku', '').strip()
                stock_info = inventory_dict.get(sku, {"branches": [], "track_stock_level": False})

                item['stock_details'] = {
                    'total_branches': len(stock_info.get('branches', [])),
                    'total_stock': sum(
                        branch['quantity'] for branch in stock_info.get('branches', [])
                    ),
                    'branches_with_stock': [
                        branch for branch in stock_info.get('branches', [])
                        if branch['has_stock']
                    ]
                }

        return {
            "total_orders": len(order_details),
            "orders_with_stock": order_details
        }

    except Exception as e:
        print("Exception traceback:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing orders: {str(e)}")
