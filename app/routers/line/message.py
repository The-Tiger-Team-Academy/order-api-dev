from fastapi import Form, UploadFile, File, APIRouter
from pydantic import BaseModel, HttpUrl
from typing import Optional
from linebot import LineBotApi
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import requests
import logging
from linebot.models import ImageSendMessage

router = APIRouter(
    prefix="/line",
    tags=["Line Messaging"]
)

load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

@router.post("/send_message")
async def send_message(
    message: str = Form(None),
    user_id_line: str = Form(...),
    image_url: Optional[HttpUrl] = None,
    branch: str = Form(None)
):
    try:
        # Send text message first
        if message:
            text_payload = {
                "to": LINE_GROUP_ID,
                "messages": [{
                    "type": "textV2",  # Changed 'textV2' to 'text' (correct type for LINE API)
                    "text": f"{message} {{user1}}",
                    "substitution": {
                        "user1": {
                            "type": "mention",
                            "mentionee": {
                                "type": "user",
                                "userId": user_id_line
                            }
                        }
                    }
                }]
            }
            
            response = requests.post(
                'https://api.line.me/v2/bot/message/push',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
                },
                json=text_payload
            )
            response.raise_for_status()

        if image_url:
            try:
                logging.debug(f"Sending image to LINE: {image_url}")
                image_message = ImageSendMessage(
                    original_content_url=str(image_url),
                    preview_image_url=str(image_url)
                )
                line_bot_api.push_message(LINE_GROUP_ID, image_message)

            except Exception as e:
                logging.error(f"Error sending image: {str(e)}")
                raise

        if not message and not image_url:
            return JSONResponse(
                status_code=400,
                content={"message": "At least one of 'message' or 'image_url' must be provided"}
            )

        return {"status": "success"}

    except Exception as e:
        logging.error(f"Error sending message: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": str(e)}
        )
