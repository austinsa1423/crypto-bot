import websocket, json, pprint, talib, numpy, time, datetime
import config
from binance.client import Client
from binance.enums import *

#you will need this config file with your own KEY and Secret that are generated in the Binanace website
client = Client(config.API_KEY, config.API_SECRET, tld='us')

# more info on this here https://python-binance.readthedocs.io/en/latest/market_data.html#id7
klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE, "1 day ago UTC")
print(klines)
temp = time.ctime(int(klines[-1][0]/1000))
print(str(time.ctime(int(klines[0][0]/1000))))
print(time.strftime("%m", klines[-1][0]/1000))

klines = str(klines).replace("'", "")
klines = klines.replace(" ", "")
klines = klines.replace("]", "\n")
klines = klines.replace("[", "")
klines = klines.replace(",", "  ")
klines = klines.replace("\n\n", "")

#print(klines)
file = open("historical-binance-data-" + str(int(time.mktime(datetime.datetime.now().timetuple())*1000)) + ".txt", "w")
file.write("  " + str(klines))
file.close()

















# lines up the google trends and twitter data with the appropriate candle and RSI which can be removed
#--------------------------------------------------------------------------
# file = open('tweets.txt', 'r')
# tweets = file.readlines()
# tweet_list = []
# for tweet in tweets:
#     tweet = tweet.split("  ")
#     tweet_list.append([tweet[1],tweet[2]])

# file = open('gt.txt', 'r')
# gts = file.readlines()
# gt_list = []
# for gt in gts:
#     gt = gt.split("  ")
#     temp = [gt[1], gt[2]]
#     gt_list.append(temp)


# #print(gt_list)

# rsi = []
# closes = []
# RSI_PERIOD = 14

# klines = []
# countTweet = -15
# countGt = -8
# klines2.reverse()
# for list in klines2:

#     closes.append(float(list[4]))
#     if len(closes) > RSI_PERIOD:
#         np_closes = numpy.array(closes)
#         temp_rsi = talib.RSI(np_closes, RSI_PERIOD)
#         rsi.append(temp_rsi[-1])

#         temp = [list[0], list[1], list[2], list[3], list[4], tweet_list[countTweet][0], tweet_list[countTweet][1], gt_list[countGt][0], gt_list[countGt][1], temp_rsi[-1]]
#         #temp = [list[1], list[4], tweet_list[countTweet][1], gt_list[countGt][1], temp_rsi[-1]]
#         print(temp)
#         klines.append(temp)
#         countTweet = countTweet - 1
#         countGt = countGt - 1

# klines.reverse()