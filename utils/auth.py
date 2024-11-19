import hmac
import hashlib
import time
import urllib.parse
from dotenv import load_dotenv # type: ignore
import os

load_dotenv()

code = os.getenv("CODE")
shop_id = int(os.getenv("SHOP_ID"))
partner_id = int(os.getenv("PARTNER_ID"))
partner_key = os.getenv("PARTNER_KEY")
redirect_url = os.getenv("REDIRECT_URL")
host = "https://partner.shopeemobile.com"


def auth():
    ts = int(time.time())
    path = "/api/v2/shop/auth_partner"
    base_str = str(partner_id) + path + str(ts)
    sign = hmac.new(partner_key.encode('utf-8'), base_str.encode('utf-8'), hashlib.sha256).hexdigest()
    encoded_redirect_url = urllib.parse.quote(redirect_url)

    url = f"{host}{path}?partner_id={partner_id}&redirect={encoded_redirect_url}&timestamp={ts}&sign={sign}"
    return {"auth_url": url}