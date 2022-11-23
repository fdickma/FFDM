#
# Free Financial Data Management - FFDM/OSS.
# 
# Frank Dickmann, Germany, 2020.07.20
# 
# Version 1.0
#

import sys
import psutil
import argparse
import os
import subprocess
import re
import glob
import numpy as np
import pandas as pd
import configparser
import csv
import datetime
import time
import sqlite3

# Import FFDM function library
import ffdm_lib as fl

# Define main variables as global
global Directory

# Set default variables including database parameters
myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
config = configparser.ConfigParser()
config.sections()
config.read(myDir + 'ffdm.ini')
DB=config['DB']['DB']
DefaultCurrency=config['Accounts']['DefaultCurrency']
fl.DefaultCurrency=config['Accounts']['DefaultCurrency']
dataDir=config['Accounts']['Dir']
mailAddr=config['Server']['Mail']
Directory = []
if config['Accounts']['dat1'] != '':
    Directory.append(config['Accounts']['dat1'])
if config['Accounts']['dat2'] != '':
    Directory.append(config['Accounts']['dat2'])
if config['Accounts']['dat3'] != '':
    Directory.append(config['Accounts']['dat3'])
if config['Accounts']['dat4'] != '':
    Directory.append(config['Accounts']['dat4'])
if config['Accounts']['dat5'] != '':
    Directory.append(config['Accounts']['dat5'])

def createLock():
    f = open(LockFile, 'w')
    f.write("")
    f.close()    

def deleteLock():
    if os.path.exists(LockFile):
        os.remove(LockFile)

def checkLock():
    if os.path.exists(LockFile):
        print("Locked!")
        return True
    else:
        return False
        
# Return the number of months between two dates
def months(d1, d2):
    return d1.month - d2.month + 12 * (d1.year - d2.year)

# Read the assets references
def readAssetRef():
    AssetData = []
    connection = sqlite3.connect(myDir + DB)
    assetrefDF = pd.DataFrame(connection.execute("SELECT AssetID, AssetType,\
            AssetName, BankRef, NetRef1, NetRef2 FROM AssetReferences").fetchall(), \
            columns=["AssetID","AssetType","AssetName","BankRef","NetRef1","NetRef2"])
    connection.close()
    return assetrefDF

# Links for finanzen.net
def get_Fnet_data(a_type, a_id, refFnet):
    link = ""
    if a_type == "STK":
        link = "https://www.finanzen.net/aktien/" + refFnet + "-Aktie" \
                +" | grep -m 1 '[0-9] EUR' | grep -o [0-9.,]*"
    if a_type == "ETF":
        link = "https://www.finanzen.net/etf/" + refFnet + "-" + a_id \
                +" | grep -m 1 '[0-9] EUR' | grep -o [0-9.,]*"
    if a_type == "FND":
        link = "https://www.finanzen.net/fonds/" + refFnet + "-" + a_id \
                +" | grep -m 1 '[0-9] EUR' | grep -o [0-9.,]*"
    if a_type == "COM" and a_id == "Gold":
        link = "https://www.finanzen.net/rohstoffe/goldpreis" \
                +" | egrep -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]{0,3}\.)?"\
                +"[[:digit:]]{1,3}\,[[:digit:]]{2}\EUR' | " \
                +"grep -o [0-9.,]*"
    if a_type == "CUR" and a_id == "USD":
        link = "https://www.finanzen.net/devisen/realtimekurs/dollarkurs" \
                +" | grep -m 1 '^[0-3].*USD' | cut -c 1-6"
    if a_type == "CUR" and a_id == "BTC":
        link = "https://www.finanzen.net/devisen/realtimekurs/" \
                +"bitcoin-euro-kurs | grep -m 2 '[0-9].*EUR' | " \
                +"grep -o ^[0-9.,]*" 
    if link != "":
        return link
    else:
        return 0
        
# Links for ard-Boerse
def get_ARD_data(a_type, a_id, refARD):
    link = "https://www.tagesschau.de/wirtschaft/boersenkurse/"\
            +"suche/?suchbegriff="
    extract = ""
    if a_type == "COM":
        extract = " | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{2}' | grep -o [0-9.,]*$"
    if a_type == "CUR" and a_id == "USD":
        extract = " | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{4}' | grep -o [0-9.,]*$"
    if a_type == "CUR" and a_id == "BTC":
        extract = " | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{2}' | grep -o [0-9.,]*$"
    if a_type == "FND" or a_type == "ETF" or a_type == "STK":
        extract = " | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{2}' | grep -o [0-9.,]*$"
    if extract != "":
        return link + refARD + extract
    else:
        return 0

def retrieveWebData(link):
    Browser = "w3m -no-cookie -dump "
    if link != 0:
        proc = subprocess.Popen(Browser + link, shell=True, text=True,\
                                stdout=subprocess.PIPE)
        try:
            outs, errs = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
        if outs == None:
            return 0
        clean = outs.replace('.', '').replace(',', '.').rstrip('\n')
        clean = clean.lstrip()
        p1 = re.compile(r'[A-Z]|[a-z]([\d]+\.\d{2})')
        m1 = p1.match(clean)
        if m1:
            return m1.group(1)
        p2 = re.compile(r'([\d]+\.\d{2,4})')
        m2 = p2.match(clean)
        if m2:
            return fl.check_float(m2.group(1))
    return -1

# Retrieve asset prices
def assetDataScraping(asset):
    return_price=-1
    a_type = asset['AssetType']
    a_id = asset['AssetID']
    refFnet = asset['NetRef1']
    refARD = asset['NetRef2']
    #return_price = retrieveWebData(get_Fnet_data(a_type, a_id, refFnet))
    return_price = retrieveWebData(get_ARD_data(a_type, a_id, refARD))
    if return_price <= 0:
        #return_price = retrieveWebData(get_ARD_data(a_type, a_id, refARD))
        return_price = retrieveWebData(get_Fnet_data(a_type, a_id, refFnet))
        #print(return_price)
    return return_price

# Get filesystem information for a file
def getFileTimestamp(File):
    ftime = os.popen("ls -la "+File).read()
    ftime = ftime.replace("\n",'')
    return ftime

# Return a list of all files to operate on
def getFileList():
    fList = []
    for sdir in Directory:
        tmpPath = dataDir + sdir + "/*.[cC][sS][vV]"
        tmpFiles = list(glob.glob(tmpPath))
        for f in tmpFiles:
            fRec = f + getFileTimestamp(f)
            fList.append(fRec)
    for sfile in list(glob.glob(myDir + 'initdata/*.[cC][sS][vV]')):
        fRec = getFileTimestamp(sfile)
        fList.append(fRec)
    return fList

# Read the file with the last time generated filesystem data for all files
def readFileChk():
    Files = []
    try:
        f = open(TempDir + 'ffdm_files.chk', 'r')
        for chk in f:
            Files.append(chk)
        f.close()
    except:
        Files = []
    return Files

# Write the file with the generated filesystem data for all files
def writeFileChk(Files):
    f = open(TempDir + 'ffdm_files.chk', 'w')
    for chk in Files:
        f.write(chk+"\n")
    f.close()
    
# Generate a hash for a list of strings
def hashList(List):
    Complete = ""
    for l in List:
        Complete = Complete + l.replace("\n",'')
    return hash(Complete)
    
def assetsUpdate():
    assetrefDF = readAssetRef()
    #targetlist = readAssetFile(TargetFile)
    print(myDir+'initdata/AssetPrices.csv')
    priceDF = pd.read_csv(myDir+'initdata/AssetPrices.csv', header=0, sep=";")
    
    i = 0
    for idx, asset in assetrefDF.iterrows():
        price = assetDataScraping(asset)
        if price > 0:
            i = i + 1
            print(i, asset['AssetName'], now_str, price)
            asset_prices = [asset['AssetID'], now_str+'.000', price, DefaultCurrency]
            df_length = len(priceDF)
            priceDF.loc[df_length] = asset_prices
        else:
            print('Failed: ', asset['AssetName'])
    priceDF.to_csv(myDir+'initdata/AssetPrices.csv', header=True, sep=";", index=False)
    return

# Retrieve current stock values from several sources
def sendEmail(a_name, a_price, target, text):
    if os.path.exists('/usr/bin/mail'):
        os.popen("echo \"" + a_name + " : " + str(a_price) + " is " + text + "\""
                +"| mail -s '"+ a_name +" is " + text + ": " \
                + str(a_price) +"' " \
                +mailAddr)
    else:
        print(a_name + " : " + str(a_price) + " is " + text)

def targetTest():
    targetDF = []
    connection = sqlite3.connect(myDir + DB)
    targetDF = pd.DataFrame(connection.execute("SELECT AssetID, TargetPriceLow,\
            TargetPriceHigh, Currency FROM TargetPrices").fetchall(), \
            columns=["AssetID","TargetPriceLow","TargetPriceHigh","Currency"])
    assetpriceDF = pd.DataFrame(connection.execute("SELECT AssetID,\
            LastPrice, AssetName FROM qWatchlist").fetchall(), \
            columns=["AssetID","LastPrice","AssetName"])
    connection.close()
    
    for idx, tgt in targetDF.iterrows():
        if len(assetpriceDF['AssetID'][(assetpriceDF['AssetID']==tgt['AssetID'])]) > 0:
            aprice = (assetpriceDF[['AssetID','LastPrice']]\
                    [(assetpriceDF['AssetID']==tgt['AssetID'])]['LastPrice']).iloc[0]
            aname = (assetpriceDF[['AssetID','AssetName']]\
                    [(assetpriceDF['AssetID']==tgt['AssetID'])]['AssetName']).iloc[0]
            if tgt['TargetPriceLow'] != 0 and tgt['TargetPriceHigh'] != 0:
                if (aprice < tgt['TargetPriceLow']):
                    sendEmail(aname, fl.format_number(aprice), \
                        tgt['TargetPriceLow'], "low")
                elif (aprice > tgt['TargetPriceHigh']):
                    sendEmail(aname, fl.format_number(aprice), \
                        tgt['TargetPriceHigh'], "high")
                else:
                    print(aname, ': check ok')
        else:
            print(tgt['AssetID'])
    return

def accountsUpdate():
    print('Re-initilize data')
    subprocess.run(["python3 " + myDir + "init_db.py"], shell=True, check=True)

if __name__ == '__main__':
    
    TempDir = os.path.dirname(os.path.realpath(__file__)) + "/"
    LockFile = TempDir + 'ffdm.lock'

    # Check if the script is already running, this instance adds
    # one instance. Therefore, check for more than one instance.
    ps_i = 0
    for process in psutil.process_iter():
        prc = process.cmdline()
        if len(prc) > 0:
            if 'python3' in prc[0] and 'ffdm.py' in prc[1]:
                ps_i = ps_i + 1
    
    # Careful, but not to be too restrictive
    if ps_i > 3:
        print("Already running")
        sys.exit()
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t', '--test', help='Dry run', action='store_true')
    parser.add_argument(
        '-w', '--web', help='Get web data', action='store_true')
    parser.add_argument(
        '-l', '--lock', help='Set lock file', action='store_true')
    parser.add_argument(
        '-u', '--unlock', help='Delete lock file', action='store_true')
    parser.add_argument(
        '-f', '--force', help='Force accounts update', action='store_true')
    parser.add_argument(
        '-a', '--all', help='Force all data update', action='store_true')
    parser.add_argument(
        '-g', '--target', help='Check target prices', action='store_true')
    args = parser.parse_args()

    now = datetime.datetime.now()
    now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        
    if args.test:
        if checkLock(): sys.exit()
        print('Test run only.')
        sys.exit(0)

    if args.lock:
        if checkLock(): sys.exit()
        print('Set lock file.')
        createLock()
        sys.exit(0)

    if args.target:
        if checkLock(): sys.exit()
        createLock()
        print('Checking target prices.')
        targetTest()
        deleteLock()
        sys.exit(0)

    if args.all:
        if checkLock(): sys.exit()
        createLock()
        print('Updating all data.')
        assetsUpdate()
        accountsUpdate()
        deleteLock()
        sys.exit(0)

    if args.web:
        if checkLock(): sys.exit()
        createLock()
        print('Updating web data.')
        assetsUpdate()
        accountsUpdate()
        targetTest()
        deleteLock()
        sys.exit(0)

    if args.force:
        if checkLock(): sys.exit()
        createLock()
        print('Force update without updating prices.')
        accountsUpdate()
        deleteLock()
        sys.exit(0)

    if args.unlock:
        print('Delete lock file.')
        deleteLock()
        sys.exit(0)
        
    oldFileList = readFileChk()
    FileList = getFileList()
    
    if hashList(FileList) == hashList(oldFileList):
        print("No new data found to update.")
    else:
        print("New data found to update")
        if checkLock(): sys.exit()
        createLock()
        accountsUpdate()
        writeFileChk(FileList)
        deleteLock()
      