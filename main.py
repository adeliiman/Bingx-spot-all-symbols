import requests, json, time
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


# db = SessionLocal()

with open('config.json') as f:
    config = json.load(f)

api = SpotAPI(config['api_secret'] , config['api_key'])


class Bingx:
	bot: str = 'Stop' # 'Run'
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
	timeframe: str = '15min'


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
			if method == 'getSymbols':
				res = api.getSymbols()
			elif method == 'getKline':
				res = api.getKline(symbol=kwargs.get('symbol'), interval=kwargs.get('interval'), limit=kwargs.get('limit'))

			if res and res['code']:
				logger.debug(f'un-success---{method}', exc_info=True) 
				return None
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


def get_signal(items):
	symbol = items[0]
	interval = items[1]
	klines = Bingx._try(method="getKline", symbol=symbol, interval=interval, limit=110)
	klines = klines[::-1][:-1] # last kline is not close
	klines = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'Filled_price', 'close_time', 'vol'])
	klines['time'] = pd.to_datetime(klines['time']*1000000)
	klines = klines[['time', 'open', 'high', 'low', 'close']] # last row is last kline
	#
	signal_ribbon = Ma_Ribbon(klines['close'])
	signal_chandelier = Chandelier_Exit(df=klines)

	signal = None
	ribbon = signal_ribbon[1:]
	ribbon.sort()
	if signal_chandelier == "Buy" and signal_ribbon[0] == "Buy":
		signal = "Buy"
	elif signal_chandelier == "Sell" and klines['high'].values[-1] < ribbon[2]:
		signal = "Sell"
	print(symbol, signal)
	return signal


def schedule_signal():

	symbols = Bingx.user_symbols
	if Bingx.use_all_symbols == "All_symbols": 
		symbols = Bingx.All_symbols[:10]

	min_ = time.gmtime().tm_min

	if Bingx.timeframe == "1min":
		with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols)+1) as executor:
			items = [(sym, '1m') for sym in symbols]
			executor.map(get_signal, items)

	elif Bingx.timeframe == "5min" and (min_ % 5 == 0):
		with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols)+1) as executor:
			items = [(sym, '5m') for sym in symbols]
			executor.map(get_signal, items)
	
	elif Bingx.timeframe == "15min" and (min_ % 15 == 0):
		with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols)+1) as executor:
			items = [(sym, '15m') for sym in symbols]
			executor.map(get_signal, items)
	
	elif Bingx.timeframe == "30min" and (min_ % 30 == 0):
		with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols)+1) as executor:
			items = [(sym, '30m') for sym in symbols]
			executor.map(get_signal, items)

	elif Bingx.timeframe == "1hour" and (min_ == 0):
		with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols)+1) as executor:
			items = [(sym, '1h') for sym in symbols]
			executor.map(get_signal, items)

	elif Bingx.timeframe == "4hour" and (min_ == 0):
		with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols)+1) as executor:
			items = [(sym, '4h') for sym in symbols]
			executor.map(get_signal, items)

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