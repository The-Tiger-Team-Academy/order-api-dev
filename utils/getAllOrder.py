from fastapi import HTTPException # type: ignore
from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel # type: ignore
from dotenv import load_dotenv # type: ignore
import os
import requests # type: ignore
from datetime import datetime
from utils.getOrderDetail import getOrderDetail
from utils.generateSign import generateSign
load_dotenv()

shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
host = "https://partner.shopeemobile.com"


class CombinedResponse(BaseModel):
    order_detail: Optional[List[Dict[str, Any]]] = None
    order_list_error: Optional[str] = None
    order_detail_error: Optional[str] = None

def getAllOrder(
    start_date: str,
    end_date: str,
    access_token: str,
    order_status: str = "READY_TO_SHIP",
    request_order_status_pending: bool = False,
    response_optional_fields: str = "buyer_username,pay_time,item_list",
):
    """
    Fetch all orders within a given date range.
    """
    try:
        start_time = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    ts = int(datetime.timestamp(datetime.now()))
    path = "/api/v2/order/get_order_list"
    sign = generateSign(path, ts, access_token)

    url = (
        f"{host}{path}?access_token={access_token}"
        f"&order_status={order_status}"
        f"&partner_id={partner_id}&shop_id={shop_id}"
        f"&time_from={start_time}&time_to={end_time}"
        f"&response_optional_fields={response_optional_fields}"
        f"&timestamp={ts}&sign={sign}"
    )

    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch orders.")

    data = response.json()
    order_list = data.get("response", {}).get("order_list", [])
    order_sn_list = ",".join([order["order_sn"] for order in order_list])

    if order_sn_list:
        try:
            details = getOrderDetail(order_sn_list, access_token)
            return CombinedResponse(order_detail=details["order_detail"])
        except Exception as e:
            return CombinedResponse(
                order_detail=[],
                order_list_error=None,
                order_detail_error=str(e),
            )
    else:
        return CombinedResponse(order_detail=[], order_list_error=None, order_detail_error="No orders found.")