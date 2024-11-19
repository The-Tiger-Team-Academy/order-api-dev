from fastapi import FastAPI, HTTPException, Query # type: ignore
from typing import Optional, Dict, Any, Union, List
from pydantic import BaseModel # type: ignore
from dotenv import load_dotenv # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from utils.auth import auth
from utils.getToken import getToken
from utils.getCurrentToken import getCurrentToken
from utils.refreshToken import refreshToken
from utils.getAllOrder import getAllOrder
from utils.checkOrder import checkOrders
from datetime import datetime, timedelta

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class CombinedResponse(BaseModel):
    order_detail: Optional[List[Dict[str, Any]]] = None
    order_list_error: Optional[str] = None
    order_detail_error: Optional[str] = None

class OrderListResponse(BaseModel):
    order_list: list


@app.get("/auth")
def generate_auth_url():
    return auth()

@app.get("/get_token", response_model=TokenResponse)
def get_token():
    return getToken()

@app.get("/check_token")
def get_current_tokens():
    return getCurrentToken()

@app.get("/refresh_token")
def refresh_token():
    return refreshToken()

@app.post("/get_all_orders", response_model=CombinedResponse)
def get_all_order(
    access_token: str,
    start_date: str = datetime.now().strftime("%Y-%m-%d"),
    end_date: str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
    order_status: str = "READY_TO_SHIP",
    request_order_status_pending: bool = False,
    response_optional_fields: str = "buyer_username,pay_time,item_list",
):
    try:
        return getAllOrder(
            start_date=start_date,
            end_date=end_date,
            access_token=access_token,
            order_status=order_status,
            request_order_status_pending=request_order_status_pending,
            response_optional_fields=response_optional_fields,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch all orders: {str(e)}")

@app.get("/check_inventory")
def check_order(access_token: str = Query(..., description="Access token for Shopee API")):
    try:
        inventory_status = checkOrders(access_token)
        return inventory_status
    except HTTPException as http_exc:
        raise http_exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")