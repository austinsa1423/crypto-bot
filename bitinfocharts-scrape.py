import requests 
from bs4 import BeautifulSoup
import pandas as pd
import re

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', -1)

def parse_strlist(sl):
    clean = re.sub("[\[\],\s]","",sl)
    splitted = re.split("[\'\"]",clean)
    values_only = [s for s in splitted if s != '']
    return values_only

# cahnge the url to pull different data, make sure to change the file name below too
# url = 'https://bitinfocharts.com/comparison/google_trends-btc.html'
url = 'https://bitinfocharts.com/comparison/google_trends-btc.html'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
scripts = soup.find_all('script')
for script in scripts:
    if '''d = new Dygraph(document.getElementById("container")''' in script.next:
        StrList = script.next
        StrList = '[[' + StrList.split('[[')[-1]
        StrList = StrList.split(']]')[0] +']]'
        StrList = StrList.replace("new Date(", '').replace(')','')
        dataList = parse_strlist(StrList)

date = []
tweet = []
for each in dataList:
    if (dataList.index(each) % 2) == 0:
        date.append(each)
    else:
        tweet.append(each)



#print(str(pd.DataFrame(list(zip(date, tweet)), columns=["Date","Decred - Tweets"])))

# change this file name 
file = open("google_trend.txt", 'w')
file.write(str(pd.DataFrame(list(zip(date, tweet)), columns=["Date","Decred - Tweets"])))
#file.write(str(df))
file.close()