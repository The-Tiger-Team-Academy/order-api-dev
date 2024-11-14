from fastapi import FastAPI, HTTPException, Query
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
from typing import Union
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Union, Dict, Any,Optional

load_dotenv()

# Get values from .env
code = os.getenv("CODE")
shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
redirect_url = os.getenv("REDIRECT_URL")


host = "https://partner.test-stable.shopeemobile.com"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change to a list of specific origins for security)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (adjust if necessary)
    allow_headers=["*"],  # Allows all headers (adjust if necessary)
)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class CombinedResponse(BaseModel):
    order_list: Optional[list]
    order_detail: Optional[list]

class OrderListResponse(BaseModel):
    order_list: list

class OrderDetailResponse(BaseModel):
    order_detail: Union[dict, list]


# Model สำหรับกำหนดรูปแบบการตอบกลับ
class CombinedResponse(BaseModel):
    order_list: Optional[list]
    order_detail: Optional[list]
    order_list_error: Optional[str] = None
    order_detail_error: Optional[str] = None
    

@app.get("/auth")
def auth():
    ts = int(time.time())
    path = "/api/v2/shop/auth_partner"
    
    # Create base string for signature
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

    # Encode the redirect URL
    encoded_redirect_url = urllib.parse.quote(redirect_url)

    # Construct the final URL
    url = f"{host}{path}?partner_id={partner_id}&redirect={encoded_redirect_url}&timestamp={ts}&sign={sign}"

    return {
        "auth_url": url,
    }

@app.get("/get_token", response_model=TokenResponse)
def get_token():
    ts = int(time.time())
    body = {"code": code, "shop_id": shop_id, "partner_id": partner_id}

    path = "/api/v2/auth/token/get"
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

    url = f"{host}{path}?partner_id={partner_id}&timestamp={ts}&sign={sign}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=body, headers=headers)
    content = json.loads(response.content)

    # ตรวจสอบว่าค่าที่ได้จาก API มี access_token และ refresh_token หรือไม่
    access_token = content.get("access_token")
    refresh_token = content.get("refresh_token")

    if access_token is None or refresh_token is None:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token or refresh token")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/refresh_token", response_model=TokenResponse)
def refresh_token_endpoint(refresh_token: str):
    ts = int(datetime.timestamp(datetime.now()))
    body = {"shop_id": shop_id, "partner_id": partner_id, "refresh_token": refresh_token}

    path = "/api/v2/auth/access_token/get"
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

    url = f"{host}{path}?partner_id={partner_id}&timestamp={ts}&sign={sign}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=body, headers=headers)
    content = json.loads(response.content)

    return TokenResponse(
        access_token=content.get("access_token"),
        refresh_token=content.get("refresh_token")
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
def get_order_list_endpoint(order_status: str, days_ago: int = 10, access_token: str = "YOUR_ACCESS_TOKEN"):
    # Calculate start and end times
    end_time = int(datetime.timestamp(datetime.now()))
    start_time = int(datetime.timestamp(datetime.now() - timedelta(days=days_ago)))

    # Call the get_order_list function
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
    
    # Debugging output for response content
    print("Response Status Code:", response.status_code)
    print("Response Content:", response.content)
    
    content = json.loads(response.content)

    # ตรวจสอบว่า "order_list" มีข้อมูลพร้อมกับข้อมูลเพิ่มเติมหรือไม่
    if content.get("error") == "" and "order_list" in content.get("response", {}):
        order_list = content["response"]["order_list"]
        
        # ตรวจสอบว่าแต่ละคำสั่งซื้อมีข้อมูลเพิ่มเติมตามที่ต้องการ
        for order in order_list:
            print("Order SN:", order["order_sn"])
            print("Buyer Username:", order.get("buyer_username"))
            print("Pay Time:", order.get("pay_time"))
            print("Item List:", order.get("item_list"))
        
        # ส่งคืน "order_list" พร้อมข้อมูลทั้งหมดที่ร้องขอ
        return {"order_detail": order_list}
    else:
        raise HTTPException(status_code=400, detail=content.get("message", "Failed to retrieve order details"))



@app.post("/get_order_detail", response_model=OrderDetailResponse)
def get_order_detail_endpoint(
    order_sn_list: str,
    access_token: str,
    request_order_status_pending: bool = False,
    response_optional_fields: str = None
):
    order_detail = get_order_detail(
        order_sn_list=order_sn_list,
        access_token=access_token,
        request_order_status_pending=request_order_status_pending,
        response_optional_fields=response_optional_fields
    )
    return OrderDetailResponse(order_detail=order_detail)

@app.post("/order", response_model=CombinedResponse)
def order_endpoint(
    access_token: str,
    order_sn_list: Optional[str] = None,
    order_status: Optional[str] = None,
    days_ago: int = 10,
    request_order_status_pending: bool = False,
    response_optional_fields: Optional[str] = "buyer_username,pay_time,item_list"
):
    combined_result: Dict[str, Any] = {}

    # Get Order List
    if order_status:
        end_time = int(datetime.timestamp(datetime.now()))
        start_time = int(datetime.timestamp(datetime.now() - timedelta(days=days_ago)))
        try:
            order_list = get_order_list(order_status=order_status, time_from=start_time, time_to=end_time, access_token=access_token)
            combined_result["order_list"] = order_list

            # Automatically set order_sn_list from the order_list if it's empty
            if not order_sn_list and order_list:
                order_sn_list = ",".join([order["order_sn"] for order in order_list])

        except HTTPException as e:
            combined_result["order_list_error"] = e.detail

    # Get Order Detail
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

    if not combined_result:
        raise HTTPException(status_code=400, detail="No valid request parameters provided.")

    return combined_result


@app.post("/get_all_orders", response_model=CombinedResponse)
def get_all_orders(
    access_token: str,
    start_date: str,
    end_date: str,
    order_status: str = "READY_TO_SHIP",
    request_order_status_pending: bool = False,
    response_optional_fields: str = "buyer_username,pay_time,item_list"
):
    combined_result: Dict[str, Any] = {}

    try:
        start_time = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    try:
        order_list = get_order_list(
            order_status=order_status,
            time_from=start_time,
            time_to=end_time,
            access_token=access_token
        )
        combined_result["order_list"] = order_list
        order_sn_list = ",".join([order["order_sn"] for order in order_list]) if order_list else None
    except HTTPException as e:
        combined_result["order_list_error"] = e.detail
        order_sn_list = None

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

    return combined_result