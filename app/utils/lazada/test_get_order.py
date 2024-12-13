import lazop #type: ignore

url = "https://api.lazada.co.th/rest"
appkey = "131467"
appSecret = "RXEpAbUXTGdVMWzRKqk4Oyt0mzxlVxSg"
access_token = "50000801202pIQ17f0f17aczhvflxDtwjfchU8nWzclgMHVir1mHa9RPcFK8MQ64"

client = lazop.LazopClient(url, appkey ,appSecret)
request = lazop.LazopRequest('/orders/get','GET')
request.add_api_param('offset', '0')
request.add_api_param('limit', '10')
request.add_api_param('update_after', '2024-11-20T09:00:00+08:00')
request.add_api_param('sort_by', 'updated_at')
request.add_api_param('status', 'ready_to_ship')
response = client.execute(request, access_token)
print(response.type)
print(response.body)