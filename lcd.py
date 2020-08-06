# -*- coding: utf-8 -*-
"""
Created on Fri May 29 01:05:29 2020

@author: Arjan
"""

def lcdPrint(hours, minutes, price, holding, BTC, equity):
    sequence = ""
    if len(str(hours)) == 1:
        sequence += "0"
    sequence += str(hours) + ":"
    if len(str(minutes)) == 1:
        sequence += "0"
    sequence += str(minutes) + "  "
    
    priceDisplay = "$" + str(round(price,2))
    while len(priceDisplay) < 9:
        priceDisplay = " " + priceDisplay
    sequence += priceDisplay
    
    BTCDisplay = str(BTC)
    if "." not in BTCDisplay:
        BTCDisplay = BTCDisplay + "."
    while len(BTCDisplay) < 5:
        BTCDisplay = BTCDisplay + "0"
    sequence += BTCDisplay
    
    if holding == -1:
        sequence += " SHORT "
    if holding == 0:
        sequence += " CASH  "
    if holding == 1:
        sequence += " LONG  "
    
    equityDisplay = str(int(equity))
    
    if len(equityDisplay) < 4:
        equityDisplay = equityDisplay + "%"
    while len(equityDisplay) < 4:
        equityDisplay = " " + equityDisplay
    sequence += equityDisplay
    
    return sequence
    
    