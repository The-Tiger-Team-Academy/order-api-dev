from fastapi import APIRouter # type: ignore
import lazop #type: ignore
from dotenv import load_dotenv #type: ignore
import os
from ...utils.lazada.latest_access_token import get_latest_access_token_from_db

router = APIRouter(
prefix='/lazada',
tags = ['Lazada']
)

load_dotenv()

@router.get("/get_order_detail")
def laz_get_orders(order_id: str):
    url = "https://api.lazada.co.th/rest"
    appkey = "131467"
    appkey = os.getenv("LAZ_KEY")
    appSecret = os.getenv("LAZ_SECRET")
    access_token = get_latest_access_token_from_db()

    client = lazop.LazopClient(url, appkey ,appSecret)
    request = lazop.LazopRequest('/order/items/get','GET')
    request.add_api_param('order_id', order_id)
    response = client.execute(request, access_token)
    return (response.body)