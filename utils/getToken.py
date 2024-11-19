from fastapi import HTTPException
from pydantic import BaseModel
import hmac
import hashlib
import time
from dotenv import load_dotenv
import os
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from db.db import SessionLocal, Token

# Load environment variables
load_dotenv()

# Environment variables
code = os.getenv("CODE")
shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
host = "https://partner.shopeemobile.com"
initial_refresh_token = "6d76444b574d7477564e707946784d6e"

# Token dictionary
tokens = {
    "access_token": None,
    "refresh_token": initial_refresh_token,
    "expiry_time": None
}

# Pydantic model for token response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expiry_time: str


def save_token_to_db(access_token: str, refresh_token: str, expiry_time: datetime):
    """
    Save token information to the database. Updates if the token exists.
    """
    db = SessionLocal()
    try:
        # Check if the token already exists in the database
        existing_token = db.query(Token).filter(Token.access_token == access_token).first()

        if existing_token:
            # Update the existing token record
            existing_token.refresh_token = refresh_token
            existing_token.expiry_time = expiry_time
            print(f"Token updated: {access_token}")
        else:
            # Add a new token record
            new_token = Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expiry_time=expiry_time,
            )
            db.add(new_token)
            print(f"Token saved: {access_token}")

        # Commit changes to the database
        db.commit()
    except SQLAlchemyError as e:
        # Rollback in case of any database errors
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    finally:
        db.close()


def getToken():
    """
    Fetch a token from Shopee API and save it to the database.
    """
    ts = int(time.time())
    body = {"code": code, "shop_id": shop_id, "partner_id": partner_id}

    path = "/api/v2/auth/token/get"
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()

    url = f"{host}{path}?partner_id={partner_id}&timestamp={ts}&sign={sign}"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()  # Raise an error for non-2xx status codes
        content = response.json()

        if "access_token" in content and "refresh_token" in content:
            access_token = content["access_token"]
            refresh_token = content["refresh_token"]
            expiry_time = datetime.now() + timedelta(hours=4)

            # Save the token to the database
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
