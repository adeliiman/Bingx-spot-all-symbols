import requests, json, time
from datetime import datetime
import pandas as pd
from datetime import datetime, timedelta
from models import Signal, Setting, Symbols
from BingXApi import BingXApi
import concurrent.futures
from database import SessionLocal


from setLogger import get_logger
logger = get_logger(__name__)


db = SessionLocal()

with open('config.json') as f:
    config = json.load(f)

api = BingXApi(SECRETKEY=config['api_secret'], APIKEY=config['api_key'])


class BingX:
	def __init__(self):
		self.bot = 'Stop' # 'Run'
		self.kline = False
		self.symbols = []
		self.timeframe = '15min'
		#self.leverage = 5

	
	def _getInterval(self, interval):
		if interval == '15min' or interval == '30min':
			gap = interval[:2]
			interval = gap
		elif interval == '1hour' or interval == '4hour':
			gap = int(interval[0]) * 60
			interval = int(interval[0])
		else:
			gap = interval[0]
			interval = gap
		return interval, gap


	def _try(self, method:str, **kwargs):
		try:
			if method == 'getPositions':
				res = api.getPositions(symbol=kwargs.get('symbol'))
			elif method == 'getOrders':
				res = api.getOrders(symbol=kwargs.get('symbol'))
			elif method == 'placeOrder':
				symbol = kwargs.get('symbol')
				side = kwargs.get('side')
				price = kwargs.get('price')
				volume = kwargs.get('volume')
				tradeType = kwargs.get('tradeType')
				action = kwargs.get('action')
				stopLossPrice = kwargs.get('stopLossPrice')
				takerProfitPrice = kwargs.get('takerProfitPrice')
				res = api.placeOrder(symbol=symbol, side=side, price=price, volume=volume, 
				tradeType=tradeType, action=action, stopLossPrice=stopLossPrice, takerProfitPrice=takerProfitPrice)
			elif method == 'getBalance':
				res = api.getBalance()
			elif method == "setLeverage":
				symbol = kwargs.get('symbol')
				side = kwargs.get('side')
				leverage = kwargs.get('leverage')
				res = api.setLeverage(symbol=symbol, side=side, leverage=leverage)
				return res
			elif method == "getKlines":
				symbol = kwargs.get('symbol')
				interval = kwargs.get('interval')
				startTime = kwargs.get('startTime')
				endTime = kwargs.get('endTime')
				klines = api.getKlines(symbol=symbol, klineType=interval, startTs=startTime, endTs=endTime)
				res = klines
			elif method == "klines":
				symbol = kwargs.get('symbol')
				t = 0
				interval, gap = self._getInterval(self.timeframe)
				stime = self._try(method='getServerTime')
				if not stime: return None
				stime = stime['currentTime']
				#
				now = datetime.now()
				startTime = now - timedelta(minutes=499*int(gap))
				startTime = int(startTime.timestamp() * 1000)
				endTime = int(now.timestamp() * 1000)
				while (stime - t) > 2*int(gap)*60000:
					try:
						klines = self._try(method='getKlines', symbol=symbol, interval=interval, startTime=startTime, endTime=endTime)
						if not klines: return None
						klines = klines['klines']
						#t = int(klines[-1][0]) # for binance
						t = klines[-1]['ts']
						#print(f'{symbol}: open kline: ... ...', datetime.fromtimestamp(t/1000), "server time: ", datetime.fromtimestamp(stime/1000))
					except Exception as e:
						logger.debug('e in market.get_kline_data ', e)
						time.sleep(1)
				
				return klines
			elif method == "getSignal":
				symbol = kwargs.get('symbol')
				klines = self._try(method='klines', symbol = symbol)
				if not klines: return None
				signal = None
				priceLevels = []
				level0 = 0
				peak2 = 0
				df = ta.DataFrame(klines)
				df = df[['open', 'close', 'high', 'low', 'time']]
				df.open = pd.to_numeric(df.open); df.close = pd.to_numeric(df.close); df.high = pd.to_numeric(df.high); df.low = pd.to_numeric(df.low)
				df.columns = ['Open', 'Close', 'High', 'Low', 'Date']
				df['rsi'] = ta.rsi(df.Close, length=14)
				df.Date = pd.to_datetime(df.Date * 1000000)
				isSignal, side, level0 = checkSignal(df)
				#
				isSignal = True
				if isSignal:
					data = db.query(Symbols).where(Symbols.symbol==symbol).first()
					fibonacci_levels = [data.fibo1, data.fibo2, data.fibo3, data.slLevel]
					priceLevels, peak2 = findPriceLevels(df, side, level0, fibonacci_levels)
					if priceLevels: signal = side

				res = {"data": (signal,level0, peak2, priceLevels, df['Date'].iloc[-1]), "code":0}
			elif method == "getServerTime":
				res = api.getServerTime()
			elif method == "setMarginMode":
				res = api.setMarginMode(symbol=kwargs.get('symbol'), marginMode=kwargs.get('marginMode'))
				res['data'] = None
			elif method == "getLatestPrice":
				symbol = kwargs.get('symbol')
				res = api.getLatestPrice(symbol=symbol)
			elif method == "closeAll":
				api.closeAllOrders()
				res = api.closeAllPositions()
			if res and res['code']:
				logger.debug(f'unSuccess---{method}', exc_info=True) 
				return None
			return res['data']
		except Exception as e:
			logger.exception(f"Exception occurred _try method: {method}", exc_info=e)


	def placeOrders(self, **kwargs):
		symbol = kwargs.get('symbol')
		positionSide = kwargs.get('positionSide')
		priceLevels = kwargs.get('priceLevels')
		priceLevel0 = kwargs.get('priceLevel0')
		dtime = kwargs.get('dtime')
		peak2 = kwargs.get('peak2')
		margin = float(Bingx._try(method='getBalance')['account']['balance'])
		if not margin: return None
		margin = margin / int(len(Bingx.symbols))
		data = db.query(Symbols).where(Symbols.symbol==symbol).first()
		# set margin mode
		Bingx._try(method="setMarginMode", symbol=symbol, marginMode=data.marginMode)
		per = (data.vol1, data.vol2, data.vol3)
		leverage = data.leverage
		size = [ round( ((data/(sum(per)))*margin / priceLevel0) * leverage, 4) for data in per]
		Bingx._try(method='setLeverage', symbol=symbol, side=positionSide, leverage=leverage)
		side = "Bid" if positionSide == "Long" else "Ask"
		TP = [priceLevel0, priceLevels[0], priceLevels[1] , priceLevels[2]]
		# placeOrder
		for i, price in enumerate(priceLevels[:-1]):
			Bingx._try(method='placeOrder', symbol=symbol, side=side, price=price, volume=size[i], tradeType="Limit", 
					action="Open", stopLossPrice=priceLevels[-1], takerProfitPrice=TP[i])
			
		self.addSignal(symbol=symbol, side=positionSide, level0=priceLevel0, level1=priceLevels[0], level2=priceLevels[1], 
		 				level3=priceLevels[2], SLPrice=priceLevels[3], vol1=size[0], vol2=size[1], vol3=size[2], dtime=dtime, 
						peak2=peak2)
		
		msg = {"symbol": symbol, "status": "", "time": str(dtime), "side":positionSide, "peak2": str(peak2), "level0": str(priceLevel0),
	 			 "level1": str(priceLevels[0]),"level2": str(priceLevels[1]), "level3": str(priceLevels[2]), 
				 "SLPrice": str(priceLevels[3]), "vol1": str(size[0]), "vol2": str(size[1]), "vol3": str(size[2])}
		toTelegram(msg)


	def addSignal(self, **kwargs):
		signal = Signal()
		signal.symbol = kwargs.get("symbol")
		signal.side = kwargs.get("side")
		signal.peak2 = kwargs.get('peak2')
		signal.level0 = kwargs.get("level0")
		signal.level1 = kwargs.get("level1")
		signal.level2 = kwargs.get("level2")
		signal.level3 = kwargs.get("level3")
		signal.SLPrice = kwargs.get("SLPrice")
		signal.vol1 = kwargs.get("vol1")
		signal.vol2 = kwargs.get("vol2")
		signal.vol3 = kwargs.get("vol3")
		signal.time = kwargs.get("dtime")
		db.add(signal)
		db.commit()
		db.refresh(signal)
		db.close()


	def cancelAllOrdersSymbol(self, **kwargs):
		symbol = kwargs.get('symbol')
		status = kwargs.get('status')
		try:
			orders = Bingx._try(method="getOrders", symbol=symbol)
			orders = orders["orders"]
			if orders:
				for order in orders:
					api.closeOrder(symbol=symbol, orderId=order["orderId"])
					# Update DB
			data = db.query(Signal).where(Signal.symbol==symbol).order_by(Signal.id.desc()).first()
			if data:
				data.status = status
				db.commit()
		except Exception as e:
			logger.exception("Exeption in close Orders. ", exc_info=e)


	def closeAllPositionSymbol(self, **kwargs):
		symbol = kwargs.get('symbol')
		try:
			position = Bingx._try(method='getPositions', symbol=symbol)
			position = position["positions"]
			if position:
				position = position[0]
				positionId = position['positionId']
				api.closePosition(symbol=symbol, positionId=positionId)
		except Exception as e:
			logger.exception("Exception --- closeAllPositionSymbol", exc_info=e)


Bingx = BingX()

