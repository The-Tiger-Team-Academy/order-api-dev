from fastapi import HTTPException, APIRouter # type: ignore
from sqlalchemy.orm import Session # type: ignore
from ...db.db_token import SessionLocal
from ...models.lazada import TokenLaz


router = APIRouter(
prefix='/lazada',
tags = ['Lazada']
)

@router.get('/check_token')
def check_token():
    try:
        last_record = get_last_record()

        if not last_record:
            raise HTTPException(status_code=404, detail="ไม่มีข้อมูล TokenLaz ล่าสุดในฐานข้อมูล")

        return {
            "access_token": last_record.access_token,
            "refresh_token": last_record.refresh_token,
            "expiry_time": last_record.expiry_time,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงข้อมูล TokenLaz: {str(e)}")

def get_last_record():
    db: Session = SessionLocal()
    try:
        last_record = db.query(TokenLaz).limit(1).offset(db.query(TokenLaz).count() - 1).first()
        return last_record
    finally:
        db.close()
