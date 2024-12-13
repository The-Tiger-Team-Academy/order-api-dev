from fastapi import HTTPException, APIRouter  # type: ignore
from datetime import datetime
from typing import Optional, Dict, Any
from ...utils.shopee.get_order_detail import get_order_detiail
from ...utils.shopee.get_order_list import get_order_list


router = APIRouter(
prefix='/shopee',
tags = ['Shopee']
)

@router.get("/get_all_orders", response_model=Dict[str, Any])
def get_all_order(
    access_token: str,
    order_status: str = "READY_TO_SHIP",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request_order_status_pending: Optional[bool] = False,
    response_optional_fields: Optional[str] = "buyer_username,pay_time,item_list",
) -> Dict[str, Any]:
    try:
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="Both start_date and end_date are required.")

        start_time = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

        if start_time > end_time:
            raise HTTPException(status_code=400, detail="start_date must be earlier than or equal to end_date.")

        order_list = get_order_list(order_status, start_time, end_time, access_token)

        order_sn_list = ",".join([order["order_sn"] for order in order_list])

        if not order_sn_list:
            return {"message": "No orders found."}

        order_details = get_order_detiail(
            order_sn_list=order_sn_list,
            access_token=access_token,
            request_order_status_pending=request_order_status_pending,
            response_optional_fields=response_optional_fields,
        )
        
        return order_details

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch all orders and details: {str(e)}")
