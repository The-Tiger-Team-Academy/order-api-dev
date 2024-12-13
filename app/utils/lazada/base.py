import time
import hmac
import hashlib
import requests #type: ignore
import logging
from os.path import expanduser
import os

dir = expanduser("~")
isExists = os.path.exists(dir + "/logs")
if not isExists:
    os.makedirs(dir + "/logs")

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.ERROR)
handler = logging.FileHandler(dir + "/logs/lazopsdk.log." + time.strftime("%Y-%m-%d", time.localtime()))
handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

P_SDK_VERSION = "lazop-sdk-python-20181207"

def sign(secret, api, parameters):
    sorted_params = sorted(parameters.items())
    parameters_str = api + ''.join(f'{key}{value}' for key, value in sorted_params)
    h = hmac.new(secret.encode('utf-8'), parameters_str.encode('utf-8'), hashlib.sha256)
    return h.hexdigest().upper()

class LazopRequest(object):
    def __init__(self, api_name, http_method='POST'):
        self._api_params = {}
        self._file_params = {}
        self._api_name = api_name
        self._http_method = http_method

    def add_api_param(self, key, value):
        self._api_params[key] = value

    def add_file_param(self, key, value):
        self._file_params[key] = value

class LazopClient(object):
    def __init__(self, server_url, app_key, app_secret, timeout=30):
        self._server_url = server_url
        self._app_key = app_key
        self._app_secret = app_secret
        self._timeout = timeout

    def execute(self, request, access_token=None):
        sys_parameters = {
            'app_key': self._app_key,
            'sign_method': 'sha256',
            'timestamp': str(int(time.time() * 1000)),
            'partner_id': P_SDK_VERSION
        }
        if access_token:
            sys_parameters['access_token'] = access_token
        all_params = sys_parameters.copy()
        all_params.update(request._api_params)
        all_params['sign'] = sign(self._app_secret, request._api_name, all_params)
        api_url = f"{self._server_url}{request._api_name}"
        full_url = api_url + '?' + '&'.join([f'{key}={value}' for key, value in all_params.items()])

        try:
            if request._http_method == 'POST' or len(request._file_params) != 0:
                response = requests.post(api_url, params=all_params, files=request._file_params, timeout=self._timeout)
            else:
                response = requests.get(full_url, timeout=self._timeout)
        except Exception as err:
            logger.error(f"HTTP Error: {str(err)}")
            raise err

        response_data = response.json()

        if response_data.get('code') != '0':
            logger.error(f"Error: {response_data.get('message')}")
            raise Exception(f"API Error: {response_data.get('message')}")

        return response_data