from fastapi import HTTPException, APIRouter #type: ignore
import hmac
import hashlib
import time
from dotenv import load_dotenv #type: ignore
import os
import requests #type: ignore
from datetime import datetime, timedelta
from ...utils.shopee.save_token import save_token_to_db

router = APIRouter(
prefix='/shopee',
tags = ['Shopee']
)

load_dotenv()

code = os.getenv("CODE")
shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
host = "https://partner.shopeemobile.com"

@router.get('/new_token')
def new_token():
    ts = int(time.time())
    body = {"code": code, "shop_id": shop_id, "partner_id": partner_id}

    path = "/api/v2/auth/token/get"
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

    url = f"{host}{path}?partner_id={partner_id}&timestamp={ts}&sign={sign}"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
        content = response.json()

        if "access_token" in content and "refresh_token" in content:
            access_token = content["access_token"]
            refresh_token = content["refresh_token"]
            expiry_time = datetime.now() + timedelta(hours=4)

            save_token_to_db(access_token, refresh_token, expiry_time)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expiry_time": expiry_time.isoformat(),
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid token response from Shopee API")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Shopee API: {str(e)}")
