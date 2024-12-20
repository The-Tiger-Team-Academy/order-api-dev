from fastapi import APIRouter, Request, HTTPException
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, LocationMessage,
    TextSendMessage, ImageSendMessage, FollowEvent, UnfollowEvent,
    PostbackEvent
)
from typing import List, Optional
import logging

router = APIRouter(
    prefix="/line",
    tags=["Line Messaging"]
)

# Configuration
LINE_CHANNEL_ACCESS_TOKEN = "GNwYjz57Kb27Rx9buk5G42j2iysAA2zmSaYLSL6F+1eiU876i7IgJUVL4bbkYWusM+OToOLeNtUL+8Z3UiPxnB1fGL2TMkE7jqWUFboaupKY9ox3zzNrdb8/9Ve1sA7AUho/7gYoF05KNidmtoMmKwdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "3c828de0474e4c8a0491090687b1b44d"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def line_webhook(request: Request):
    """
    Handle LINE webhook events and manage user interactions
    """
    # Get X-Line-Signature header value
    signature = request.headers.get('X-Line-Signature', '')
    
    # Get request body as text
    body = await request.body()
    body_decode = body.decode('utf-8')
    
    try:
        events = parser.parse(body_decode, signature)
        
        for event in events:
            user_id = event.source.user_id
            
            # Get user profile
            try:
                profile = line_bot_api.get_profile(user_id)
                logger.info(f"User interaction: {profile.display_name} ({user_id})")
            except LineBotApiError as e:
                logger.error(f"Error getting user profile: {e}")
            
            # Handle different event types
            if isinstance(event, FollowEvent):
                await handle_follow(event)
                
            elif isinstance(event, UnfollowEvent):
                await handle_unfollow(event)
                
            elif isinstance(event, PostbackEvent):
                await handle_postback(event)
                
            elif isinstance(event, MessageEvent):
                if isinstance(event.message, TextMessage):
                    await handle_text_message(event)
                elif isinstance(event.message, ImageMessage):
                    await handle_image_message(event)
                elif isinstance(event.message, LocationMessage):
                    await handle_location_message(event)
        
        # Get updated follower list
        try:
            friend_list = line_bot_api.get_followers_ids()
            logger.info(f"Total followers: {len(friend_list.user_ids)}")
            
            # Log all follower IDs
            for follower_id in friend_list.user_ids:
                logger.debug(f"Follower ID: {follower_id}")
                
        except LineBotApiError as e:
            logger.error(f"Error getting follower list: {e}")
        
        return {"status": "success", "message": "Webhook processed successfully"}
        
    except InvalidSignatureError:
        logger.error("Invalid signature error")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except LineBotApiError as e:
        logger.error(f"LINE API error: {e}")
        raise HTTPException(status_code=500, detail=f"LINE API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def handle_follow(event: FollowEvent):
    """Handle new followers"""
    try:
        profile = line_bot_api.get_profile(event.source.user_id)
        welcome_message = f"สวัสดีคุณ {profile.display_name}! ขอบคุณที่เพิ่มเราเป็นเพื่อน"
        
        messages = [
            TextSendMessage(text=welcome_message),
            TextSendMessage(text="พิมพ์ 'เมนู' เพื่อดูคำสั่งทั้งหมด")
        ]
        
        line_bot_api.reply_message(event.reply_token, messages)
        logger.info(f"New follower: {profile.display_name} ({event.source.user_id})")
        
        # Here you might want to save user info to your database
        
    except Exception as e:
        logger.error(f"Error handling follow event: {e}")

async def handle_unfollow(event: UnfollowEvent):
    """Handle unfollows"""
    try:
        logger.info(f"User unfollowed: {event.source.user_id}")
        # Here you might want to update user status in your database
        
    except Exception as e:
        logger.error(f"Error handling unfollow event: {e}")

async def handle_text_message(event: MessageEvent):
    """Handle text messages"""
    try:
        text = event.message.text.lower()
        user_id = event.source.user_id
        
        # Basic command handling
        if text == "เมนู":
            menu_text = """พิมพ์คำสั่งต่อไปนี้:
1. ข้อมูล - ดูข้อมูลผู้ใช้
2. ติดต่อ - ข้อมูลการติดต่อ
3. ช่วยเหลือ - วิธีใช้งาน"""
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=menu_text)
            )
            
        elif text == "ข้อมูล":
            profile = line_bot_api.get_profile(user_id)
            info_text = f"""ข้อมูลของคุณ:
ชื่อ: {profile.display_name}
สถานะ: {profile.status_message or 'ไม่ระบุ'}
รูปประจำตัว: มี"""
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=info_text)
            )
            
        else:
            # Echo the message (you might want to change this)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"คุณส่ง: {event.message.text}")
            )
            
    except Exception as e:
        logger.error(f"Error handling text message: {e}")

async def handle_image_message(event: MessageEvent):
    """Handle image messages"""
    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ได้รับรูปภาพของคุณแล้ว")
        )
    except Exception as e:
        logger.error(f"Error handling image message: {e}")

async def handle_location_message(event: MessageEvent):
    """Handle location messages"""
    try:
        location = event.message
        response = f"ได้รับตำแหน่งของคุณแล้ว: {location.address}"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )
    except Exception as e:
        logger.error(f"Error handling location message: {e}")

async def handle_postback(event: PostbackEvent):
    """Handle postback events"""
    try:
        data = event.postback.data
        # Handle different postback data
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"ได้รับคำสั่ง: {data}")
        )
    except Exception as e:
        logger.error(f"Error handling postback: {e}")