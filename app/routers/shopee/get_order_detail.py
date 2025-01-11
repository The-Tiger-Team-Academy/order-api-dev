from fastapi import HTTPException # type: ignore
from fastapi import APIRouter # type: ignore
import hmac
import hashlib
from dotenv import load_dotenv # type: ignore
import os
import requests # type: ignore
import json
from datetime import datetime
from ...utils.shopee.latest_access_token import get_latest_access_token_from_db

load_dotenv()


router = APIRouter(
prefix='/shopee',
tags = ['Shopee']
)


shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
host = "https://partner.shopeemobile.com"

@router.get('/get_order_detail')
async def get_order_detiail(order_sn_list: str ,request_order_status_pending=True, response_optional_fields="buyer_username,pay_time,item_list"):
    access_token = get_latest_access_token_from_db()
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
        return {"order_details": content["response"]["order_list"]}
    else:
        raise HTTPException(status_code=400, detail=content.get("message", "Failed to retrieve order details"))
