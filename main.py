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
# from utils.checkOrder import checkOrders
from utils.getOrderList import getOrderList
from utils.getOrderDetail import getOrderDetail
from datetime import datetime, timedelta
from utils.fetchWithAuth import fetchAuth

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

@app.get("/get_all_orders", response_model=Dict[str, Any])
def get_all_orders(
    access_token: str = Query(..., description="Access token for Shopee API"),
    start_date: str = Query(..., description="Start date in YYYY-MM-DD"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD"),
    order_status: str = Query("READY_TO_SHIP", description="Status of the orders to filter"),
    request_order_status_pending: Optional[bool] = Query(False, description="Include pending order status in details"),
    response_optional_fields: Optional[str] = Query("buyer_username,pay_time,item_list", description="Optional fields to include in the response"),
):
    try:
        return getAllOrder(
            access_token=access_token,
            order_status=order_status,
            start_date=start_date,
            end_date=end_date,
            request_order_status_pending=request_order_status_pending,
            response_optional_fields=response_optional_fields,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch all orders and details: {str(e)}")

@app.get("/api/stores")
def get_stores():
    return fetchAuth("/stores")


@app.get("/api/inventory/{store_id}")
def get_inventory(store_id: str):
    return fetchAuth(f"/inventory/{store_id}")


@app.get("/api/products/{product_id}")
def get_product_details(product_id: str):
    return fetchAuth(f"/products/{product_id}")


# @app.get("/check_inventory", summary="Check Inventory", tags=["Inventory"])
# def check_order(
#     access_token: str = Query(..., description="Access token for Shopee API"),
#     start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
#     end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
# ) -> Any:
#         inventory_status = checkOrders(access_token, start_date, end_date)
#         return {"data": inventory_status}


@app.get("/orders", response_model=OrderListResponse)
def getOrderListEndpoint(
    access_token: str = Query(..., description="Access token for Shopee API"),
    order_status: str = Query("READY_TO_SHIP", description="Status of the orders to filter"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """
    API endpoint to get the order list for a specific date and order status.
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        selected_date = datetime.strptime(date, "%Y-%m-%d")
        start_time = int(datetime.timestamp(selected_date))
        end_time = int(datetime.timestamp(selected_date + timedelta(days=1)) - 1)

        order_list = getOrderList(order_status, start_time, end_time, access_token)
        return OrderListResponse(order_list=order_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_order_detail")
def get_order_detail_endpoint(
    order_sn_list: str = Query(..., description="Comma-separated list of order_sn"),
    access_token: str = Query(..., description="Access token for Shopee API"),
    request_order_status_pending: Optional[bool] = Query(False, description="Include pending order status"),
    response_optional_fields: Optional[str] = Query("buyer_username,pay_time,item_list", description="Optional fields to include in the response")
):
    """
    API endpoint to get detailed information about specific orders.
    """
    try:
        order_details = getOrderDetail(
            order_sn_list=order_sn_list,
            access_token=access_token,
            request_order_status_pending=request_order_status_pending,
            response_optional_fields=response_optional_fields
        )
        return order_details
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve order details: {str(e)}")


