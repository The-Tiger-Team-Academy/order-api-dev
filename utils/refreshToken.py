from fastapi import HTTPException  # type: ignore
import hmac
import hashlib
from dotenv import load_dotenv  # type: ignore
import os
import requests  # type: ignore
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.db import SessionLocal, Token  # Import database session and model

load_dotenv()

shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
host = "https://partner.shopeemobile.com"

def get_latest_refresh_token_from_db():
    """
    Retrieve the most recent refresh token from the database.
    """
    db: Session = SessionLocal()
    try:
        latest_token = db.query(Token).order_by(Token.expiry_time.desc()).first()
        if not latest_token:
            raise HTTPException(status_code=404, detail="No refresh token found in the database.")
        return latest_token.refresh_token
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving refresh token: {str(e)}")
    finally:
        db.close()


def save_token_to_db(access_token: str, refresh_token: str, expiry_time: datetime):
    """
    Save token information to the database.
    """
    db: Session = SessionLocal()
    try:
        # Check if the token already exists
        existing_token = db.query(Token).filter(Token.access_token == access_token).first()

        if existing_token:
            # Update the existing record
            existing_token.refresh_token = refresh_token
            existing_token.expiry_time = expiry_time
        else:
            # Add a new record
            new_token = Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expiry_time=expiry_time,
            )
            db.add(new_token)

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()


def refreshToken():
    """
    Refresh the access token using the latest refresh token and save the new tokens to the database.
    """
    try:
        # Get the latest refresh token from the database
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

            # Save the new tokens to the database
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
