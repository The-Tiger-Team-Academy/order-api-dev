from fastapi import Request, HTTPException, APIRouter
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, 
    TextMessage,
    JoinEvent,
    MemberJoinedEvent,
    MemberLeftEvent
)
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import hashlib
import hmac
import base64

router = APIRouter(
    prefix="/line",
    tags=["Line Messaging"]
)

load_dotenv()

logging.basicConfig(level=logging.INFO)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

group_users = {}

def get_user_display_name(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except Exception as e:
        print(f"Error getting profile for {user_id}: {e}")
        return "Unknown User"

@router.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get('X-Line-Signature', '')
    body = await request.body()
    body_text = body.decode('utf-8')
    
    # Log the raw webhook data
    logging.info(f"Received webhook body: {body_text}")
    
    try:
        # Handle the webhook directly - no need to parse separately
        handler.handle(body_text, signature)
        
        # For logging purposes, we can decode the JSON body
        import json
        body_json = json.loads(body_text)
        
        # Log events information
        if 'events' in body_json and body_json['events']:
            for event in body_json['events']:
                event_type = event.get('type', 'unknown')
                source = event.get('source', {})
                source_type = source.get('type', 'unknown')
                group_id = source.get('groupId', 'N/A') if source_type == 'group' else 'N/A'
                
                logging.info(f"Event Type: {event_type}")
                logging.info(f"Source Type: {source_type}")
                logging.info(f"Group ID: {group_id}")
                
    except InvalidSignatureError:
        logging.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return {'message': 'OK'}

@handler.add(JoinEvent)
def handle_join(event):
    if event.source.type == 'group':
        group_id = event.source.group_id
        line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text="Bot joined group! I'll start tracking member activity.")
        )

@handler.add(MemberJoinedEvent)
def handle_member_joined(event):
    if event.source.type == 'group':
        now = datetime.now().isoformat()
        for user in event.joined.members:
            display_name = get_user_display_name(user.user_id)
            group_users[user.user_id] = {
                'last_active': now,
                'display_name': display_name
            }
            
        line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=f"Welcome new members! Total known users: {len(group_users)}")
        )

@handler.add(MemberLeftEvent)
def handle_member_left(event):
    if event.source.type == 'group':
        for user in event.left.members:
            if user.user_id in group_users:
                del group_users[user.user_id]

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type == 'group':
        user_id = event.source.user_id
        display_name = get_user_display_name(user_id)
        group_users[user_id] = {
            'last_active': datetime.now().isoformat(),
            'display_name': display_name
        }
        
        if event.message.text == '/members':
            response = f"Known active members: {len(group_users)}\n"
            response += "Note: This only shows members who have interacted since the bot was added.\n"
            response += f"Members:\n"
            
            for user_id, user_info in group_users.items():
                response += f"- {user_info['display_name']} (ID: {user_id})\n"
                response += f"  Last active: {user_info['last_active']}\n"
            
            line_bot_api.reply_message(
                event.reply_token,
                TextMessage(text=response[:5000])
            )
