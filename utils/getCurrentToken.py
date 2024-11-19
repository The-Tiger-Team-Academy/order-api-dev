from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.db import SessionLocal, Token

def getCurrentToken():
    try:
        last_record = get_last_record()

        if not last_record:
            raise HTTPException(status_code=404, detail="ไม่มีข้อมูล Token ล่าสุดในฐานข้อมูล")

        return {
            "access_token": last_record.access_token,
            "refresh_token": last_record.refresh_token,
            "expiry_time": last_record.expiry_time,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาดในการดึงข้อมูล Token: {str(e)}")

def get_last_record():
    db: Session = SessionLocal()
    try:
        # Query token ล่าสุดตามลำดับการเพิ่มในตาราง
        last_record = db.query(Token).limit(1).offset(db.query(Token).count() - 1).first()
        return last_record
    finally:
        db.close()
