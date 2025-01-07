from fastapi import HTTPException, APIRouter
import hmac
import hashlib
from dotenv import load_dotenv
import os
import requests
import json
import logging
from datetime import datetime, timedelta
from ...utils.shopee.latest_refresh_token import get_latest_refresh_token_from_db
from ...utils.shopee.save_token import save_token_to_db

# ตั้งค่า logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/shopee',
    tags=['Shopee']
)

load_dotenv()

# ตรวจสอบ environment variables
required_env_vars = {
    "SHOP_ID": os.getenv("SHOP_ID"),
    "PARTNER_ID": os.getenv("PARTNER_ID"),
    "PARTNER_KEY": os.getenv("PARTNER_KEY")
}

for var_name, value in required_env_vars.items():
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")

shop_id = int(required_env_vars["SHOP_ID"])
partner_id = int(required_env_vars["PARTNER_ID"])
partner_key = required_env_vars["PARTNER_KEY"]
host = "https://partner.shopeemobile.com"

@router.get("/refresh_token")
async def refreshToken():
    try:
        # ดึง refresh token จาก database
        refresh_token = get_latest_refresh_token_from_db()
        if not refresh_token:
            logger.error("No refresh token found in database")
            raise HTTPException(status_code=400, detail="No refresh token available")

        # สร้าง timestamp และ request body
        ts = int(datetime.timestamp(datetime.now()))
        body = {
            "shop_id": shop_id,
            "partner_id": partner_id,
            "refresh_token": refresh_token
        }

        # สร้าง signature
        path = "/api/v2/auth/access_token/get"
        base_str = str(partner_id) + path + str(ts)
        sign = hmac.new(
            partner_key.encode('utf-8'),
            base_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # สร้าง request URL และ headers
        url = f"{host}{path}?partner_id={partner_id}&timestamp={ts}&sign={sign}"
        headers = {"Content-Type": "application/json"}

        # Log request details
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request body: {body}")

        # ส่ง request ไปยัง Shopee API
        response = requests.post(url, json=body, headers=headers)
        
        # Log response
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.content}")

        # แปลง response เป็น JSON
        try:
            content = json.loads(response.content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise HTTPException(status_code=500, detail="Invalid response from Shopee API")

        if "error" in content and content["error"]:
            error_message = content.get("message", "Unknown error")
            logger.error(f"Shopee API error: {error_message}")
            raise HTTPException(status_code=400, detail=f"Shopee API error: {error_message}")

        # ตรวจสอบ response tokens
        if "access_token" in content and "refresh_token" in content:
            access_token = content["access_token"]
            new_refresh_token = content["refresh_token"]
            expiry_time = datetime.now() + timedelta(hours=4)

            # บันทึก tokens ลง database
            try:
                save_token_to_db(access_token, new_refresh_token, expiry_time)
            except Exception as e:
                logger.error(f"Failed to save tokens to database: {e}")
                raise HTTPException(status_code=500, detail="Failed to save tokens")

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "expiry_time": expiry_time.isoformat(),
            }
        else:
            logger.error("Missing tokens in response")
            raise HTTPException(
                status_code=400,
                detail="Invalid response: Missing access_token or refresh_token"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )