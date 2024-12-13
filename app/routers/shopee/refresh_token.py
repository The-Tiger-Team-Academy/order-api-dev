from fastapi import HTTPException, APIRouter # type: ignore
import hmac
import hashlib
from dotenv import load_dotenv  # type: ignore
import os
import requests  # type: ignore
import json
from datetime import datetime, timedelta
from ...utils.shopee.latest_refresh_token import get_latest_refresh_token_from_db
from ...utils.shopee.save_token import save_token_to_db

router = APIRouter(
prefix='/shopee',
tags = ['Shopee']
)

load_dotenv()

shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
host = "https://partner.shopeemobile.com"

@router.get("/refresh_token")
def refreshToken():
    try:
        refresh_token = get_latest_refresh_token_from_db()

        ts = int(datetime.timestamp(datetime.now()))
        body = {"shop_id": shop_id, "partner_id": partner_id, "refresh_token": refresh_token}

        path = "/api/v2/auth/access_token/get"
        base_str = str(partner_id) + path + str(ts)
        sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

        url = f"{host}{path}?partner_id={partner_id}&timestamp={ts}&sign={sign}"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=body, headers=headers)
        content = json.loads(response.content)

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
            raise HTTPException(status_code=400, detail="Token refresh failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing token: {str(e)}")
