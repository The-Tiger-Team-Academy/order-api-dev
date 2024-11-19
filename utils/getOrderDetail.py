from fastapi import HTTPException # type: ignore
import hmac
import hashlib
from dotenv import load_dotenv # type: ignore
import os
import requests # type: ignore
import json
from datetime import datetime
load_dotenv()

shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
host = "https://partner.shopeemobile.com"

def getOrderDetail(order_sn_list: str, access_token: str, request_order_status_pending=False, response_optional_fields="buyer_username,pay_time,item_list"):
    ts = int(datetime.timestamp(datetime.now()))
    path = "/api/v2/order/get_order_detail"
    base_str = str(partner_id) + path + str(ts) + access_token + str(shop_id)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

    url = (
        f"{host}{path}"
        f"?access_token={access_token}"
        f"&order_sn_list={order_sn_list}"
        f"&partner_id={partner_id}"
        f"&shop_id={shop_id}"
        f"&sign={sign}"
        f"&timestamp={ts}"
    )

    if request_order_status_pending:
        url += "&request_order_status_pending=true"
    if response_optional_fields:
        url += f"&response_optional_fields={response_optional_fields}"

    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers, allow_redirects=False)
    content = json.loads(response.content)

    if content.get("error") == "" and "order_list" in content.get("response", {}):
        return {"order_detail": content["response"]["order_list"]}
    else:
        raise HTTPException(status_code=400, detail=content.get("message", "Failed to retrieve order details"))