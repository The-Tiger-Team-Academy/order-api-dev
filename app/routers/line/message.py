from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
from linebot import LineBotApi
from linebot.models import TextSendMessage, ImageSendMessage
from linebot.exceptions import LineBotApiError

router = APIRouter(
    prefix="/line",
    tags=["Line Messaging"]
)

# Configuration
LINE_CHANNEL_ACCESS_TOKEN = "GNwYjz57Kb27Rx9buk5G42j2iysAA2zmSaYLSL6F+1eiU876i7IgJUVL4bbkYWusM+OToOLeNtUL+8Z3UiPxnB1fGL2TMkE7jqWUFboaupKY9ox3zzNrdb8/9Ve1sA7AUho/7gYoF05KNidmtoMmKwdB04t89/1O/w1cDnyilFU="
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

class LineMessage(BaseModel):
    user_id: str
    message: Optional[str] = None
    image_url: Optional[HttpUrl] = None

@router.post("/send_message")
async def send_line_message(message_data: LineMessage):
    """
    Send message and/or image to Line user
    
    Parameters:
    - user_id: Line user ID
    - message: Text message (optional)
    - image_url: URL of image to send (optional)
    """
    try:
        messages = []
        
        # Add text message if provided
        if message_data.message:
            messages.append(
                TextSendMessage(text=message_data.message)
            )
        
        # Add image if URL is provided
        if message_data.image_url:
            messages.append(
                ImageSendMessage(
                    original_content_url=str(message_data.image_url),
                    preview_image_url=str(message_data.image_url)
                )
            )
            
        # Check if at least one message type is provided
        if not messages:
            raise HTTPException(
                status_code=400,
                detail="Either message or image_url must be provided"
            )
            
        # Send message(s)
        line_bot_api.push_message(
            message_data.user_id,
            messages
        )
        
        return {
            "status": "success",
            "message": "Messages sent successfully"
        }
        
    except LineBotApiError as line_error:
        raise HTTPException(
            status_code=500,
            detail=f"Line API error: {str(line_error)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )

@router.post("/broadcast")
async def broadcast_message(message_data: LineMessage):
    """
    Broadcast message and/or image to all Line users
    
    Parameters:
    - message: Text message (optional)
    - image_url: URL of image to send (optional)
    """
    try:
        messages = []
        
        if message_data.message:
            messages.append(
                TextSendMessage(text=message_data.message)
            )
            
        if message_data.image_url:
            messages.append(
                ImageSendMessage(
                    original_content_url=str(message_data.image_url),
                    preview_image_url=str(message_data.image_url)
                )
            )
            
        if not messages:
            raise HTTPException(
                status_code=400,
                detail="Either message or image_url must be provided"
            )
            
        line_bot_api.broadcast(messages)
        
        return {
            "status": "success",
            "message": "Messages broadcasted successfully"
        }
        
    except LineBotApiError as line_error:
        raise HTTPException(
            status_code=500,
            detail=f"Line API error: {str(line_error)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )
    
