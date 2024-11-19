from db import SessionLocal, Token
from datetime import datetime, timedelta

db = SessionLocal()

# Create a test token entry
test_token = Token(
    access_token="test_access_token",
    refresh_token="test_refresh_token",
    expiry_time=datetime.now() + timedelta(hours=4),
)

try:
    db.add(test_token)
    db.commit()
    print("Test token added successfully!")
except Exception as e:
    db.rollback()
    print(f"Failed to add test token: {e}")
finally:
    db.close()
