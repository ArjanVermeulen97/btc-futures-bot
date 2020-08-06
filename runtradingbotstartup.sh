#!/bin/bash
sleep 20
chronyd -q 'server 185.255.55.20 iburst'
while true; do
  sleep 10
  nohup python /home/alarm/tradingbot/bot.py >> /home/alarm/tradingbot/bot.log
  chronyd -q 'server 185.255.55.20 iburst'
done &
