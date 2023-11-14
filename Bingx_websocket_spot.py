
import websocket, time, gzip
import json, requests
from database import SessionLocal
from models import  Signal
from setLogger import get_logger


logger = get_logger(__name__)


with open('config.json') as f:
    config = json.load(f)




class BingxWS:
    def __init__(self, handler=None, sub=None, Bingx=None):
        self.url = "wss://open-api-ws.bingx.com/market"
        self.APIKEY = config['api_key']
        # self.url = f"wss://open-api-ws.bingx.com/market?listenKey={self.getListenKey()}"
        self.handeler = handler
        self.sub = sub
        self.Bingx = Bingx
        self.ws = None
        self.listenKey = ''
        self.extendListenKeyStatus = False
        self.headers = {
            'Host': 'open-api-swap.bingx.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X -1_0_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        }
        
    def getListenKey(self):
        headers = {"X-BX-APIKEY" : self.APIKEY}
        res = requests.post("https://open-api.bingx.com/openApi/user/auth/userDataStream", headers=headers)
        self.listenKey = res.json()['listenKey']
        print(self.listenKey)
        return self.listenKey
    
    def extendListenKey(self):
        headers = {"X-BX-APIKEY" : self.APIKEY}
        res = requests.put(f"https://open-api.bingx.com/openApi/user/auth/userDataStream?listenKey={self.listenKey}", headers=headers)
        #print("extendListenKey:......", res)
        return res
    

    def on_open(self, ws):
        # subscribe = {"id":"24dd0e35-56a4-4f7a-af8a-394c7060909c","dataType":"BTC-USDT@trade"} 
        subscribe = self.sub
        ws.send(json.dumps(subscribe))
        # for sub in subscribe:
        #     ws.send(json.dumps(sub))


    def on_message(self, ws, msg):
        data = gzip.decompress(msg)
        data = str(data,'utf-8')
        data = json.loads(data)
        if not self.Bingx.ws:
            self.stop()

        if "ping" in data:
            ws.send(json.dumps({"pong": data['ping'], "time": data['time']}))
            if int(time.strftime('%M', time.localtime(time.time()))) % 30 == 0 and (not self.extendListenKeyStatus):
                #print('its time to extend key .... .... .... .... .... .... ... ... ...')
                self.extendListenKey()
                self.extendListenKeyStatus = True
            elif int(time.strftime('%M', time.localtime(time.time()))) % 30 != 0:
                self.extendListenKeyStatus = False
        else:
             self.handeler(data)


    def on_error(self, ws, error):
        print('on_error: ', error)


    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")
        if close_status_code or close_msg:
            print("close status code: " + str(close_status_code))
            print("close message: " + str(close_msg))
        if self.Bingx.bot == "Run":
            print("try open websocket ...................")
            self.start()


    def start(self):
        #websocket.enableTrace(True)
        listenKey = self.getListenKey()
        self.ws = websocket.WebSocketApp(url=self.url+f"?listenKey={listenKey}", 
                                on_open=self.on_open, 
                                on_close=self.on_close,
                                on_message=  self.on_message,
                                on_error=self.on_error,
                                header = self.headers)
        print("BingX WS OPENING ... ... ...")
        self.ws.run_forever()#dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
        #rel.signal(2, rel.abort)  # Keyboard Interrupt
        #rel.dispatch()


    def stop(self):
        self.ws.close()
        print('BingxWS  Closed.')



def start_bingx_ws():
    subscribe = {"id": "spot", "dataType": "spot.executionReport"}
    from main import Bingx
    bingxWS =  BingxWS(handler=handler, sub=subscribe, Bingx=Bingx)
    bingxWS.start()


def handler(data):
    
    print(data)
    if 'data' in data:
        data = data['data']
        event_Type = data['e']
        event_Time = data['E']
        pair = data['s']
        direction = data['S']
        order_Type = data['o']
        quantity = data['q']
        price = data['p']

        print(pair, event_Type, event_Time, direction, order_Type, quantity, price)
        try:
            signal = Signal()
            signal.symbol = pair
            signal.price = price
            signal.side = direction
            signal.qty = quantity
            signal.time = event_Time
            db = SessionLocal()
            db.add(signal)
            db.commit()
            db.close()
        except Exception as e:
            logger.exception(msg="add signal: "+ str(e))

