import json
from datetime import datetime, timedelta
from fastapi import APIRouter # type: ignore

from ...utils.lazada.base import LazopRequest, LazopClient
from ...utils.lazada.latest_refresh_token import get_latest_refresh_token_from_db
from ...utils.lazada.save_token import save_token_to_db

router = APIRouter(
    prefix='/laz',
    tags=['Lazada']
)

P_APPKEY = "131467"
P_APP_SECRET = "RXEpAbUXTGdVMWzRKqk4Oyt0mzxlVxSg"
P_API_URL = "https://api.lazada.com/rest"  

@router.get("/refresh_token")
def refresh_access_token():
    client = LazopClient(
        server_url=P_API_URL,
        app_key=P_APPKEY,
        app_secret=P_APP_SECRET
    )

    request = LazopRequest('/auth/token/refresh')
    refresh_token = get_latest_refresh_token_from_db()
    request.add_api_param("refresh_token", refresh_token)
    try:
        response = client.execute(request)
        print(f"Response: {json.dumps(response, indent=2)}")
        if 'access_token' in response:
            print(f"Access Token: {response['access_token']}")
            print(f"Refresh Token: {response.get('refresh_token')}")

            expiry_time = datetime.now() + timedelta(seconds=response['expires_in'])
            
            save_token_to_db(
                response['access_token'],
                response['refresh_token'],
                expiry_time 
            )
            return {"Response": response}
        else:
            print("Failed to retrieve access token.")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

