from fastapi import HTTPException  # type: ignore
from sqlalchemy.orm import Session
from db.db import SessionLocal, Token  # Import your database session and Token model


def getCurrentToken():
    """
    Fetch the current access_token and refresh_token from the database.
    """
    db: Session = SessionLocal()
    try:
        # Query the Token table for the latest token
        current_token = db.query(Token).order_by(Token.expiry_time.desc()).first()

        if not current_token:
            raise HTTPException(status_code=404, detail="Tokens not available")

        return {
            "access_token": current_token.access_token,
            "refresh_token": current_token.refresh_token,
            "expiry_time": current_token.expiry_time,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving token from database: {str(e)}")
    finally:
        db.close()
