from fastapi import FastAPI, HTTPException # type: ignore
from datetime import datetime, timedelta
import hmac
import hashlib
import requests # type: ignore
import os
from pydantic import BaseModel # type: ignore

app = FastAPI()

shop_id = int(os.getenv("SHOP_ID", "0"))
partner_id = int(os.getenv("PARTNER_ID", "0"))
partner_key = os.getenv("PARTNER_KEY", "")
host = "https://partner.shopeemobile.com"

class OrderListResponse(BaseModel):
    order_list: list

def get_order_list(order_status: str, time_from: int, time_to: int, access_token: str):
    ts = int(datetime.timestamp(datetime.now()))
    path = "/api/v2/order/get_order_list"
    base_str = f"{partner_id}{path}{ts}{access_token}{shop_id}"
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
    content = response.json()

    if "response" in content and "order_list" in content["response"]:
        return content["response"]["order_list"]
    else:
        raise HTTPException(status_code=400, detail=content.get("error_message", "Failed to retrieve order list"))
