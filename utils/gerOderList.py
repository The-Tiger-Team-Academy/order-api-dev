from fastapi import HTTPException  # type: ignore
import hmac
import hashlib
import requests  # type: ignore
import json
from datetime import datetime, timedelta
import os
from pydantic import BaseModel  # type: ignore

shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
host = "https://partner.shopeemobile.com"


class OrderListResponse(BaseModel):
    order_list: list


def getOrderList(order_status: str, time_from: int, time_to: int, access_token: str):
    """
    Fetch the order list from Shopee API for the given time range and order status.
    """
    ts = int(datetime.timestamp(datetime.now()))
    path = "/api/v2/order/get_order_list"
    base_str = str(partner_id) + path + str(ts) + access_token + str(shop_id)
    sign = hmac.new(partner_key.encode("utf-8"), base_str.encode("utf-8"), hashlib.sha256).hexdigest()

    url = (
        f"{host}{path}?access_token={access_token}"
        f"&order_status={order_status}"
        f"&page_size=100&partner_id={partner_id}"
        f"&response_optional_fields=order_status&shop_id={shop_id}"
        f"&sign={sign}"
        f"&time_from={time_from}&time_range_field=create_time"
        f"&time_to={time_to}&timestamp={ts}"
    )

    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers, allow_redirects=False)
    content = json.loads(response.content)

    if "response" in content and "order_list" in content["response"]:
        return content["response"]["order_list"]
    else:
        raise HTTPException(status_code=400, detail="Failed to retrieve order list")


def getOrderListEndpoint(access_token: str, order_status: str, date: str = None):
    """
    Endpoint function to get the order list for a specific date and order status.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    selected_date = datetime.strptime(date, "%Y-%m-%d")
    start_time = int(datetime.timestamp(selected_date))
    end_time = int(datetime.timestamp(selected_date + timedelta(days=1)) - 1)

    order_list = getOrderList(order_status, start_time, end_time, access_token)
    return OrderListResponse(order_list=order_list)
