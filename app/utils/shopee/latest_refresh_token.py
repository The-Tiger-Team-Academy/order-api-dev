from fastapi import HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from ...db.db_token import SessionLocal
from ...models.shopee import TokenShopee 

def get_latest_refresh_token_from_db():
    db: Session = SessionLocal()
    try:
        total_tokens = db.query(TokenShopee).count()
        
        if total_tokens == 0:
            raise HTTPException(status_code=404, detail="No refresh tokens found in the database.")
        
        last_token = db.query(TokenShopee)[total_tokens - 1]
        
        if not last_token or not last_token.refresh_token:
            raise HTTPException(status_code=404, detail="No valid refresh TokenShopee found.")

        return last_token.refresh_token
    except IndexError:
        raise HTTPException(status_code=404, detail="Unable to retrieve the last TokenShopee.")
    except Exception as e:
        print(f"Error during last index TokenShopee retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving last index refresh TokenShopee: {str(e)}")
    finally:
        db.close()