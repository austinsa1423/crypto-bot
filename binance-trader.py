import websocket, json, pprint, talib, numpy as np, time, datetime, pandas
import config
from binance.client import Client
from binance.enums import *
from finta import TA
import pandas as pd
import config

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', -1)

# Things to reference
# -------------------------------
# https://github.com/peerchemist/finta

# things that I would like to add
# --------------------------------------------------------------------
# Add in a get account balance method to update the avaliable vars after an order
# make testing new data easier?
# add MA
# when the program starts have it call historical data to populate thing like the moving average and the RSI
# rewrite the rsi in FinTA
# fnish updating the trading logic
# incorperate cancels
# determine the best type of buy or sell to make
# would having the short ma use the decline by x%  to sell and the second intersection of the 

closes = []
rsi = []
short_MA = []
long_MA = []
short_EMA = []
long_EMA = []
stoch = []
stochd = []
uo = []
obv =[]
cloud = []
bbands = []

buys = 0
sells = 0

coin_starting = 0.04834805
USD_starting = 0
do_i_own_coin = True # false means my money is in USD, ready to buy coin

symbol_short = 'BTC'
trade_symbol = 'btcusdt'
TRADE_SYMBOL = 'BTCUSD'
#TRADE_QUANTITY = 0.05
SOCKET = "wss://stream.binance.com:9443/ws/" + trade_symbol + "@kline_15m"

RSI_PERIOD = 15
MA_SHORT_PERIOD = 10
MA_LONG_PERIOD = 22
STOCH_PERIOD = 15
UO_PERIOD = 28

was_short_SMA_above = False

client = Client(config.API_KEY, config.API_SECRET, tld='us')
market_data_file = open("market-data-file-" + str(int(time.mktime(datetime.datetime.now().timetuple())*1000)) + ".txt", "w")

def order(side, quantity, symbol, price, order_type=ORDER_TYPE_MARKET):
    try:
        print("Placing order...")
        #order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity, price=price)
        order = client.create_test_order(symbol=symbol, side=side, type=order_type, quantity=quantity, price=price)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    
    return True
    

def on_open(ws):
    print('Socket Connection Established\nAwaiting first message...')

def on_close(ws):
    #market_data_file = open("market-data-file-" + str(int(time.mktime(datetime.datetime.now().timetuple())*1000)) + ".txt", "w")
    market_data_file.write(str(coin_avaliable) + "," + str(USD_avaliable) + "," + str(sells) + "," + str(buys) + "\n")
    #print(str(MA_SHORT_PERIOD) + "," + str(MA_LONG_PERIOD) + "," + (str(coin_avaliable) + "," + str(USD_avaliable) + "," + str(sells) + "," + str(buys) + "\n"))
    #market_data_file.write(str(df))

def on_message(ws, candle):
    global closes, do_i_own_coin, sells, buys, USD_avaliable, coin_avaliable, was_short_SMA_above

    is_candle_closed = True
    close = candle.iloc[-1]['close']

    if is_candle_closed:
        closes.append(1)

        if len(closes) >= RSI_PERIOD:
            temp_RSI = TA.RSI(candle, RSI_PERIOD, 'close', True)
            rsi.append(temp_RSI.iat[-1])

        if len(closes) >= RSI_PERIOD:
            temp_OBV = TA.OBV(candle, 'close')
            obv.append(temp_OBV.iat[-1])

        if len(closes) >= 20:
            temp_bbands = TA.BBANDS(candle, 20, TA.SMA(candle, 20, "close"), "close", 2)
            #print(temp_bbands.iloc[-1])
            temp = [temp_bbands.iloc[-1].BB_LOWER, temp_bbands.iloc[-1].BB_MIDDLE, temp_bbands.iloc[-1].BB_UPPER]
            bbands.append(temp)

                
            # paste the indicator in above this state so that these statements will be inside of it. Changes the true and false
            # values to represent when you would want the bot to buy or sell based on the indicators

            # is the closing price above the middle bbands

            above_mbband = False
            rsi_in_position = False
            obv_in_position = False
            #print(candle.iloc[-1]['close'])
            #print(bbands[-1][1])
            if bbands[-1][1] < candle.iloc[-1]['close']:
                above_mbband = True
            if rsi[-1] > 60:
                rsi_in_position = True
            if obv[-1] > obv[-2] and obv[-1] > obv[-3] and obv[-1] > obv[-4]:
                obv_in_position = True 


            if above_mbband and rsi_in_position and obv_in_position:
                if do_i_own_coin:
                    #buy
                    do_i_own_coin = not do_i_own_coin

                    balance = coin_avaliable * close
                    USD_avaliable = balance
                    USD_avaliable = USD_avaliable * 0.999
                    
                    coin_avaliable = 0
                    buys = buys + 1
                    on_close(6)
                        #print(str(coin_avaliable) + str(USD_avaliable) + str(buys) + str(sells))
            elif not above_mbband and not rsi_in_position and not obv_in_position:
                if not do_i_own_coin:
                    #sell
                    do_i_own_coin = not do_i_own_coin

                    balance = (USD_avaliable * .999) / candle.iloc[-1]['open']
                    coin_avaliable = balance

                    USD_avaliable = 0
                    sells = sells + 1
                    on_close(6)
                    #print(str(coin_avaliable) + str(USD_avaliable) + str(buys) + str(sells))

coin_avaliable = coin_starting
USD_avaliable = USD_starting

# opens a raw data output file
file = open("binance-output-1616948205000.txt", 'r')
raw_data = file.readlines()

# build frame
df = pd.DataFrame([], columns=['TimeStamp', 'open', 'high', 'low', 'close', 'volume'])
#print(df)
for line in raw_data:
    # adds the raw data to dataframe
    candle = line.split("  ")
    candle.pop(0)
    df = df.append({'TimeStamp': float(candle[0]), 'open': float(candle[1]), 'high': float(candle[2]), 'low': float(candle[3]), 'close': float(candle[4]), 'volume': float(candle[5])}, ignore_index=True)    # calls method to calculate the indicators
    on_message(6, df)    # adds each indicator to the dataframe
    #if len(short_MA) > 0:
    #    df.iloc[-1, df.columns.get_loc('7x short SMA')] = short_MA[-1]
    #    if len(long_MA) > 0:
    #        df.iloc[-1, df.columns.get_loc('25x long SMA')] = long_MA[-1]
    #df.iloc[-1, df.columns.get_loc('Coin')] = coin_avaliable
    #df.iloc[-1, df.columns.get_loc('USD')] = USD_avaliable
    #df.iloc[-1, df.columns.get_loc('Buys')] = buys
    #df.iloc[-1, df.columns.get_loc('Sells')] = sells
#print("final: " + str(coin_avaliable) + str(USD_avaliable) + str(buys) + str(sells))
market_data_file.close()

# build frame
#df = pd.DataFrame([], columns=['TimeStamp', 'open', 'High', 'Low', 'close', '7x short SMA', '25x long SMA', 'Coin', 'USD', 'Buys', 'Sells'])
##print(df)
#for line in raw_data:
#    # adds the raw data to dataframe
#    candle = line.split("  ")
#    candle.pop(0)
#    df = df.append({'TimeStamp': float(candle[0]), 'open': float(candle[1]), 'High': float(candle[2]), 'Low': float(candle[3]), 'close': float(candle[4])}, ignore_index=True)    # calls method to calculate the indicators
#    on_message(6, df)    # adds each indicator to the dataframe
#    if len(short_MA) > 0:
#        df.iloc[-1, df.columns.get_loc('7x short SMA')] = short_MA[-1]
#        if len(long_MA) > 0:
#            df.iloc[-1, df.columns.get_loc('25x long SMA')] = long_MA[-1]
#    df.iloc[-1, df.columns.get_loc('Coin')] = coin_avaliable
#    df.iloc[-1, df.columns.get_loc('USD')] = USD_avaliable
#    #df.iloc[-1, df.columns.get_loc('Buys')] = buys
#    #df.iloc[-1, df.columns.get_loc('Sells')] = sells
#on_close(6)


#------------------------------
#while MA_SHORT_PERIOD > 3:
#        MA_LONG_PERIOD = 23
#        while MA_LONG_PERIOD < 28:
#            for line in raw_data:
#                # adds the raw data to dataframe
#                candle = line.split("  ")
#                candle.pop(0)
#                df = df.append({'TimeStamp': float(candle[0]), 'open': float(candle[1]), 'High': float(candle[2]), 'Low': float(candle[3]), 'close': float(candle[4])}, ignore_index=True)
#
#                # calls method to calculate the indicators
#                on_message(6, df)
#
#                # adds each indicator to the dataframe
#                if len(short_MA) > 0:
#                    df.iloc[-1, df.columns.get_loc('7x short SMA')] = short_MA[-1]
#                    if len(long_MA) > 0:
#                        df.iloc[-1, df.columns.get_loc('25x long SMA')] = long_MA[-1]
#                df.iloc[-1, df.columns.get_loc('Coin')] = coin_avaliable
#                df.iloc[-1, df.columns.get_loc('USD')] = USD_avaliable
#                #df.iloc[-1, df.columns.get_loc('Buys')] = buys
#                #df.iloc[-1, df.columns.get_loc('Sells')] = sells
#            on_close(6)
#            do_i_own_coin = True
#            sells = 0 
#            buys = 0
#            coin_avaliable = 0.04834805
#            USD_avaliable = 0
#            MA_LONG_PERIOD = MA_LONG_PERIOD + 1
#        MA_SHORT_PERIOD = MA_SHORT_PERIOD - 1 
#market_data_file.close()