import json
from fastapi import APIRouter # type: ignore

router = APIRouter(
prefix='/laz',
tags = ['Lazada']
)

@router.get('/auth')
def auth():
    call_back = "https://google.com/"
    app_key = 131467
    link = f"https://auth.lazada.com/oauth/authorize?response_type=code&force_auth=true&redirect_uri={call_back}&client_id={app_key}"
    return {"Auth link": link}

# https://auth.lazada.com/oauth/authorize?response_type=code&force_auth=true&redirect_uri=https://google.com/&client_id=131467