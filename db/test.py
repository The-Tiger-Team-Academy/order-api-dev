from sqlalchemy.orm import Session
from sqlalchemy import text
from db import SessionLocal

def test_connection():
    try:
        # Open a new session
        db: Session = SessionLocal()
        
        # Execute a simple SQL query to test the connection
        result = db.execute(text("SELECT 1"))
        
        # Fetch the result
        output = result.fetchone()
        print("Database Connection Successful. Test Query Output:", output)
    except Exception as e:
        print("Error Connecting to the Database:", str(e))
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()
