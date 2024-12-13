import json
from datetime import datetime, timedelta
from fastapi import APIRouter # type: ignore

from ...utils.lazada.base import LazopClient, LazopRequest
from ...utils.lazada.save_token import save_token_to_db

router = APIRouter(
    prefix='/laz',
    tags=['Lazada']
)

P_CODE = 'code'
P_APPKEY = "131467"
P_APP_SECRET = "RXEpAbUXTGdVMWzRKqk4Oyt0mzxlVxSg"
P_API_URL = "https://api.lazada.com/rest"  

@router.get("/new_token")
def get_access_token():
    client = LazopClient(
        server_url=P_API_URL,
        app_key=P_APPKEY,
        app_secret=P_APP_SECRET
    )
    request = LazopRequest('/auth/token/create')

    authorization_code = '0_131467_8lvzaWNldvgYZEKHa7MHXdJV37664' 
    request.add_api_param(P_CODE, authorization_code)

    try:
        response = client.execute(request)
        print(f"Response: {json.dumps(response, indent=2)}")
        
        if 'access_token' in response:
            print(f"Access Token: {response['access_token']}")
            print(f"Refresh Token: {response.get('refresh_token')}")
            
            # Calculate expiry timestamp by adding expires_in seconds to current time
            expiry_time = datetime.now() + timedelta(seconds=response['expires_in'])
            
            save_token_to_db(
                response['access_token'],
                response['refresh_token'],
                expiry_time  # Now passing a datetime object instead of seconds
            )
            return {"Response": response}
        else:
            print("Failed to retrieve access token.")
            return {"error": "Failed to retrieve access token"}
    except Exception as e:
        error_message = f"Error occurred in New Token: {str(e)}"
        print(error_message)
        return {"error": error_message}