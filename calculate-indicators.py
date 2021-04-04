from os import close
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
# https://tradingstrategyguides.com/best-combination-of-technical-indicators/

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

# what seems to work best is if you have 1 of 3 (but voume seems to be swapped with volatility sometimes) of the catergories or indicators
# a suggested one is RSI, OBV, and Ichimoku Kinko Hyo (Ichimoku Cloud)

# momentum
closes = []
rsi = []
short_MA = []
long_MA = []
short_EMA = []
long_EMA = []
stoch = []
stochd = []
uo = []

#volume
obv = []

# volitility
msd = [] #standard deviation

# trend
cloud = []
bbands = [] 

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

        # On balance volume
        if len(closes) >= RSI_PERIOD:
            temp_OBV = TA.OBV(candle, 'close')
            obv.append(temp_OBV.iat[-1])

        # Ichimoku Kinko Hyo (Ichimoku Cloud)
        if len(closes) >= 52:
            temp_cloud = TA.ICHIMOKU(candle, 9, 26, 52, 26)
            # tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span
            cloud_diff = temp_cloud.iloc[-1].senkou_span_a - temp_cloud.iloc[-1].SENKOU
            temp = [temp_cloud.iloc[-1].TENKAN, temp_cloud.iloc[-1].KIJUN, cloud_diff, temp_cloud.iloc[-1].senkou_span_a, temp_cloud.iloc[-1].SENKOU, temp_cloud.iloc[-1].CHIKOU]
            cloud.append(temp)

        # Bollinger Bands
        # This is taking a moving average as an input. Currently taking a simple MA but can take any MA
        if len(closes) >= 20:
            temp_bbands = TA.BBANDS(candle, 20, TA.SMA(candle, 20, "close"), "close", 2)
            temp = [temp_bbands.iloc[-1].BB_LOWER, temp_bbands.iloc[-1].BB_MIDDLE, temp_bbands.iloc[-1].BB_UPPER]
            bbands.append(temp)

        # Bollinger Bands
        # This is taking a moving average as an input. Currently taking a simple MA but can take any MA
        if len(closes) >= 22:
            temp_msd = TA.MSD(candle, 21, 1, "close")
            msd.append(temp_msd.iat[-1])




# opens a raw data output file binance-output-1616948205000
file = open("historical-binance-data-1616972113000.txt", 'r')
raw_data = file.readlines()

# build frame
#df = pd.DataFrame([], columns=['TimeStamp', 'open', 'high', 'low', 'close', 'volume', 'Quote', 'Number of trades', 'Taker base', 'Taker quote', '7x short SMA', '25x long SMA', '7x short EMA', '25x long EMA', 'RSI', 'StochasticOscillator_K', 'StochasticOscillator_D', 'UltimateOscillator', 'OnBalanceVolume', 'MovingStandardDeviation'])

# with cloud and bolligner
df = pd.DataFrame([], columns=[
    'TimeStamp', 'open', 'high', 'low', 'close', 'volume', 'Quote', 'NumberOfTrades', 'TakerBase', 'TakerQuote', 
    '7xshortSMA', '25xlongSMA', '7xshortEMA', '25xlongEMA', 
    'RSI', 'StochasticOscillator_K', 'StochasticOscillator_D', 'UltimateOscillator', 
    'OnBalanceVolume', 
    'MovingStandardDeviation', 
    'IchimokuCloud_TENKAN', 'IchimokuCloud_KIJUN', 'IchimokuCloud_SENKOU_Diff', 'IchimokuCloud_SENKOU_SpanA', 'IchimokuCloud_SENKOU_SpanB', 'IchimokuCloud_CHIKOU', 
    'BollingerBands_LOWER', 'BollingerBands_MIDDLE', 'BollingerBands_UPPER'])
# print(df)

# iterates through the raw data that was in the output file and calculates each indicator for at that candle
for line in raw_data:
    # adds the raw data to dataframe
    candle = line.split("  ")
    candle.pop(0)
    df = df.append({'TimeStamp': float(candle[0]), 'open': float(candle[1]), 'high': float(candle[2]), 'low': float(candle[3]), 'close': float(candle[4]), 'volume': float(candle[5]),'Quote': float(candle[7]), 'NumberOfTrades': float(candle[8]), 'TakerBase': float(candle[9]), 'TakerQuote': float(candle[10])}, ignore_index=True)

    # calls method to calculate the indicators
    on_message(6, df)

    # adds each indicator to the dataframe
    if len(closes) > 52: 
        df.iloc[-1, df.columns.get_loc('7xshortEMA')] = short_EMA[-1]
        df.iloc[-1, df.columns.get_loc('25xlongEMA')] = long_EMA[-1]
        df.iloc[-1, df.columns.get_loc('7xshortSMA')] = short_MA[-1]
        df.iloc[-1, df.columns.get_loc('25xlongSMA')] = long_MA[-1]

        df.iloc[-1, df.columns.get_loc('RSI')] = rsi[-1]
        df.iloc[-1,df.columns.get_loc('StochasticOscillator_K')] = stoch[-1]
        df.iloc[-1,df.columns.get_loc('StochasticOscillator_D')] = stochd[-1]
        df.iloc[-1, df.columns.get_loc('UltimateOscillator')] = uo[-1]

        df.iloc[-1, df.columns.get_loc('OnBalanceVolume')] = obv[-1]

        df.iloc[-1, df.columns.get_loc('IchimokuCloud_TENKAN')] = cloud[-1][0]
        df.iloc[-1, df.columns.get_loc('IchimokuCloud_KIJUN')] = cloud[-1][1]
        df.iloc[-1, df.columns.get_loc('IchimokuCloud_SENKOU_Diff')] = cloud[-1][2]
        df.iloc[-1, df.columns.get_loc('IchimokuCloud_SENKOU_SpanA')] = cloud[-1][3]
        df.iloc[-1, df.columns.get_loc('IchimokuCloud_SENKOU_SpanB')] = cloud[-1][4]
        df.iloc[-1, df.columns.get_loc('IchimokuCloud_CHIKOU')] = cloud[-1][5]

        df.iloc[-1, df.columns.get_loc('BollingerBands_LOWER')] = bbands[-1][0]
        df.iloc[-1, df.columns.get_loc('BollingerBands_MIDDLE')] = bbands[-1][1]
        df.iloc[-1, df.columns.get_loc('BollingerBands_UPPER')] = bbands[-1][2]

        df.iloc[-1, df.columns.get_loc('MovingStandardDeviation')] = msd[-1]
            # print(df)
            # time.sleep(5)

# output the dataframe to a file
df = df[df.index >= 52]
market_data_file = open("market-indicators-" + str(int(time.mktime(datetime.datetime.now().timetuple())*1000)) + ".txt", "w")
market_data_file.write(str(df))
# print(df)
