from fastapi import FastAPI # type: ignore
from typing import Optional, Dict, Any, List
from pydantic import BaseModel # type: ignore
from dotenv import load_dotenv # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore

from app.routers.shopee import check_token_shopee, new_token_shopee, auth_shopee, get_all_order, refresh_token_shopee
from app.routers.storehub import inventory_check
from app.routers.orders import compare_orders, merge_orders
from app.routers.lazada import auth_laz, check_token_laz, new_token_laz, refresh_token_laz, laz_get_orders, laz_get_order_detail, all_orders
from app.routers.line import message, webhook
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

class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str

#---Shopee Routers-----
app.include_router(refresh_token_shopee.router)
app.include_router(check_token_shopee.router)
app.include_router(auth_shopee.router)
app.include_router(new_token_shopee.router)
app.include_router(get_all_order.router)
#----------------------

#---Lazada Routers-----
app.include_router(new_token_laz.router)
app.include_router(auth_laz.router)
app.include_router(refresh_token_laz.router)
app.include_router(check_token_laz.router)
app.include_router(laz_get_orders.router)
app.include_router(laz_get_order_detail.router)
app.include_router(all_orders.router)
#----------------------

#---StoreHub Routers---
app.include_router(inventory_check.router)
#----------------------

#---Orders Routers-----
# app.include_router(compare_orders.router)
app.include_router(merge_orders.router)
#----------------------

#---Line Routers---
app.include_router(message.router)
app.include_router(webhook.router)
#----------------------
