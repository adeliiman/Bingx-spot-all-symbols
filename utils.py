import pandas_ta as ta
from sqlalchemy.orm import Session
from models import Setting, Symbols, AllSymbols, Signal

from setLogger import get_logger

logger = get_logger(__name__)


def Ma_Ribbon(close, length1=40, length2=60, length3=80, length4=100):
    try:
        ema1 = ta.ma(name='ema', source=close, length=length1) # green
        ema2 = ta.ma(name='ema', source=close, length=length2) # blue
        ema3 = ta.ma(name='ema', source=close, length=length3) # yellow
        ema4 = ta.ma(name='ema', source=close, length=length4) # red
        signal = None

        def cond_sell(i):
            return ema1.values[-i] < ema2.values[-i] < ema3.values[-i] < ema4.values[-i]
        def cond_buy(i):
            ema1.values[-i] > ema2.values[-i] > ema3.values[-i] > ema4.values[-i]
        
        if cond_sell(1) and not cond_sell(2):
            signal = "Short"
        elif cond_buy(1) and not cond_buy(2):
            signal = "Long"
        
        return  [signal, ema1.values[-1], ema2.values[-1], ema3.values[-1], ema4.values[-1] ]
    except Exception as e:
        logger.exception(msg="Ma_Ribbon error.", exc_info=e)



def Chandelier_Exit(df, length=22, mult=3):
    try:
        def wwma(values, n):
            return values.ewm(alpha=1/n, adjust=False).mean()
        def atr(df, n):
            data = df.copy()
            high = data['high']
            low = data['low']
            close = data['close']
            data['tr0'] = abs(high - low)
            data['tr1'] = abs(high - close.shift())
            data['tr2'] = abs(low - close.shift())
            tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
            atr = wwma(tr, n)
            return atr
        
        df['atr'] = mult * atr(df, length)
        df['dir'] = 0

        df['longStop'] = df['close'].rolling(length).max() - df['atr']
        df['shortStop'] = df['close'].rolling(length).min() + df['atr']

        for i in df.index:
            if df['close'].iloc[i-1] > df['longStop'].iloc[i-1]:
                df.at[i, 'longStop'] = max(df['longStop'].iloc[i], df['longStop'].iloc[i-1])
            
            if df['close'].iloc[i-1] < df['shortStop'].iloc[i-1]:
                df.at[i, 'shortStop'] = min(df['shortStop'].iloc[i], df['shortStop'].iloc[i-1])

            if df['close'].iloc[i] > df['shortStop'].iloc[i-1]:
                df.at[i, 'dir'] = 1
            elif df['close'].iloc[i] < df['longStop'].iloc[i-1]:
                df.at[i, 'dir'] = -1
            else:
                df.at[i, 'dir'] = df['dir'].iloc[i-1]

        df = df.round(decimals = 4)
        # print(df.tail(10))
        signal = None
        if df['dir'].iloc[-1] == 1 and df['dir'].iloc[-2] == -1:
            signal = 'Buy'
        elif df['dir'].iloc[-1] == -1 and df['dir'].iloc[-2] == 1:
            signal = 'Sell'
        
        del df
        return signal
    except Exception as e:
        logger.exception(msg="Chandelier_Exit error.", exc_info=e)


def get_user_params(db: Session):
    try:
        user = db.query(Setting).first()
        user_symbols = db.query(Symbols).all()
        All_symbols = db.query(AllSymbols).all()
        from main import Bingx
        Bingx.ma1 = user.ma1
        Bingx.ma2 = user.ma2
        Bingx.ma3 = user.ma3
        Bingx.ma4 = user.ma4
        Bingx.chandelier_length = user.chandelier_length
        Bingx.chandelier_multi = user.chandelier_multi
        Bingx.trade_value = user.trade_value
        Bingx.timeframe = user.timeframe
        Bingx.use_all_symbols = user.use_all_symbols
        for sym in user_symbols:
            Bingx.user_symbols.append(sym.symbol)

        for sym in All_symbols:
            Bingx.All_symbols.append(sym.symbol)
    except Exception as e:
        logger.exception(msg="get_user_params", exc_info=e)


