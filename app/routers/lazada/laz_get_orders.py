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

@router.get("/get_orders")
def laz_get_orders():
    url = "https://api.lazada.co.th/rest"
    appkey = "131467"
    appkey = os.getenv("LAZ_KEY")
    appSecret = os.getenv("LAZ_SECRET")
    access_token = get_latest_access_token_from_db()

    client = lazop.LazopClient(url, appkey ,appSecret)
    request = lazop.LazopRequest('/orders/get','GET')
    request.add_api_param('offset', '0')
    request.add_api_param('limit', '100')
    request.add_api_param('update_after', '2024-12-17T00:00:00+08:00')
    request.add_api_param('sort_by', 'created_at')
    request.add_api_param('status', 'ready_to_ship')
    response = client.execute(request, access_token)
    return (response.body)