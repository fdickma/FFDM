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
import subprocess
import os
import glob
import numpy as np
import pandas as pd
import configparser
import csv
import datetime
import time
import smtplib
import __main__

# Import FFDM function library
import ffdm_lib as fl
import ffdm_scrape as scrape
scrape.refAvailable = []

# Define main variables as global
global Directory

# Set default variables including database parameters
baseDir = os.path.abspath(os.path.dirname(__file__)) + '/'
config = configparser.ConfigParser()
config.sections()
config.read(baseDir + 'ffdm.ini')
DB=config['DB']['DB']
DefaultCurrency=config['Accounts']['DefaultCurrency']
fl.DefaultCurrency=config['Accounts']['DefaultCurrency']
dataDir=config['Accounts']['Dir']
mailAddr=config['Server']['Mail']
mailPwd=config['Server']['MailPwd']
mailServ=config['Server']['MailServ']
Directory = []

# Iterating account directory entries
dir_count = 0
for cdir in config['Accounts']:
    print(cdir)
    if cdir[:3] == "dat":
        dir_count += 1
        if config['Accounts']['dat' + str(dir_count)] != "":
            Directory.append(config['Accounts']['dat' + str(dir_count)])    

# Finally retrieve a list of all users
userlist = []
userlist = fl.get_user_db('SELECT username FROM users')

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
def readAssetRef(user_id):
    myDir = baseDir + 'users/' + user_id + '/'
    AssetData = []
    assetrefDF = pd.DataFrame(fl.get_db_data("SELECT AssetID, AssetType,\
            AssetName, Ticker, NetRef1, NetRef2 FROM AssetReferences", user_id), \
            columns=["AssetID","AssetType","AssetName","Ticker","NetRef1","NetRef2"])
    return assetrefDF

# Get filesystem information for a file
def getFileTimestamp(File):
    ftime = os.popen("ls -la "+File).read()
    ftime = ftime.replace("\n",'')
    return ftime

# Return a list of all files to operate on
def getFileList():
    fList = []

    for user_id in userlist:
        if type(user_id) != str:
            u_id = str(user_id[0])
        else:
            u_id = user_id
        print('Directory for:', u_id)

        myDir = baseDir + 'users/' + u_id + '/'
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
    scrape.check_online()

    if (scrape.refAvailable[0] == False) and (scrape.refAvailable[1] == False) \
        and (scrape.refAvailable[2] == False):
        print("No online services available...")
        return
    
    for user_id in userlist:
        if type(user_id) != str:
            u_id = str(user_id[0])
        else:
            u_id = user_id
        print('Update assets data for:', u_id)

        myDir = baseDir + 'users/' + u_id + '/'
        assetrefDF = readAssetRef(u_id)
        print(myDir+'initdata/AssetPrices.csv')
        priceDF = pd.read_csv(myDir+'initdata/AssetPrices.csv', header=0, sep=";")

        i = 0
        for idx, asset in assetrefDF.iterrows():
            if (priceDF['AssetID'] == asset['AssetID']).any():
                old_price = priceDF.set_index('AssetPrice')['AssetID']\
                    .eq(asset['AssetID'])[::-1].idxmax()
            else:
                old_price = 0
            price = scrape.assetDataScraping(asset, old_price)
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

# Check function to test if the mail server is alive in general
def checkMailserver():
    print("Checking mail server...")
    smtpServer=mailServ
    try:
        server = smtplib.SMTP(smtpServer, port=587, timeout=1)
        server.quit()
    except:
        print("Mail server not working!")
        return False
    return True

# Retrieve current stock values from several sources
def sendEmail(a_name, a_price, target, text):
    smtpServer=mailServ
    fromAddr=mailAddr
    toAddr=mailAddr
    msg= "Subject: " + \
        a_name +" is " + text + ": " + str(a_price) + "\n\n" + \
        a_name + " : " + str(a_price) + " is " + text
    try:
        server = smtplib.SMTP(smtpServer, port=587, timeout=1)
        server.ehlo()
        server.starttls()
        server.login(mailAddr, mailPwd)
        server.sendmail(fromAddr, toAddr, msg)
        server.quit()
    except:
        print("Mail server not working!")
    print(a_name + " : " + str(a_price) + " is " + text)

def targetTest():
    
    # In case the mail server is not reachable don't continue
    if checkMailserver() != True:
        return

    for user_id in userlist:
        if type(user_id) != str:
            u_id = str(user_id[0])
        else:
            u_id = user_id
        print('Targets for:', u_id)

        targetDF = []
        targetDF = pd.DataFrame(fl.get_db_data("SELECT AssetID, TargetPriceLow,\
                TargetPriceHigh, Currency FROM TargetPrices", u_id), \
                columns=["AssetID","TargetPriceLow","TargetPriceHigh","Currency"])
        assetpriceDF = pd.DataFrame(fl.get_db_data("SELECT AssetID,\
                LastPrice, AssetName FROM qWatchlist", u_id), \
                columns=["AssetID","LastPrice","AssetName"])

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
    for user_id in userlist:
        if type(user_id) != str:
            u_id = str(user_id[0])
        else:
            u_id = user_id
        print('Re-initilize data for:', u_id)
        fl.get_currencies()
        subprocess.run(["python3 " + baseDir + "init_db.py " + u_id], shell=True, check=True)

def tickerDataUpdate():
    for user_id in userlist:
        if type(user_id) != str:
            u_id = str(user_id[0])
        else:
            u_id = user_id
        print('Re-initilize data for:', u_id)
        assetDF = fl.get_assets(u_id)
        for a in assetDF.AssetID:
            if assetDF[(assetDF['AssetID'] == a)]['AssetType'].iloc[0] != 'CUR':
                ticker = assetDF[(assetDF['AssetID'] == a)]['Ticker'].iloc[0]
                print(a, ticker)
                fl.dl_ticker_data(a, ticker, 5)

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
        '-d', '--tdu', help='Update ticker data', action='store_true')
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
    
    # The last parameter is the username
    parser.add_argument('rest', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    now = datetime.datetime.now()
    now_str = time.strftime('%Y-%m-%d %H:%M:%S')

    # In case a username is given check it against the userlist
    # If the username exists append it to an empty userlist as the single 
    # username to be processed
    if args.rest:
        if userlist != None:
            if fl.in_list(args.rest, userlist):
                userlist = []
                userlist.append(args.rest)
        else:
            print("Username does not exist.")
            exit()

    print(userlist)

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

    if args.tdu:
        if checkLock(): sys.exit()
        createLock()
        print('Update ticker data.')
        tickerDataUpdate()
        accountsUpdate()
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
      