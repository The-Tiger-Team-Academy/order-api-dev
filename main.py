from fastapi import FastAPI, HTTPException, Depends
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel
import hmac
import hashlib
import time
import urllib.parse
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
code = os.getenv("CODE")
shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
redirect_url = os.getenv("REDIRECT_URL")
host = "https://partner.test-stable.shopeemobile.com"
initial_refresh_token = "464977474a496c4f4f50595071465370"  # Provided refresh token

# Global storage for tokens
tokens = {
    "access_token": None,
    "refresh_token": initial_refresh_token,
    "expiry_time": None
}

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class CombinedResponse(BaseModel):
    order_list: Optional[list]
    order_detail: Optional[list]
    order_list_error: Optional[str] = None
    order_detail_error: Optional[str] = None

class OrderListResponse(BaseModel):
    order_list: list

class OrderDetailResponse(BaseModel):
    order_detail: Union[dict, list]


def refresh_token():
    global tokens
    ts = int(datetime.timestamp(datetime.now()))
    body = {"shop_id": shop_id, "partner_id": partner_id, "refresh_token": tokens["refresh_token"]}

    path = "/api/v2/auth/access_token/get"
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

    url = f"{host}{path}?partner_id={partner_id}&timestamp={ts}&sign={sign}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=body, headers=headers)
    content = json.loads(response.content)

    if "access_token" in content and "refresh_token" in content:
        tokens["access_token"] = content["access_token"]
        tokens["refresh_token"] = content["refresh_token"]
        tokens["expiry_time"] = datetime.now() + timedelta(hours=4)
    else:
        raise HTTPException(status_code=400, detail="Token refresh failed")

def get_access_token():
    # Check if token needs refreshing
    if tokens["access_token"] is None or tokens["expiry_time"] <= datetime.now():
        refresh_token()
    return tokens["access_token"]

@app.get("/auth")
def auth():
    ts = int(time.time())
    path = "/api/v2/shop/auth_partner"
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()
    encoded_redirect_url = urllib.parse.quote(redirect_url)

    url = f"{host}{path}?partner_id={partner_id}&redirect={encoded_redirect_url}&timestamp={ts}&sign={sign}"
    return {"auth_url": url}

@app.get("/get_token", response_model=TokenResponse)
def get_token():
    global tokens
    ts = int(time.time())
    body = {"code": code, "shop_id": shop_id, "partner_id": partner_id}

    path = "/api/v2/auth/token/get"
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

    url = f"{host}{path}?partner_id={partner_id}&timestamp={ts}&sign={sign}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=body, headers=headers)
    content = json.loads(response.content)

    if "access_token" in content and "refresh_token" in content:
        tokens["access_token"] = content["access_token"]
        tokens["refresh_token"] = content["refresh_token"]
        tokens["expiry_time"] = datetime.now() + timedelta(hours=4)
    else:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"]
    )

def get_order_list(order_status: str, time_from: int, time_to: int, access_token: str):
    ts = int(datetime.timestamp(datetime.now()))
    path = "/api/v2/order/get_order_list"
    base_str = str(partner_id) + path + str(ts) + access_token + str(shop_id)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

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

@app.post("/get_order_list", response_model=OrderListResponse)
def get_order_list_endpoint(order_status: str, date: str = None, access_token: str = Depends(get_access_token)):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    selected_date = datetime.strptime(date, "%Y-%m-%d")
    start_time = int(datetime.timestamp(selected_date))
    end_time = int(datetime.timestamp(selected_date + timedelta(days=1)) - 1)

    order_list = get_order_list(order_status, start_time, end_time, access_token)
    return OrderListResponse(order_list=order_list)

def get_order_detail(order_sn_list: str, access_token: str, request_order_status_pending=False, response_optional_fields="buyer_username,pay_time,item_list"):
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

@app.post("/get_all_orders", response_model=CombinedResponse)
def get_all_orders(
    start_date: str,
    end_date: str,
    order_status: str = "READY_TO_SHIP",
    request_order_status_pending: bool = False,
    response_optional_fields: str = "buyer_username,pay_time,item_list",
    access_token: str = Depends(get_access_token)
):
    combined_result: Dict[str, Any] = {}

    # Convert start and end date to timestamps
    try:
        start_time = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Fetch order list
    try:
        order_list = get_order_list(
            order_status=order_status,
            time_from=start_time,
            time_to=end_time,
            access_token=access_token
        )
        combined_result["order_list"] = order_list

        # Prepare order_sn_list for fetching order details
        if order_list:
            order_sn_list = ",".join([order["order_sn"] for order in order_list])
        else:
            order_sn_list = None

    except HTTPException as e:
        combined_result["order_list_error"] = e.detail
        order_sn_list = None

    # Fetch order details if order_sn_list is available
    if order_sn_list:
        try:
            order_detail = get_order_detail(
                order_sn_list=order_sn_list,
                access_token=access_token,
                request_order_status_pending=request_order_status_pending,
                response_optional_fields=response_optional_fields
            )
            combined_result["order_detail"] = order_detail["order_detail"]
        except HTTPException as e:
            combined_result["order_detail_error"] = e.detail
    else:
        combined_result["order_detail_error"] = "No orders found for the specified date range."

    if not combined_result:
        raise HTTPException(status_code=400, detail="No valid request parameters provided.")

    return combined_result
