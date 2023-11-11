
import time, json
import requests
import hmac
from hashlib import sha256


class SpotAPI:
    def __init__(self, SECRETKEY='', APIKEY=''):
        self.SECRETKEY = SECRETKEY
        self.APIKEY = APIKEY
        self.APIURL = "https://open-api.bingx.com"

    def get_sign(self, api_secret, payload):
        signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
        return signature

    def send_request(self, method, path, urlpa, payload):
        url = "%s%s?%s&signature=%s" % (self.APIURL, path, urlpa, self.get_sign(self.SECRETKEY, urlpa))
        # print(url)
        headers = {
            'X-BX-APIKEY': self.APIKEY,
        }
        response = requests.request(method, url, headers=headers, data=payload)
        return response.json()

    def praseParam(self, paramsMap):
        sortedKeys = sorted(paramsMap)
        paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
        return paramsStr+"&timestamp="+str(int(time.time() * 1000))


    def getSymbols(self, symbol=""):
        payload = {}
        path = '/openApi/spot/v1/common/symbols'
        method = "GET"
        paramsMap = {
        "symbol": symbol
        }
        paramsStr = self.praseParam(paramsMap)
        return self.send_request(method, path, paramsStr, payload)
    
    def getKline(self, symbol, interval, startTime='', endTime='', limit=''):
        payload = {}
        path = '/openApi/spot/v2/market/kline'
        method = "GET"
        paramsMap = {
        "symbol": symbol,
        "interval": interval,
        "startTime": startTime,
        "endTime": endTime,
        "limit": limit
        }
        paramsStr = self.praseParam(paramsMap)
        return self.send_request(method, path, paramsStr, payload)

    def getBalance(self):
        payload = "POST"
        path = '/openApi/spot/v1/account/balance'
        method = "POST"
        paramsMap = {
        "recvWindow": 0
        }
        paramsStr = self.praseParam(paramsMap)
        return self.send_request(method, path, paramsStr, payload)
    
    def newOrder(self, symbol, side, type_, quantity='', quoteOrderQty='', price='', orderId='', stopPrice=''):
        payload = {}
        path = '/openApi/spot/v1/trade/order'
        method = "POST"
        paramsMap = {
            "symbol": symbol,
            "side": side,
            "type": type_,
            # "timeInForce": 0,
            "quantity": quantity,
            "quoteOrderQty": quoteOrderQty,
            "price": price,
            "newClientOrderId": orderId,
            "stopPrice": stopPrice,
            "recvWindow": 0
            }
        paramsStr = self.praseParam(paramsMap)
        return self.send_request(method, path, paramsStr, payload)






# with open('config.json') as f:
#     config = json.load(f)

# api = SpotAPI(config['api_secret'] , config['api_key'])

# # # data = api.getSymbols(symbol="BTC-USDT")
# data = api.getKline(symbol="BTC-USDT", interval='1m', limit=5)
# # # # data = api.getBalance()
# # # # data = api.newOrder(symbol="BTC-USDT", side='BUY', type_="LIMIT", quoteOrderQty=10, price=30000)
# # print(data['data'])
# import pandas as pd
# klines = pd.DataFrame(data['data'][::-1][:-1], columns=['time', 'open', 'high', 'low', 'close', 'Filled_price', 'close_time', 'vol'])
# klines = klines[['time', 'open', 'high', 'low', 'close']]
# klines['time'] = pd.to_datetime(klines['time']*1000000)
# print(klines)
