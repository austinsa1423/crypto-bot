import websocket
import json
import pprint
import talib
import numpy as np
import time
import datetime
import pandas as pd
import config
from binance.client import Client
from binance.enums import *
from finta import TA

# Reference
# -------------------------------
# https://github.com/peerchemist/finta

# removes limits on pandas
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', -1)

# data evalulation periods for the specific indicators
RSI_PERIOD = 15
MA_SHORT_PERIOD = 7
MA_LONG_PERIOD = 25
STOCH_PERIOD = 15
UO_PERIOD = 28

# lists that stores all fo the values for that indicator, mostly used to store temporarily till it is added to the dataframe
closes = []
rsi = []
short_MA = []
long_MA = []
short_EMA = []
long_EMA = []
stoch = []
stochd = []
uo = []

client = Client(config.API_KEY, config.API_SECRET, tld='us')


def on_message(ws, candle):
    global closes, do_i_own_coin, sells, buys, USD_avaliable, coin_avaliable

    is_candle_closed = True
    close = 1

    if is_candle_closed:
        closes.append(float(close))

        # 2 simple moving average
        if len(closes) >= MA_SHORT_PERIOD:
            np_closes = np.array(closes)
            temp_short_MA = TA.SMA(candle, MA_SHORT_PERIOD, 'close')
            short_MA.append(temp_short_MA.iat[-1])

            if len(closes) >= MA_LONG_PERIOD:
                temp_long_MA = TA.SMA(candle, MA_LONG_PERIOD, 'close')
                long_MA.append(temp_long_MA.iat[-1])

            # 2 exponential moving averages
            if len(closes) >= MA_SHORT_PERIOD:
                temp_short_EMA = TA.EMA(candle, MA_SHORT_PERIOD, 'close', True)
                short_EMA.append(temp_short_EMA.iat[-1])

            if len(closes) >= MA_LONG_PERIOD:
                temp_long_EMA = TA.EMA(candle, MA_LONG_PERIOD, 'close', True)
                long_EMA.append(temp_long_EMA.iat[-1])

        # Relative strength index
        if len(closes) >= RSI_PERIOD:
            temp_RSI = TA.RSI(candle, RSI_PERIOD, 'close', True)
            rsi.append(temp_RSI.iat[-1])

        # Stochastic Oscillator K%
        if len(closes) >= STOCH_PERIOD:
            temp_stoch = TA.STOCH(candle, STOCH_PERIOD)
            stoch.append(temp_stoch.iat[-1])

        # Stochastic Oscillator D%
        # using the same period as stoch
        if len(closes) >= STOCH_PERIOD:
            temp_stochd = TA.STOCHD(candle, 3, STOCH_PERIOD)
            stochd.append(temp_stochd.iat[-1])

        # Ultimate Oscillator
        if len(closes) >= UO_PERIOD:
            temp_uo = TA.UO(candle, 'close')
            uo.append(temp_uo.iat[-1])


# opens a raw data output file
file = open("binance-output-1615696702000.txt", 'r')
raw_data = file.readlines()

# build frame
df = pd.DataFrame([], columns=['TimeStamp', 'Open', 'High', 'Low', 'close', 'Volume', 'Quote', 'Number of trades', 'Taker base', 'Taker quote', '7x short SMA', '25x long SMA', '7x short EMA', '25x long EMA', 'RSI', 'StochasticOscillator_K', 'StochasticOscillator_D', 'UltimateOscillator'])
# print(df)

# iterates through the raw data that was in the output file and calculates each indicator for at that candle
for line in raw_data:
    # adds the raw data to dataframe
    candle = line.split("  ")
    candle.pop(0)
    df = df.append({'TimeStamp': float(candle[0]), 'Open': float(candle[1]), 'High': float(candle[2]), 'Low': float(candle[3]), 'close': float(candle[4]), 'Volume': float(candle[5]),'Quote': float(candle[7]), 'Number of trades': float(candle[8]), 'Taker base': float(candle[9]), 'Taker quote': float(candle[10])}, ignore_index=True)

    # calls method to calculate the indicators
    on_message(6, df)

    # adds each indicator to the dataframe
    if len(short_EMA) > 0:
        df.iloc[-1, df.columns.get_loc('7x short EMA')] = short_EMA[-1]
        if len(long_EMA) > 0:
            df.iloc[-1, df.columns.get_loc('25x long EMA')] = long_EMA[-1]
    if len(short_MA) > 0:
        df.iloc[-1, df.columns.get_loc('7x short SMA')] = short_MA[-1]
        if len(long_MA) > 0:
            df.iloc[-1, df.columns.get_loc('25x long SMA')] = long_MA[-1]
        if len(rsi) > 0:
            df.iloc[-1, df.columns.get_loc('RSI')] = rsi[-1]
        if len(stoch) > 0:
            df.iloc[-1,
                    df.columns.get_loc('StochasticOscillator_K')] = stoch[-1]
        if len(stochd) > 0:
            df.iloc[-1,
                    df.columns.get_loc('StochasticOscillator_D')] = stochd[-1]
        if len(uo) > 0:
            df.iloc[-1, df.columns.get_loc('UltimateOscillator')] = uo[-1]
            # print(df)
            # time.sleep(5)

# output the dataframe to a file
market_data_file = open("market-data-file-" + str(
    int(time.mktime(datetime.datetime.now().timetuple())*1000)) + ".txt", "w")
market_data_file.write(str(df))
# print(df)
