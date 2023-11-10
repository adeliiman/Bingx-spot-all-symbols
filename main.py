import requests, json, time
from datetime import datetime
import pandas as pd
from datetime import datetime, timedelta
from models import Signal, Setting, Symbols
from Bingx_api_spot import SpotAPI
import concurrent.futures
from database import SessionLocal


from setLogger import get_logger
logger = get_logger(__name__)


# db = SessionLocal()

with open('config.json') as f:
    config = json.load(f)

api = SpotAPI(config['api_secret'] , config['api_key'])


class Bingx:
	bot: str = 'Stop' # 'Run'
	kline: bool = False
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

