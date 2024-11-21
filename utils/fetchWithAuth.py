from fastapi import FastAPI, HTTPException
import requests
from typing import List
from dotenv import load_dotenv  # type: ignore
import os
load_dotenv()

BASE_URL = "https://api.storehubhq.com"
AUTH_USERNAME = (os.getenv("STOREHUB_API_USERNAME"))
AUTH_PASSWORD = (os.getenv("STOREHUB_API_PASSWORD"))
AUTH_CREDENTIALS = (AUTH_USERNAME, AUTH_PASSWORD)

# Function to fetch data from StoreHub API
def fetchAuth(endpoint: str):
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, auth=AUTH_CREDENTIALS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=response.status_code, detail=str(e))
