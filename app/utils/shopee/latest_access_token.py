from fastapi import HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from ...db.db_token import SessionLocal
from ...models.shopee import TokenShopee 
from ...routers.shopee.refresh_token_shopee import refreshToken

def get_latest_access_token_from_db():
    db: Session = SessionLocal()
    try:
        total_tokens = db.query(TokenShopee).count()
        
        if total_tokens == 0:
            # Try refreshing token if no tokens found
            new_token =  refreshToken()
            return new_token
        
        last_token = db.query(TokenShopee)[total_tokens - 1]
        
        if not last_token or not last_token.access_token:
            # Try refreshing token if token is invalid
            new_token =  refreshToken()
            return new_token

        return last_token.access_token
    except IndexError:
        # Try refreshing token on index error
        new_token =  refreshToken()
        return new_token
    except Exception as e:
        print(f"Error during last index TokenShopee retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving last index refresh TokenShopee: {str(e)}")
    finally:
        db.close()
