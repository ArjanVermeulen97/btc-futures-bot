# -*- coding: utf-8 -*-
"""
Created on Wed May 27 14:16:51 2020

@author: Arjan
"""

import binance
from binance.client import Client
from auth import key, secret
import math
import time
from datetime import datetime, timedelta
import requests
import json
from notify_run import Notify
import tuning

# Initiate notify and binance clients
notify = Notify()
client = Client(key, secret)

position = client.futures_position_information()[0]
if abs(float(position["positionAmt"])) < 0.001:
    holding = 0
    holdingBTC = 0
    lastbuy = 0
    lastsell = 0
elif float(position['liquidationPrice']) < float(position['entryPrice']):
    holding = 1
    holdingBTC = float(position['positionAmt'])
    lastbuy = float(position['entryPrice'])
    lastsell = 0
else:
    holding = -1
    holdingBTC = float(position['positionAmt'])*-1
    lastbuy = 0
    lastsell = float(position['entryPrice'])
holdingUSDT = float(client.futures_account_balance()[0]["balance"])
equity = holdingUSDT/85.0*100
print(f"Started program at {datetime.today()}")
if holding == 0:
    print("No position")
elif holding == 1:
    print(f"Long {holdingBTC} BTC")
elif holding == -1:
    print(f"Short {holdingBTC} BTC")
print(" ")


short_MA_duration = tuning.short_MA_duration
long_MA_duration = tuning.long_MA_duration
long_enter_s = tuning.long_enter_s
long_exit_s = tuning.long_exit_s
short_enter_s = tuning.short_enter_s
short_exit_s = tuning.short_exit_s
long_enter_l = tuning.long_enter_l
long_exit_l = tuning.long_exit_l
short_enter_l = tuning.short_enter_l
short_exit_l = tuning.short_exit_l
winloss_margin = tuning.winloss_margin
winloss_bias = tuning.winloss_bias
leverage = tuning.leverage

client.futures_change_leverage(symbol="BTCUSDT", leverage=leverage)


startTime = datetime.today()
if startTime.minute > 59:
    next_time = startTime + timedelta(hours=1)
    next_time = next_time.replace(minute=15, second=0, microsecond=0)
elif startTime.minute > 44:
    next_time = startTime + timedelta(hours=1)
    next_time = next_time.replace(minute=0, second=0, microsecond=0)
elif startTime.minute > 29:
    next_time = startTime
    next_time = next_time.replace(minute=45, second=0, microsecond=0)
elif startTime.minute > 14:
    next_time = startTime
    next_time = next_time.replace(minute=30, second=0, microsecond=0)
else:
    next_time = startTime
    next_time = next_time.replace(minute=15, second=0, microsecond=0)

notify.send("Autorun on RPi 4!\nFuturesBot v2.3 - hardware upgrade!")
while True:
    while datetime.today() < next_time:
        time.sleep(5)
    if datetime.today() > next_time:
        holdingUSDT = float(client.futures_account_balance()[0]["balance"])
        if holding != 0:
            PnL = float(client.futures_position_information()[0]["unRealizedProfit"])
            if holding > 0:
                side = "Long " + str(holdingBTC) + " BTC"
            if holding < 0:
                side = "Short " + str(holdingBTC) + " BTC"
        if holding == 0:
            PnL = 0
            side = "No position"
        balance = round(holdingUSDT, 2)
        print(str(next_time) + ", " + str(side) + " \nBalance: " + str(balance) + " USDT")
        if next_time.minute < 10:
            notify.send(str(next_time) + ", " + str(side) + " \nBalance: " + str(balance) + " USDT, Open PnL: " + str(round(PnL, 2)) + " USDT")

        long = False
        short = False
        close_long = False
        close_short = False
        
        jsonklines = requests.get("https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=15m&limit=" + str(long_MA_duration+1))
        
        klines = jsonklines.json()
        pricedata = [float(kline[4]) for kline in klines][::-1]
        
        price = pricedata[0]        
        MA_short = sum(pricedata[0:short_MA_duration])/short_MA_duration
        MA_short_prev = sum(pricedata[1:short_MA_duration+1])/short_MA_duration
        MA_long = sum(pricedata[0:long_MA_duration])/long_MA_duration
        MA_long_prev = sum(pricedata[1:long_MA_duration+1])/long_MA_duration
        
        if MA_short - MA_short_prev > price/long_enter_s and MA_long - MA_long_prev > long_enter_l:
            long = True
        if MA_short - MA_short_prev < price/short_enter_s and MA_long - MA_long_prev < short_enter_l:
            short = True
        if MA_short - MA_short_prev < price/long_exit_s and MA_long - MA_long_prev < long_exit_l:
            if abs(price/lastbuy+winloss_bias) > winloss_margin:
                close_long = True
        if MA_short - MA_short_prev > price/short_exit_s and MA_long - MA_long_prev > -short_exit_l:
            if abs(lastsell/price+winloss_bias) > winloss_margin:
                close_short = True    
        if long and holding == 0:
            holding = 1
            lastbuy = price
            maxbuy = math.floor(holdingUSDT*leverage/price*1000)/1000
            holdingBTC = maxbuy
            client.futures_create_order(symbol="BTCUSDT", side="BUY",
                                        type="MARKET", quantity=maxbuy)
            notify.send("Long " + str(maxbuy) + " BTC at " + str(price))
            print("Long " + str(maxbuy) + " BTC at " + str(price))
        if short and holding == 0:
            holding = -1
            lastsell = price
            maxsell = math.floor(holdingUSDT*leverage/price*1000)/1000
            holdingBTC = maxsell
            client.futures_create_order(symbol="BTCUSDT", side="SELL",
                                        type="MARKET", quantity=maxsell)
            notify.send("Short " + str(maxsell) + " BTC at " + str(price))
            print("Short " + str(maxsell) + " BTC at " + str(price))
        if close_long and holding == 1:
            holding = 0
            diff = ((price/lastbuy)-1)*leverage - fee + 1
            equity = equity*diff
            trade_arr.append((diff-1)*100)
            client.futures_create_order(symbol="BTCUSDT", side="SELL",
                                        type="MARKET", quantity=holdingBTC)
            notify.send("Closed long " + str(holdingBTC) + " BTC at " + str(price) +" \n" +\
                        "This trade: " + str(diff*100) + "%, total: " + str(equity) + "%")
            print("Closed long " + str(holdingBTC) + " BTC at " + str(price) +" \n" +\
                  "This trade: " + str(diff*100) + "%, total: " + str(equity) + "%")
        if close_short and holding == -1:
            holding = 0
            diff = ((lastsell/price)-1)*leverage - fee + 1
            equity = equity*diff
            trade_arr.append((diff-1)*100)
            client.futures_create_order(symbol="BTCUSDT", side="BUY",
                                        type="MARKET", quantity=holdingBTC)
            notify.send("Closed short " + str(holdingBTC) + " BTC at " + str(price) +" \n" +\
                        "This trade: " + str(diff*100) + "%, total: " + str(equity) + "%")
            print("Closed short " + str(holdingBTC) + " BTC at " + str(price) +" \n" +\
                  "This trade: " + str(diff*100) + "%, total: " + str(equity) + "%")
        
        next_time = next_time + timedelta(minutes=15)
        print("Price: " + str(price))
        print("Diff-5: " + str(MA_short - MA_short_prev) + "\nDiff-12: " + str(MA_long - MA_long_prev))
        print(" ")

		
		
