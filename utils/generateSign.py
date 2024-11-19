import os
from typing import Optional
import hmac
import hashlib

shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")

def generateSign(path: str, ts: int, access_token: Optional[str] = None):
    base_str = str(partner_id) + path + str(ts)
    if access_token:
        base_str += access_token + str(shop_id)
    return hmac.new(partner_key.encode("utf-8"), base_str.encode("utf-8"), hashlib.sha256).hexdigest()

