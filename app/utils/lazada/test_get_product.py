import lazop #type: ignore

url = "https://api.lazada.co.th/rest"
appkey = "131467"
appSecret = "RXEpAbUXTGdVMWzRKqk4Oyt0mzxlVxSg"
access_token = "50000801202pIQ17f0f17aczhvflxDtwjfchU8nWzclgMHVir1mHa9RPcFK8MQ64"

client = lazop.LazopClient(url, appkey ,appSecret)
request = lazop.LazopRequest('/products/get','GET')
# request.add_api_param('filter', 'live')
request.add_api_param('update_before', '2024-12-29T00:00:00+0800')
request.add_api_param('create_before', '2024-12-30T00:00:00+0800')
request.add_api_param('offset', '0')
request.add_api_param('limit', '10')
request.add_api_param('options', '1')
response = client.execute(request, access_token)
print(response.message)
print(response.type)
print(response.body)
