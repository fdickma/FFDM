import sqlite3
import io
import os
import glob
import sys
import datetime
import multiprocessing as mp
import time
import locale
import pandas as pd
import numpy as np
import configparser
import csv
import re
from datetime import date, timedelta
import __main__

# Import FFDM function library
import ffdm_lib as fl

def entriesToDB(account_entries, depot_entries):
    
    if len(account_entries) > 1:
        tableName = "Accounts"
        tableData = pd.DataFrame(account_entries[1:],columns=account_entries[0])
        tableData.to_sql(tableName, con=connection, if_exists='append', index=False)     

    if len(depot_entries) > 1:
        tableName = "Depots"
        tableData = pd.DataFrame(depot_entries[1:],columns=depot_entries[0])
        tableData.to_sql(tableName, con=connection, if_exists='append', index=False)     
    return

def filterDF(Expression):
    return accountDF[accountDF['Reference'].str.contains(Expression, na=0,\
        flags=re.IGNORECASE, regex=True)]\
        .groupby(accountDF['EntryDate'].dt.to_period('Y'))['Amount'].sum()

def countFilterDF(Expression):
    return accountDF[accountDF['Reference'].str.contains(Expression, na=0, \
        flags=re.IGNORECASE, regex=True)]\
        .groupby(accountDF['EntryDate'].dt.to_period('M'))['Amount']\
        .size().resample('Y').size()

def getMonths(years):
    curmonth = datetime.datetime.now().strftime("%m")
    curyear = datetime.datetime.now().strftime("%Y")
    ymonth = []
    for y in years:
        if y < curyear:
            ymonth.append(12)
        else:
            ymonth.append(int(curmonth))
    return ymonth

def watchlist_asset(assets, proc_num):
    watchlistDF = pd.DataFrame()
    for a in assets:
        print("Process: {0:<2}  /  Asset: {1:12}".format(proc_num, a))
        recalc = False
        try:
            pricetime = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                        [(__main__.assetpriceDF['AssetID']==a)]["PriceTime"].max())
            lastprice = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                        [(__main__.assetpriceDF['PriceTime']==pricetime) \
                        & (__main__.assetpriceDF['AssetID']==a)]['AssetPrice'].iloc[0])
            if lastprice == None:
                lastprice = 0
            pricetime = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                        [(__main__.assetpriceDF['AssetID']==a)]["PriceTime"].max())
            pricetimesDF = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                        [(__main__.assetpriceDF['AssetID']==a)])
            
            amaxpriceDF = pricetimesDF.loc[pricetimesDF.groupby(pricetimesDF['PriceTime']\
                       .dt.normalize())['PriceTime'].idxmax().values]
            amaxpriceDF = amaxpriceDF.reset_index()

            prevpricetime = amaxpriceDF['PriceTime'].iloc[(len(amaxpriceDF['PriceTime'])-2)]

            prevprice = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                        [(__main__.assetpriceDF['PriceTime']==prevpricetime) \
                        & (__main__.assetpriceDF['AssetID']==a)]['AssetPrice'].iloc[0])
            if (prevprice == None) or (prevprice == 0):
                prevprice = lastprice
            aname = (__main__.assetrefDF[['AssetID','AssetName']]\
                        [(__main__.assetrefDF['AssetID']==a)]['AssetName'].iloc[0])
        except:
            print(a," not finished 1")
            continue
        if len(__main__.oldwlist) > 0:
            try:
                lastprice_o = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['LastPrice']).iloc[0]
            except:
                lastprice_o = 0
            try:
                prevprice_o = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['PrevPrice']).iloc[0]
            except:
                prevprice_o = 0
            if prevprice == prevprice_o and lastprice == lastprice_o:
                delta = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['Delta']).iloc[0]
                deltaprice = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['DeltaPrice']).iloc[0]
                price20av = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['Avg20Price']).iloc[0]
                price200av = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['Avg200Price']).iloc[0]
                lowtarget = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['TargetLow']).iloc[0]
                hightarget = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['TargetHigh']).iloc[0]
                minprice = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['MinPrice']).iloc[0]
                maxprice = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['MaxPrice']).iloc[0]
                lowprice = (__main__.oldwlist[(__main__.oldwlist['AssetID']==a)]\
                    ['LowPrice']).iloc[0]
                if lastprice < minprice: minprice = lastprice
                if lastprice < lowprice: lowprice = lastprice
                if lastprice > maxprice: maxprice = lastprice
            else:
                recalc = True

        if len(__main__.oldwlist) == 0 or recalc == True:
            try:
                price20av = round((__main__.assetpriceDF[['PriceTime','AssetID',\
                            'AssetPrice']]\
                            [(__main__.assetpriceDF['PriceTime']>__main__.price20time) \
                            & (__main__.assetpriceDF['AssetID']==a)]['AssetPrice'])\
                            .values.mean(),4)
                price200av = round((__main__.assetpriceDF[['PriceTime','AssetID',\
                            'AssetPrice']]\
                            [(__main__.assetpriceDF['PriceTime']>__main__.price200time) \
                            & (__main__.assetpriceDF['AssetID']==a)]['AssetPrice'])\
                            .values.mean(),4)
                maxprice = round((__main__.assetpriceDF[['PriceTime','AssetID',\
                            'AssetPrice']]\
                            [(__main__.assetpriceDF['AssetID']==a)]['AssetPrice'])\
                            .values.max(),4)
                maxdate = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                            [(__main__.assetpriceDF['AssetPrice']==maxprice) \
                            & (__main__.assetpriceDF['AssetID']==a)]['PriceTime']).iloc[0]
                lowprice = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                    [(__main__.assetpriceDF['AssetID']==a)]['AssetPrice']).values.min()
                if maxdate < __main__.pricetime:
                    minprice = round((__main__.assetpriceDF[['PriceTime','AssetID',\
                                'AssetPrice']]\
                                [(__main__.assetpriceDF['PriceTime']>maxdate) & \
                                (__main__.assetpriceDF['AssetID']==a)]['AssetPrice'])\
                                .values.min(),4)
                else:
                    minprice = maxprice
                try:
                    lowtarget = (__main__.targetpriceDF[['AssetID','TargetPriceLow']]\
                                [(__main__.targetpriceDF['AssetID']==a)]\
                                ['TargetPriceLow']).iloc[0]
                except:
                    lowtarget = 0
                try:
                    hightarget = (__main__.targetpriceDF[['AssetID','TargetPriceHigh']]\
                                [(__main__.targetpriceDF['AssetID']==a)]\
                                ['TargetPriceHigh']).iloc[0]
                except:
                    hightarget = 0
                deltaprice = round(lastprice - prevprice, 2)
                delta = round((lastprice / price20av * 100) - 100, 2)
            except:
                print(a," not finished 2")
                continue
        
        # Adding Fibonacci retracements and the underlaying trend
        r_618 = 0
        e_382 = 0
        trend = 0
        # Check if upward trend
        if minprice < lowprice:
            r_618 = round(maxprice - ((maxprice - minprice) * 0.618),4)
            e_382 = round(maxprice + ((maxprice - minprice) * 0.382),4)
            trend = 1            
        # Check if downward trend
        if minprice >= lowprice:
            r_618 = round(minprice + ((maxprice - minprice) * 0.618),4)
            e_382 = round(minprice - ((maxprice - minprice) * 0.382),4)
            trend = -1
            
        watchlist = pd.Series([a,aname,delta,deltaprice,lastprice,prevprice,\
                    price20av,price200av,lowtarget,hightarget,minprice,maxprice,\
                    lowprice,r_618,e_382,trend])
        watchlistDF = pd.concat([watchlistDF, watchlist.to_frame().T], axis = 0, \
                    ignore_index=True)

    return watchlistDF

if __name__ == '__main__':
    # Get the start time
    start_time = time.time()

    cores = os.cpu_count()

    myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    config = configparser.ConfigParser()
    config.sections()
    config.read(myDir + 'ffdm.ini')
    DB=config['DB']['DB']
    DefaultCurrency=config['Accounts']['DefaultCurrency']
    fl.DefaultCurrency=config['Accounts']['DefaultCurrency']
    filterList=[]
    filterList.append(['Income', config['Filter']['Income']])
    filterList.append(['Dividend', config['Filter']['Dividends']])
    filterList.append(['Interest', config['Filter']['Interest']])
    filterList.append(['Rent', config['Filter']['Rent']])
    filterList.append(['Stock', config['Filter']['Stock']])
    filterList.append(['Metal', config['Filter']['NobleMetal']])
    filterList.append(['Sales', config['Filter']['Sales']])
    spendList=[]
    spendList.append(['Cash','AUSZAHLUNG.|GELDAUTOMAT'])
    spendList.append(['Card','KARTENZAHLUNG'])
    spendList.append(['Amazon','EREF.*AMAZON'])
    dataDir=config['Accounts']['Dir']
    accountDir = []
    if config['Accounts']['dat1'] != '':
        accountDir.append(config['Accounts']['dat1'])
    if config['Accounts']['dat2'] != '':
        accountDir.append(config['Accounts']['dat2'])
    if config['Accounts']['dat3'] != '':
        accountDir.append(config['Accounts']['dat3'])
    if config['Accounts']['dat4'] != '':
        accountDir.append(config['Accounts']['dat4'])
    if config['Accounts']['dat5'] != '':
        accountDir.append(config['Accounts']['dat5'])

    connection = sqlite3.connect(myDir + DB)

    with open(myDir + 'init_schema.sql') as f:
        connection.executescript(f.read())

    cur = connection.cursor()

    files_list = list(glob.glob(myDir+"initdata/*.[cC][sS][vV]"))

    print('Import: Accounts and Depots')
    for sdir in accountDir:
        files_list.extend(list(glob.glob(dataDir + sdir + "/*.[cC][sS][vV]")))
    account_entries = []
    depot_entries = []
    for f in files_list:
        print("File: "+f)
        account_entries, depot_entries = fl.readStatement(f)
        if (len(account_entries)<2 and len(depot_entries)<2):
            tableName = (os.path.splitext(os.path.split(f)[-1])[0])
            tableData = pd.read_csv(f, header=0, sep=";")
            tableData.to_sql(tableName, con=connection, if_exists='append', index=False)
        else:
            entriesToDB(account_entries, depot_entries)

    account_entries, depot_entries = fl.get_vl_plans(connection)
    entriesToDB(account_entries, depot_entries)

    accountDF = pd.DataFrame(connection.execute("SELECT Bank,AccountNr,EntryDate,\
                Reference,Amount,Currency FROM Accounts").fetchall(), \
                columns=["Bank","AccountNr","EntryDate","Reference","Amount","Currency"])

    accountBalanceDF = accountDF.groupby(['Bank','AccountNr'])['Amount'].sum()\
                        .reset_index()
    accountBalanceDF = accountBalanceDF.round(2)
    accountBalanceDF.to_sql("qAccountBalances", con=connection, if_exists='replace', \
                            index=False)

    accountDF = pd.DataFrame(connection.execute("SELECT Bank,AccountNr,EntryDate,\
                Reference,Amount,Currency FROM Accounts").fetchall(), \
                columns=["Bank","AccountNr","EntryDate","Reference","Amount","Currency"])

    accountDF['EntryDate'] = pd.to_datetime(accountDF['EntryDate'])

    # Initialize the separate index for the years with data
    tmpDF = pd.DataFrame()
    tmpDF['Year'] = accountDF.groupby(accountDF['EntryDate']\
                        .dt.to_period('Y'))['Amount'].sum()
    tmpDF['Year'] = tmpDF.index.copy().astype(str)

    # Generate yearly dataframe
    print('Generate: Yearly Data')
    yearDF = pd.DataFrame()
    yearDF['Year'] = tmpDF['Year']

    yearDF['Cashflow'] = accountDF.groupby(accountDF['EntryDate']\
                        .dt.to_period('Y'))['Amount'].sum()

    for filterLine in filterList:
        yearDF[filterLine[0]] = filterDF(filterLine[1])
    yearDF = yearDF.fillna(0)

    yearDF['TotalIncome'] = yearDF['Income'] + yearDF['Dividend'] + yearDF['Interest'] \
                            + yearDF['Rent'] + yearDF['Sales']
    yearDF['Invest'] = (yearDF['Stock'] * (-1)) + (yearDF['Metal'] * (-1))
    yearDF['Saving'] = yearDF['Cashflow'] + yearDF['Invest']
    yearDF['Spending'] = yearDF['TotalIncome'] - yearDF['Saving']
    yearDF['SavingRate'] = yearDF['Saving'] / yearDF['TotalIncome'] * 100
    yearDF['PayMonths'] = countFilterDF(filterList[0][1])
    yearDF['Months'] = getMonths(yearDF['Year'])
    yearDF.to_sql('qYearly', con=connection, if_exists='replace', index=False)

    # Generate yearly cumulative dataframe
    print('Generate: Yearly Cumulative')
    cumyearDF = pd.DataFrame()
    cumyearDF = yearDF.cumsum()
    cumyearDF['Year'] = yearDF['Year']
    cumyearDF.to_sql('qCumulative', con=connection, if_exists='replace', index=False)

    # Generate monthly average dataframe
    print('Generate: Monthly Data')
    monthDF = pd.DataFrame()
    monthDF['Year'] = tmpDF['Year']
    monthDF['Income'] = yearDF['TotalIncome'] / yearDF['PayMonths']
    monthDF['Spend'] = yearDF['Spending'] / yearDF['Months']
    monthDF['Invest'] = yearDF['Invest'] / yearDF['PayMonths']
    monthDF['Saving'] = yearDF['Saving'] / yearDF['PayMonths']
    monthDF=monthDF.round(2)
    monthDF.to_sql('qMonthly', con=connection, if_exists='replace', index=False)

    # Generate quarterly cashflow dataframe
    print('Generate: Quarterly Cashflow')
    quarterDF = pd.DataFrame()
    quarterDF['Cashflow'] = accountDF.groupby(accountDF['EntryDate']\
                .dt.to_period('Q'))['Amount'].sum()
    quarterDF['Quarter'] = quarterDF.index.astype(str).str.\
                            replace(r'(\d+)Q(\d)', r'\1-Q\2', regex=True)
    quarterDF = quarterDF.round(2)
    quarterDF.to_sql('qQuarterly', con=connection, if_exists='replace', index=False)

    # Generate spending dataframe
    print('Generate: Spending')
    spendDF = pd.DataFrame()
    spendDF['Year'] = tmpDF['Year']
    for spendLine in spendList:
        spendDF[spendLine[0]] = filterDF(spendLine[1])
    spendDF['Total'] = spendDF.sum(axis=1, numeric_only=True)
    spendDF = spendDF.fillna(0)
    spendDF.to_sql('qSpending', con=connection, if_exists='replace', index=False)

    # Generate depot dataframes
    print('Generate: Depots')
    depotDF = pd.DataFrame(connection.execute("SELECT Bank,DepotNr,AssetID,\
                BankRef, AssetAmount, AssetBuyPrice, Currency FROM Depots").fetchall(), \
                columns=["Bank","DepotNr","AssetID","BankRef","AssetAmount",\
                "AssetBuyPrice","Currency"])
    # Gold grams to ounce
    depotDF['AssetAmount'] = np.where(depotDF['AssetID'] == 'Gold',
                                            depotDF['AssetAmount'] / 31.1034768,
                                            depotDF['AssetAmount'])

    assetrefDF = pd.DataFrame(connection.execute("SELECT AssetID, AssetType,\
                AssetName, BankRef, NetRef1, NetRef2 FROM AssetReferences").fetchall(), \
                columns=["AssetID","AssetType","AssetName","BankRef","NetRef1","NetRef2"])

    assetpriceDF = pd.DataFrame(connection.execute("SELECT AssetID, PriceTime,\
                AssetPrice, Currency FROM AssetPrices").fetchall(), \
                columns=["AssetID","PriceTime","AssetPrice","Currency"])

    # Generate target prices dataframe
    targetpriceDF = pd.DataFrame(connection.execute("SELECT AssetID,TargetPriceLow,\
                TargetPriceHigh,Currency FROM TargetPrices").fetchall(), \
                columns=["AssetID","TargetPriceLow","TargetPriceHigh","Currency"])

    # Generate watchlist dataframe
    print('Generate: Watchlist')

    assetpriceDF['PriceTime']= pd.to_datetime(assetpriceDF['PriceTime'])
    pricetime = assetpriceDF["PriceTime"].max()

    price20time = datetime.datetime.strptime(str(pricetime)[:-9], '%Y-%m-%d')\
                - timedelta(days=19)

    price200time = datetime.datetime.strptime(str(pricetime)[:-9], '%Y-%m-%d')\
                - timedelta(days=199)

    # Get watchlist if it exists
    try:
        oldwlist = pd.read_sql_query("SELECT * FROM qWatchlist", connection)
    except:
        oldwlist = pd.DataFrame()

    watchlistDF = pd.DataFrame()

    if cores < 2:
        # One process means all data for that process and one process only
        watchlistDF = watchlist_asset(assetrefDF['AssetID'], 1)
        
    # multiple processes need the data to be separated
    else:
        assets = np.array_split(assetrefDF['AssetID'].to_numpy(), cores)

        # Define a list of processes form a range
        proc_num = [*range(1, cores + 1)]
        pool = mp.Pool(processes = cores)
    
        pqueue = pool.starmap(watchlist_asset, zip(assets, proc_num))
        pool.close()
        pool.join()
    
        # Iterate the Pool segments for results to build the complete results
        for q in pqueue:
            try:
                if len(q) > 0:
                    watchlistDF = pd.concat([watchlistDF, q], axis = 0, ignore_index=True)
            except:
                if len(q) > 0:
                    watchlistDF = q
    
    watchlistDF.columns = ['AssetID','AssetName','Delta','DeltaPrice','LastPrice',\
                        'PrevPrice','Avg20Price','Avg200Price','TargetLow','TargetHigh',\
                        'MinPrice','MaxPrice','LowPrice','Fib_e382','Fib_r618','Trend']
    # Additional key performance indicators
    watchlistDF['DeltaLow'] = watchlistDF['LastPrice'] - watchlistDF['MinPrice']
    watchlistDF['DeltaHigh'] = watchlistDF['MaxPrice'] - watchlistDF['LastPrice']
    watchlistDF['Avg20Diff'] = (watchlistDF['LastPrice'] - watchlistDF['Avg20Price']) / \
                        watchlistDF['MaxPrice'] * 100
    watchlistDF['Avg200Diff'] = (watchlistDF['LastPrice'] - watchlistDF['Avg200Price']) / \
                        watchlistDF['MaxPrice'] * 100
    watchlistDF['MaxDD']=(watchlistDF['MaxPrice'] - watchlistDF['MinPrice']) / \
                        watchlistDF['MaxPrice'] * -100

    # Finally writing the watchlist to database
    watchlistDF.to_sql('qWatchlist', con=connection, if_exists='replace', index=False)

    # Generate compound dividend dataframe
    print('Generate: Dividends')
    dividendDF = pd.DataFrame()
    for a in assetrefDF['AssetID']:
        dividend = pd.Series([a, filterDF("(?:"+filterList[1][1]+").*"+a).sum()])
        dividendDF = pd.concat([dividendDF, dividend.to_frame().T], \
                    axis = 0, ignore_index=True)
    dividendDF.columns = ['AssetID','Dividend']

    # Generate depot overview dataframe
    print('Generate: Depot Overview')
    depotviewDF = pd.DataFrame()
    depotviewDF = depotDF.copy()
    depotviewDF = depotviewDF.groupby(['AssetID']).sum(['AssetAmount', 'AssetBuyPrice'])
    depotviewDF = pd.merge(depotviewDF,assetrefDF[['AssetID','AssetType']], on="AssetID")
    depotviewDF = pd.merge(depotviewDF,assetrefDF[['AssetID','AssetName']], on="AssetID")
    depotviewDF = pd.merge(depotviewDF,dividendDF[['AssetID','Dividend']], on="AssetID")
    depotviewDF = pd.merge(depotviewDF,watchlistDF[['AssetID','LastPrice']], on="AssetID")
    depotviewDF['Value'] = (depotviewDF['LastPrice'] * depotviewDF['AssetAmount'])
    depotviewDF['Earn'] = depotviewDF['Value'] - depotviewDF['AssetBuyPrice']
    depotviewDF['Return'] = (depotviewDF['Earn'] / depotviewDF['AssetBuyPrice']) * 100
    depotviewDF['DivReturn'] = (depotviewDF['Dividend'] / depotviewDF['AssetBuyPrice']) \
                                * 100
    depotviewDF.to_sql('qDepotOverview', con=connection, if_exists='replace', index=False)

    # Generate performance dataframe
    print('Generate: Performance')
    perfDF = pd.DataFrame()
    perfDF['TotalEarnings'] = [depotviewDF['Earn'].sum() + depotviewDF['Dividend'].sum()]
    perfDF['CoreEarnings'] = [depotviewDF['Earn'].sum()]
    perfDF['TotalInvest'] = [depotviewDF['AssetBuyPrice'].sum()]
    perfDF['BTCInvest'] = depotviewDF.loc[(depotviewDF['AssetID']=='BTC')]['AssetBuyPrice']
    perfDF['BTCEarn'] = depotviewDF.loc[(depotviewDF['AssetID']=='BTC')]['Earn']
    perfDF['TotalPerformance'] = (perfDF['TotalEarnings'] / perfDF['TotalInvest']) * 100
    # Number of days of current year
    datenow = datetime.date.today()
    ydays = pd.Timestamp(datenow.year, datenow.month, datenow.day).dayofyear
    # Total time of investing
    perfDF['Years'] = [len(yearDF['Year']) - 1 + (ydays/365)]
    # (Interest return * 100) / (invested capital * time)
    perfDF['YearPerformance'] = (perfDF['TotalEarnings'] * 100) / \
                                (perfDF['TotalInvest'] * perfDF['Years']) 
    coreearn = perfDF['TotalEarnings'] - perfDF['BTCEarn']
    coreinvest = perfDF['TotalInvest'] - perfDF['BTCInvest']
    perfDF['YearCorePerformance'] = (coreearn * 100) / \
                                (coreinvest * perfDF['Years']) 
    perfDF = perfDF.round(2)
    perfDF.to_sql('qPerformance', con=connection, if_exists='replace', index=False)

    # Generate overview dataframe
    print('Generate: Overview')
    o_cash = accountBalanceDF['Amount'].sum()
    o_portfolio = depotviewDF['Value'].sum()
    o_etf = depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['Value'].sum()
    o_stock = depotviewDF[(depotviewDF['AssetType'] == 'STK')]['Value'].sum()
    o_fund = depotviewDF[(depotviewDF['AssetType'] == 'FND')]['Value'].sum()
    o_real = depotviewDF[(depotviewDF['AssetType'] == 'RET')]['Value'].sum()
    o_gold = depotviewDF[(depotviewDF['AssetID'] == 'Gold')]['Value'].sum()
    o_btc = depotviewDF[(depotviewDF['AssetID'] == 'BTC')]['Value'].sum()

    o_portfolio_b = depotviewDF['AssetBuyPrice'].sum()
    o_etf_b = depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['AssetBuyPrice'].sum()
    o_stock_b = depotviewDF[(depotviewDF['AssetType'] == 'STK')]['AssetBuyPrice'].sum()
    o_fund_b = depotviewDF[(depotviewDF['AssetType'] == 'FND')]['AssetBuyPrice'].sum()
    o_real_b = depotviewDF[(depotviewDF['AssetType'] == 'RET')]['AssetBuyPrice'].sum()
    o_gold_b = depotviewDF[(depotviewDF['AssetID'] == 'Gold')]['AssetBuyPrice'].sum()
    o_btc_b = depotviewDF[(depotviewDF['AssetID'] == 'BTC')]['AssetBuyPrice'].sum()

    o_portfolio_e = depotviewDF['Earn'].sum()
    o_portfolio_e += depotviewDF['Dividend'].sum()
    o_etf_e = depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['Earn'].sum()
    o_etf_e += depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['Dividend'].sum()
    o_stock_e = depotviewDF[(depotviewDF['AssetType'] == 'STK')]['Earn'].sum()
    o_stock_e += depotviewDF[(depotviewDF['AssetType'] == 'STK')]['Dividend'].sum()
    o_fund_e = depotviewDF[(depotviewDF['AssetType'] == 'FND')]['Earn'].sum()
    o_fund_e += depotviewDF[(depotviewDF['AssetType'] == 'FND')]['Dividend'].sum()
    o_gold_e = depotviewDF[(depotviewDF['AssetID'] == 'Gold')]['Earn'].sum()
    o_btc_e = depotviewDF[(depotviewDF['AssetID'] == 'BTC')]['Earn'].sum()

    o_total = o_cash + o_portfolio
    o_total_e = o_portfolio_e
    o_total_b = o_cash + o_portfolio_b

    overviewS = [['Total', o_total, 100, o_total_e, o_total_e/o_total_b*100]]
    overviewS.append(['Cash', o_cash, o_cash/o_total*100, 0, 0])
    overviewS.append(['Portfolio', o_portfolio, o_portfolio/o_total*100, \
                        o_portfolio_e, o_portfolio_e/o_portfolio_b*100])
    overviewS.append(['ETF', o_etf, o_etf/o_total*100, o_etf_e, o_etf_e/o_etf_b*100])
    overviewS.append(['Stock', o_stock, o_stock/o_total*100, o_stock_e, \
                    o_stock_e/o_stock_b*100])
    overviewS.append(['Fund', o_fund, o_fund/o_total*100, o_fund_e, \
                    o_fund_e/o_fund_b*100])
    overviewS.append(['Gold', o_gold, o_gold/o_total*100, o_gold_e, \
                    o_gold_e/o_gold_b*100])
    overviewS.append(['BTC', o_btc, o_btc/o_total*100, o_btc_e, o_btc_e/o_btc_b*100])
    overviewDF = pd.DataFrame(overviewS, columns=['Position', 'Amount', 'Slice', \
                            'Earn','Return'])
    overviewDF = overviewDF.round(2)
    overviewDF.to_sql('qOverview', con=connection, if_exists='replace', index=False)

    # Important products dataframe: gold, USD, BTC
    print('Generate: USD-Prices')
    valuesDF = pd.DataFrame()
    prod = ['USD','Gold','BTC']
    for p in prod:
        valuesDF[p] = [(watchlistDF[['AssetID','LastPrice']]\
            [(watchlistDF['AssetID']==p)]['LastPrice']).iloc[0]]
    valuesDF.to_sql('qUSDValues', con=connection, if_exists='replace', index=False)

    # Closing the database
    connection.commit()
    connection.close()

    # End of FFDM
    print('Init FFDM DB took {} (h:min:s, wall clock time).' \
        .format(datetime.timedelta(seconds=round(time.time() - start_time))))
