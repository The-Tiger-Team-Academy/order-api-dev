from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError #type: ignore
from ...db.db_token import SessionLocal
from ...models.laz import TokenLaz

def save_token_to_db(access_token: str, refresh_token: str, expiry_time: datetime):
    db = SessionLocal()
    try:
        existing_token = db.query(TokenLaz).filter(TokenLaz.access_token == access_token).first()

        if existing_token:
            existing_token.refresh_token = refresh_token
            existing_token.expiry_time = expiry_time
            print(f"TokenLaz updated: {access_token}")
        else:   
            new_token = TokenLaz(
                access_token=access_token,
                refresh_token=refresh_token,
                expiry_time=expiry_time,
            )
            db.add(new_token)
            print(f"TokenLaz saved: {access_token}")

        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    finally:
        db.close()