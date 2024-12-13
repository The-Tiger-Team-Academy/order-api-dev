from fastapi import FastAPI # type: ignore
from typing import Optional, Dict, Any, List
from pydantic import BaseModel # type: ignore
from dotenv import load_dotenv # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore

from app.routers.shopee import refresh_token, check_token, auth, new_token, get_all_order
from app.routers.storehub import inventory_check
from app.routers.orders import compare_orders
from app.routers.lazada import new_token,auth,refresh_token, check_token

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
app.include_router(refresh_token.router)
app.include_router(check_token.router)
app.include_router(auth.router)
app.include_router(new_token.router)
app.include_router(get_all_order.router)
#----------------------

#---Lazada Routers-----
app.include_router(new_token.router)
app.include_router(auth.router)
app.include_router(refresh_token.router)
app.include_router(check_token.router)
#----------------------

#---StoreHub Routers---
app.include_router(inventory_check.router)
#----------------------

#---Orders Routers-----
app.include_router(compare_orders.router)
#----------------------
