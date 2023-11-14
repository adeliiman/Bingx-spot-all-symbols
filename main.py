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
	timeframe: str = '15min'
	best_symbol: dict = {}


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
				logger.debug(f'un-success---{method}: '+ str(res)) 
				return None
			logger.debug(msg=f"method: {method}" )
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
	klines = klines[::-1][:-1] # last kline is not close
	klines = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'Filled_price', 'close_time', 'vol'])
	klines['time'] = pd.to_datetime(klines['time']*1000000)
	klines = klines[['time', 'open', 'high', 'low', 'close']] # last row is last kline
	#
	signal_ribbon = Ma_Ribbon(klines['close'])
	signal_chandelier = Chandelier_Exit(df=klines)

	signal = None
	ribbon = signal_ribbon[1:]
	ribbon.sort() # min to max/ Ascending
	last_kline_percent = (klines['close'].values[-1] - klines['open'].values[-1]) / klines['open'].values[-1]
	over_ema_lines = klines['open'].values[-1] > ribbon[-1]

	if signal_chandelier == "Buy" and signal_ribbon[0] == "Buy" and last_kline_percent > 0 and over_ema_lines:
		signal = "Buy", last_kline_percent
	elif signal_chandelier == "Sell" and klines['close'].values[-1] < ribbon[2] and klines['open'].values[-1] < ribbon[2]:
		signal = "Sell", last_kline_percent
	
	logger.debug(msg=f"signal: {symbol}: {signal} \n signal_ribbon: {signal_ribbon[0]} \n signal_chandelier: {signal_chandelier}")
	return signal


def new_trade(items):
	symbol = items[0]
	interval = items[1]
	signal, last_kline_percent = get_signal(symbol, interval)

	if signal == "Buy":
		# res = Bingx._try(method="newOrder", symbol=symbol, side='BUY', quoteQty=Bingx.trade_value)
		if last_kline_percent > Bingx.best_symbol.get('percent', default=0):
			Bingx.best_symbol['percent'] = last_kline_percent
			Bingx.best_symbol['symbol'] = symbol
	elif signal == "Sell":
		qty = Bingx._try(method='getBalance')
		qty = qty['balances']
		_qty = 0
		for q in qty:
			if q['asset'] == symbol.split('-')[0]:
				_qty = float(q['free'])
				break
		if _qty:
			res = Bingx._try(method="newOrder", symbol=symbol, side='SELL', qty=_qty)


def schedule_signal():
	Bingx.best_symbol = {}
	symbols = Bingx.user_symbols
	if Bingx.use_all_symbols == "All_symbols": 
		symbols = Bingx.All_symbols[:10]

	min_ = time.gmtime().tm_min

	if Bingx.timeframe == "1min":
		tf = '1m'
	elif Bingx.timeframe == "5min" and (min_ % 5 == 0):
		tf = '5m'
	elif Bingx.timeframe == "15min" and (min_ % 15 == 0):
		tf = '15m'
	elif Bingx.timeframe == "30min" and (min_ % 30 == 0):
		tf = '30m'
	elif Bingx.timeframe == "1hour" and (min_ == 0):
		tf = '1h'
	elif Bingx.timeframe == "4hour" and (min_ == 0):
		tf = '4h'

	with concurrent.futures.ThreadPoolExecutor(max_workers=len(symbols)+1) as executor:
		items = [(sym, f'{tf}') for sym in symbols]
		executor.map(new_trade, items)
	
	if Bingx.best_symbol:
		res = Bingx._try(method="newOrder", symbol=Bingx.best_symbol['symbol'], side='BUY', quoteQty=Bingx.trade_value)
		Bingx.best_symbol = {}


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