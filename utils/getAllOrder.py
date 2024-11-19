from fastapi import HTTPException  # type: ignore
from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from utils.getOrderDetail import getOrderDetail
from utils.getOrderList import getOrderList  # แก้ไขตามชื่อไฟล์ของคุณ


def getAllOrder(
    access_token: str,
    order_status: str = "READY_TO_SHIP",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request_order_status_pending: Optional[bool] = False,
    response_optional_fields: Optional[str] = "buyer_username,pay_time,item_list",
) -> Dict[str, Any]:
    """
    Function to fetch all orders and their details for a specific date range and status.
    """
    try:
        # ตรวจสอบและแปลงวันที่
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="Both start_date and end_date are required.")

        start_time = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

        if start_time > end_time:
            raise HTTPException(status_code=400, detail="start_date must be earlier than or equal to end_date.")

        # Step 1: Call getOrderList
        order_list = getOrderList(order_status, start_time, end_time, access_token)

        # Step 2: Extract order_sn_list
        order_sn_list = ",".join([order["order_sn"] for order in order_list])

        if not order_sn_list:
            return {"message": "No orders found."}

        # Step 3: Call getOrderDetail
        order_details = getOrderDetail(
            order_sn_list=order_sn_list,
            access_token=access_token,
            request_order_status_pending=request_order_status_pending,
            response_optional_fields=response_optional_fields,
        )

        # Step 4: Return combined result
        return {
            "order_list": order_list,
            "order_details": order_details,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch all orders and details: {str(e)}")
