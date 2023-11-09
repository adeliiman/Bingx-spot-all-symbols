import requests
import requests, json, time, math
import hmac, hashlib, base64, urllib
import time
import json


with open('config.json') as f:
    config = json.load(f)


class BingXApi:
    def __init__(self, SECRETKEY='', APIKEY=''):
        self.SECRETKEY = SECRETKEY
        self.APIKEY = APIKEY
        self.APIURL = "https://api-swap-rest.bingbon.pro"

    try:
        
        def genSignature(self, path, method, paramsMap):
            sortedKeys = sorted(paramsMap)
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
            paramsStr = method + path + paramsStr
            #ret = hmac.new(SECRETKEY.encode("utf-8"), paramsStr.encode("utf-8"), digestmod=hashlib.sha256).digest()
            ret = hmac.new(bytes(self.SECRETKEY, 'utf-8'), bytes(paramsStr, 'utf-8'), digestmod=hashlib.sha256).digest()
            ret = base64.b64encode(ret).decode("utf-8")
            import urllib.parse
            ret = urllib.parse.quote_plus(ret)
            return ret


        def post(self, url, body):
            url +=  body
            res = requests.post(url)
            return res.json()


        def convertSymbol(self, symbol):
            idx = symbol.index('USD')
            symbol = symbol[:idx] + "-" + symbol[idx:]
            return symbol


        def getServerTime(self):
            url = "https://api-swap-rest.bingbon.pro/api/v1/common/server/time"
            res = requests.get(url)
            res = res.json()
            return res


        def getLatestPrice(self,symbol):
            url = "https://api-swap-rest.bingbon.pro/api/v1/market/getLatestPrice?"+"symbol="+symbol
            res = requests.get(url)
            res = res.json()
            return res#['data']['tradePrice']


        def getLastKline(self,symbol, klineType):
            # Last kline is open
            url = "https://api-swap-rest.bingbon.pro/api/v1/market/getLatestKline?"+\
            "symbol="+symbol+"&"+"klineType="+str(klineType)
            res = requests.get(url)
            res = res.json()
            return res


        def getKlines(self,symbol, klineType, startTs, endTs): # Max limit = 1440
            url = "https://api-swap-rest.bingbon.pro/api/v1/market/getHistoryKlines?"+\
            "symbol="+symbol+"&"+"klineType="+str(klineType)+"&"+"startTs="+str(startTs)+\
            "&"+"endTs="+str(endTs)
            res = requests.get(url)
            res = res.json()
            return res


        def getBalance(self):
            paramsMap = {
            "currency": "USDT",
            "apiKey": self.APIKEY,
            "timestamp": int(time.time()*1000)
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/getBalance", "POST", paramsMap)
            url = "%s/api/v1/user/getBalance?" % self.APIURL
            balance =  self.post(url, str(paramsStr))
            # margin = balance['data']['account']['availableMargin']
            return balance


        def getPositions(self, symbol):  # --> 'data': {'positions': None}
            paramsMap = {
                "symbol": symbol,
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap ])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/getPositions", "POST", paramsMap)
            url = "%s/api/v1/user/getPositions?" % self.APIURL
            return self.post(url, paramsStr)


        def getOrders(self, symbol):  # --> 'data': {'orders': None}
            paramsMap = {
                "symbol": symbol,
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap ])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/pendingOrders", "POST", paramsMap)
            url = "%s/api/v1/user/pendingOrders?" % self.APIURL
            return self.post(url, paramsStr)


        def getStopOrders(self, symbol): #--> 'data': {'orders': []}
            paramsMap = {
                "symbol": symbol,
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap ])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/pendingStopOrders", "POST", paramsMap)
            url = "%s/api/v1/user/pendingStopOrders?" % self.APIURL
            return self.post(url, paramsStr)


        def placeOrder(self, symbol, side, price, volume, tradeType, action, stopLossPrice=None, takerProfitPrice=None):
            # side: Bid/Ask
            # tradeType: Market/Limit
            # action: Open/Close
            paramsMap = {
                "symbol": symbol,
                "apiKey": self.APIKEY,
                "side": side,
                "entrustPrice": price,
                "entrustVolume": volume,
                "tradeType": tradeType,
                "action": action,
                "timestamp": int(time.time()*1000),
            }
            if stopLossPrice: paramsMap["stopLossPrice"] = stopLossPrice
            if takerProfitPrice: paramsMap["takerProfitPrice"] = takerProfitPrice
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/trade", "POST", paramsMap)
            url = "%s/api/v1/user/trade?" % self.APIURL
            return self.post(url, paramsStr)


        def placeStopOrder(self, positionId, stopLossPrice, takeProfitPrice, volume, orderId):
            paramsMap = {
                "apiKey": self.APIKEY,
                "positionId": positionId,
                "stopLossPrice": stopLossPrice,
                "takeProfitPrice": takeProfitPrice,
                "entrustVolume": volume,
                "orderId": orderId,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/stopOrder", "POST", paramsMap)
            url = "%s/api/v1/user/stopOrder?" % self.APIURL
            return self.post(url, paramsStr)


        def closePosition(self, symbol, positionId):
            paramsMap = {
                "symbol": symbol,
                "positionId": positionId,
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/oneClickClosePosition", "POST", paramsMap)
            url = "%s/api/v1/user/oneClickClosePosition?" % self.APIURL
            return self.post(url, paramsStr)


        def closeOrder(self, symbol, orderId):
            paramsMap = {
                "orderId": orderId,
                "symbol": symbol,
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000)
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/cancelOrder", "POST", paramsMap)
            url = "%s/api/v1/user/cancelOrder?" % self.APIURL
            return self.post(url, paramsStr)


        def closeStopOrder(self, symbol, orderId):
            paramsMap = {
                "orderId": orderId,
                "symbol": symbol,
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000)
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/cancelStopOrder", "POST", paramsMap)
            url = "%s/api/v1/user/cancelStopOrder?" % self.APIURL
            return self.post(url, paramsStr)


        def closeAllPositions(self):
            paramsMap = {
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/oneClickCloseAllPositions", "POST", paramsMap)
            url = "%s/api/v1/user/oneClickCloseAllPositions?" % self.APIURL
            return self.post(url, paramsStr)


        def closeAllOrders(self):
            paramsMap = {
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/cancelAll", "POST", paramsMap)
            url = "%s/api/v1/user/cancelAll?" % self.APIURL
            return self.post(url, paramsStr)


        def setLeverage(self, symbol, side, leverage):
            # side: Long/Short
            paramsMap = {
                "symbol": symbol,
                "side": side,
                "leverage": leverage,
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/setLeverage", "POST", paramsMap)
            url = "%s/api/v1/user/setLeverage?" % self.APIURL
            return self.post(url, paramsStr)


        def setMarginMode(self, symbol, marginMode):
            # marginMode: Isolated / Cross
            paramsMap = {
                "symbol": symbol,
                "marginMode": marginMode,
                "apiKey": self.APIKEY,
                "timestamp": int(time.time()*1000),
            }
            paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in paramsMap])
            paramsStr += "&sign=" + self.genSignature("/api/v1/user/setMarginMode", "POST", paramsMap)
            url = "%s/api/v1/user/setMarginMode?" % self.APIURL
            return self.post(url, paramsStr)

    except Exception as e:
        print("Exeption in API", e)





# from datetime import datetime, timedelta
# now = datetime.now()
# startTime = now - timedelta(minutes=5)
# startTs = int(startTime.timestamp() * 1000)
# endTs = int(now.timestamp() * 1000)



# api = BingXApi(SECRETKEY=config['api_secret'], APIKEY=config['api_key'])
# print(api.getServerTime())
# print(api.getLatestPrice("BTC-USDT"))
# print(api.getLastKline(symbol="BTC-USDT", klineType="1"))
# print(api.getKlines(symbol="BTC-USDT", klineType="1", startTs=startTs, endTs=endTs)['data']['klines'])
# print(api.getBalance())
# print(api.getPositions("ADA-USDT"))
# print(api.getOrders("ADA-USDT"))
# print(api.getStopOrders("ADA-USDT"))
# print(api.placeOrder(symbol="BTC-USDT", side="Bid", price='26216', volume=0.00011, tradeType='Limit', action='Open'))#, stopLossPrice=0.348))#, takerProfitPrice=0.36))

#print(api.stopOrder(positionId='1620931353748967424', stopLossPrice=0.3940, takeProfitPrice=0.399, volume=100))
#'1620931353748967424'

# print(api.setLeverage("BTC-USDT", "Long", '20'))
# print(api.setMarginMode("BTC-USDT", "Isolated"))



# print(api.closePosition(symbol="ADA-USDT", positionId='1575974277398663168'))
# print(api.closeStopOrder(symbol="ADA-USDT", orderId=123456))

# print(api.closeAllPositions())
# print( api.closeAllOrders())

