import pandas_ta as ta


def Ma_Ribbon(close, length1=40, length2=60, length3=80, length4=100):
    ema1 = ta.ma(name='ema', source=close, length=length1) # green
    ema2 = ta.ma(name='ema', source=close, length=length2) # blue
    ema3 = ta.ma(name='ema', source=close, length=length3) # yellow
    ema4 = ta.ma(name='ema', source=close, length=length4) # red
    signal = None
    if ema1[-1] < ema2[-1] < ema3[-1] < ema4[-1]:
        signal = "Short"
    elif ema1[-1] > ema2[-1] > ema3[-1] > ema4[-1]:
        signal = "Long"
    return ema1[-1], ema2[-1], ema3[-1], ema4[-1], signal


def Chandelier_Exit(df, length=22, mult=3):

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
    if df['dir'].iloc[-1] == 1 and df['dir'].iloc[-2] == -1:
        signal = 'Buy'
    elif df['dir'].iloc[-1] == -1 and df['dir'].iloc[-2] == 1:
        signal = 'Sell'
    
    del df
    return signal