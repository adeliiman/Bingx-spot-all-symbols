import requests, json, time, random
from datetime import datetime
import pandas as pd
from datetime import datetime, timedelta
from models import Signal, Setting, Symbols
from Bingx_api_spot import SpotAPI
import concurrent.futures
from database import SessionLocal
import schedule
from utils import Ma_Ribbon, Chandelier_Exit


from setLogger import get_logger
logger = get_logger(__name__)


with open('config.json') as f:
    config = json.load(f)

api = SpotAPI(config['api_secret'] , config['api_key'])


class Bingx:
	bot: str = 'Stop' # 'Run'
	ws: bool = True
	kline: bool = False
	use_all_symbols: str = "user_symbols"
	user_symbols: list = []
	All_symbols: list = []
	ma1: int = 40
	ma2: int = 60
	ma3: int = 80
	ma4: int = 100
	chandelier_length: int = 22
	chandelier_multi: int = 3
	trade_value: int = 10
	trade_percent: int = 50
	trade_volume: str = "trade_value"
	timeframe: str = '15min'
	best_symbol: dict = {}
	balance: list = []
	ema_offset: int = 10
	ema_percent: float = 0.1


	def _try(self, method:str, **kwargs):
		try:
			if method == 'getSymbols':
				res = api.getSymbols()
			elif method == 'getKline':
				res = api.getKline(symbol=kwargs.get('symbol'), interval=kwargs.get('interval'), limit=kwargs.get('limit'))
			elif method == 'newOrder':
				res = api.newOrder(symbol=kwargs.get('symbol'), side=kwargs.get('side'),
						quoteOrderQty=kwargs.get('quoteQty', ''), quantity=kwargs.get('qty', ''))
			elif method == 'getBalance':
				res = api.getBalance()

			if res and res['code']:
				logger.info(f"un-success---{method}-symbol: {kwargs.get('symbol')}: "+ str(res)) 
				return None
			logger.info(msg=f"method: {method}--symbol: {kwargs.get('symbol')}" )
			return res['data']
		except Exception as e:
			logger.exception(f"Exception occurred _try method: {method}", exc_info=e)

	def loadSymbols(self):
		data = Bingx._try(method='getSymbols')
		if not data:
			return None
		data = data['symbols']
		all_symbol = []
		for d in data:
			if d['symbol'][-4:] == 'USDT' and d['symbol'][:4]!= "USDC":
				all_symbol.append(d['symbol'])
		return all_symbol

	
Bingx = Bingx()


def get_signal(symbol:str, interval):
	
	klines = Bingx._try(method="getKline", symbol=symbol, interval=interval, limit=110)
	if not klines:
		return None, 0, 0
	klines = klines[::-1][:-1] # last kline is not close
	klines = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'Filled_price', 'close_time', 'vol'])
	klines['time'] = pd.to_datetime(klines['time']*1000000)
	klines = klines[['time', 'open', 'high', 'low', 'close']] # last row is last kline
	#
	signal_ribbon = Ma_Ribbon(klines['close'], length1=Bingx.ma1, length2=Bingx.ma2, length3=Bingx.ma3, length4=Bingx.ma4)
	signal_chandelier = Chandelier_Exit(df=klines, length=Bingx.chandelier_length, mult=Bingx.chandelier_multi)

	signal = None
	ribbon = signal_ribbon[1:]
	ribbon.sort() # min to max/ Ascending
	last_kline_percent = (klines['close'].iat[-1] - klines['open'].iat[-1]) / klines['open'].iat[-1]
	over_ema_lines = klines['open'].iat[-1] > ribbon[-1]

	logger.info(f"{symbol}: signal_ribbon: {signal_ribbon[0]}  signal_chandelier: {signal_chandelier} over_ema_lines: {over_ema_lines}")

	if signal_chandelier == "Buy" and signal_ribbon[0] == "Buy" and last_kline_percent > 0 and over_ema_lines:
		signal = "Buy"
	elif signal_chandelier == "Sell" or (klines['close'].iat[-1] < ribbon[2] and klines['open'].iat[-1] < ribbon[2]):
		signal = "Sell"
	
	logger.info(msg=f"signal: {symbol}: {signal}  ,last_kline_percent: {last_kline_percent}")
	return signal, last_kline_percent, klines['close'].iat[-1]


def add_to_sqlite(pair, price, direction, quantity):
	try:
		signal = Signal()
		signal.symbol = pair
		signal.price = price
		signal.side = direction
		signal.qty = quantity
		event_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		signal.time = event_time
		db = SessionLocal()
		db.add(signal)
		db.commit()
		db.close()
		logger.info(msg=f"add order to sqlite: {pair}-{price}-{direction}-{quantity}-{event_time}")
	except Exception as e:
		logger.exception(msg="add signal: "+ str(e))

def new_trade(items):
	try:
		time.sleep(0.5 + random.randint(5, 9)/100)
		symbol = items[0]
		interval = items[1]
		signal, last_kline_percent, price = get_signal(symbol, interval)

		if signal == "Buy":
			# res = Bingx._try(method="newOrder", symbol=symbol, side='BUY', quoteQty=Bingx.trade_value)
			if last_kline_percent > Bingx.best_symbol.get('percent', 0):
				Bingx.best_symbol['percent'] = last_kline_percent
				Bingx.best_symbol['symbol'] = symbol
				Bingx.best_symbol['price'] = price
				logger.info(f"set best symbol: {symbol}---{last_kline_percent}")
		elif signal == "Sell":
			
			_qty = 0
			for q in Bingx.balance:
				if q['asset'] == symbol.split('-')[0]:
					_qty = float(q['free'])
					break
			logger.info(f"quantity: {_qty}---{symbol}")
			if _qty and price*_qty>2:
				res = Bingx._try(method="newOrder", symbol=symbol, side='SELL', qty=_qty)
				logger.info(f"sell order {symbol}---{_qty}-dollar")
				if not res:
					return None
				add_to_sqlite(pair=symbol, price=price, direction='Sell', quantity=_qty)

	except Exception as e:
		logger.exception(str(e))


def schedule_signal():
	try:
		Bingx.best_symbol = {}
		symbols = Bingx.user_symbols
		if Bingx.use_all_symbols == "All_symbols": 
			symbols = Bingx.All_symbols

		min_ = time.gmtime().tm_min
		tf = None

		# if Bingx.timeframe == "1min":
		# 	tf = '1m'
		if Bingx.timeframe == "5min" and (min_ % 5 == 0):
			tf = '5m'
		elif Bingx.timeframe == "15min" and (min_ % 15 == 0):
			tf = '15m'
		elif Bingx.timeframe == "30min" and (min_ % 30 == 0):
			tf = '30m'
		elif Bingx.timeframe == "1hour" and (min_ == 0):
			tf = '1h'
		elif Bingx.timeframe == "4hour" and (min_ == 0):
			tf = '4h'

		if tf:
			qty = Bingx._try(method='getBalance')
			Bingx.balance = qty['balances']

			with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols)+1) as executor:
				items = [(sym, f'{tf}') for sym in symbols]
				executor.map(new_trade, items)
			
			if not Bingx.best_symbol:
				logger.info("nothing best symbol")
				return None
			
			logger.info(f"Buying {Bingx.best_symbol['symbol']} ... ... ...")
		
			
			balance = 0
			for q in Bingx.balance:
				if q['asset'] == "USDT":
					qty = float(q['free']) * Bingx.trade_percent / 100
				elif q['asset'] == Bingx.best_symbol['symbol'].split("-")[0]:
					balance = float(q['free'])
			if balance * Bingx.best_symbol['price'] > 5:
				logger.info(f"we have volume on {Bingx.best_symbol['symbol']}")
				return None
			
			if Bingx.trade_volume == "Dollar":
				qty = Bingx.trade_value

			res = Bingx._try(method="newOrder", symbol=Bingx.best_symbol['symbol'], side='BUY', quoteQty=qty)
			logger.info(f"buy order: {Bingx.best_symbol['symbol']}, quantity: {qty}---{Bingx.best_symbol['percent']}")
			Bingx.best_symbol = {}
			if not res:
				return None
			add_to_sqlite(pair=Bingx.best_symbol['symbol'], price=Bingx.best_symbol['price'], direction='Buy', quantity=qty)
	except Exception as e:
		logger.exception(str(e))


def main_job():
    schedule.every(1).minutes.at(":02").do(job_func=schedule_signal)

    while True:
        if Bingx.bot == "Stop":
            #schedule.cancel_job(my_job)
            schedule.clear()
            break
        schedule.run_pending()
        print(time.ctime(time.time()))
        time.sleep(1)