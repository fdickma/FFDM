import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
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
import matplotlib.pyplot as plt
import configparser
import csv
import re
import subprocess
from datetime import date, timedelta
import __main__

# Import FFDM function library
import ffdm_lib as fl

import locale
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

def entriesToDB(account_entries, depot_entries):
    
    if len(account_entries) > 1:
        tableName = "Accounts"
        tableData = pd.DataFrame(account_entries[1:],columns=account_entries[0])
        tableData.to_sql(tableName, con=__main__.connection, if_exists='append', index=False, chunksize=__main__.cz)     

    if len(depot_entries) > 1:
        tableName = "Depots"
        tableData = pd.DataFrame(depot_entries[1:],columns=depot_entries[0])
        tableData.to_sql(tableName, con=__main__.connection, if_exists='append', index=False, chunksize=__main__.cz)     
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
            pricetimesDF = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                        [(__main__.assetpriceDF['AssetID']==a)])
            
            amaxpriceDF = pricetimesDF.loc[pricetimesDF.groupby(pricetimesDF['PriceTime']\
                       .dt.normalize())['PriceTime'].idxmax().values]
            amaxpriceDF = amaxpriceDF.reset_index()

            # Get the timestamp of the previous price data update
            # Since len -1 equals the current one we need to reduce the counter by 2 
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

        plt.rcParams["figure.dpi"] = 150
        chartDF = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
        [(__main__.assetpriceDF['AssetID']==a)][['PriceTime','AssetPrice']])\
        .set_index('PriceTime').copy()
        chartDF['SMA20'] = chartDF['AssetPrice'].rolling(20).mean()
        chartDF['SMA200'] = chartDF['AssetPrice'].rolling(200).mean()
        chartDF.plot(title=aname,figsize=(8,4), linewidth = '1.0')
        plt.grid(color = 'grey', linestyle = '--', linewidth = 0.25)
        #current_values = plt.gca().get_yticks()
        #plt.gca().set_yticklabels(['{:,.0f}'.format(x) for x in current_values])
        try:
            plt.savefig(__main__.baseDir+"static/charts/"+a+".png")
        except:
            print("Plot for " + a + " not saved!")

        price20time = datetime.datetime.strptime(str(pricetime)[:-9], '%Y-%m-%d')\
                    - timedelta(days=19)

        price200time = datetime.datetime.strptime(str(pricetime)[:-9], '%Y-%m-%d')\
                    - timedelta(days=199)
        
        if len(__main__.oldwlist) == 0 or recalc == True:
            try:

                price20av = round((__main__.assetpriceDF[['PriceTime','AssetID',\
                            'AssetPrice']]\
                            [(__main__.assetpriceDF['PriceTime']>price20time) \
                            & (__main__.assetpriceDF['AssetID']==a)]['AssetPrice'])\
                            .values.mean(),4)
                price200av = round((__main__.assetpriceDF[['PriceTime','AssetID',\
                            'AssetPrice']]\
                            [(__main__.assetpriceDF['PriceTime']>price200time) \
                            & (__main__.assetpriceDF['AssetID']==a)]['AssetPrice'])\
                            .values.mean(),4)
                maxprice = (__main__.assetpriceDF[['PriceTime','AssetID',\
                            'AssetPrice']]\
                            [(__main__.assetpriceDF['AssetID']==a)]['AssetPrice'])\
                            .values.max()
                maxdate = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                            [(__main__.assetpriceDF['AssetPrice']==maxprice) \
                            & (__main__.assetpriceDF['AssetID']==a)]['PriceTime']).iloc[0]
                lowprice = (__main__.assetpriceDF[['PriceTime','AssetID','AssetPrice']]\
                    [(__main__.assetpriceDF['AssetID']==a)]['AssetPrice']).values.min()
                if maxdate < pricetime:
                    minprice = round((__main__.assetpriceDF[['PriceTime','AssetID',\
                                'AssetPrice']]\
                                [(__main__.assetpriceDF['PriceTime']>maxdate) & \
                                (__main__.assetpriceDF['AssetID']==a)]['AssetPrice'])\
                                .values.min(),4)
                else:
                    minprice = maxprice
                # print(a,"MinPrice:",minprice,"MaxPrice:",maxprice,"MaxDate:",maxdate)
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
        if e_382 < 0:
            e_382 = 0.0

        watchlist = pd.Series([a,aname,delta,deltaprice,lastprice,pricetime,prevprice,\
                    price20av,price200av,lowtarget,hightarget,minprice,maxprice,\
                    lowprice,r_618,e_382,trend])
        watchlistDF = pd.concat([watchlistDF, watchlist.to_frame().T], axis = 0, \
                    ignore_index=True)

    return watchlistDF

def get_currency(id):
    myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    file1 = baseDir + 'assetdata/' + id + '_info.csv'
    file2 = baseDir + 'currencies/' + id + '_info.csv'
    if os.path.exists(file1):
        tdf = pd.read_csv(file1, index_col=None, header=0)
        attr_col = tdf.columns[0]
        val_col = tdf.columns[1]
        currency = tdf[(tdf[attr_col] == 'currency')][val_col].iloc[0]
        return str(currency).upper()
    elif os.path.exists(file2):
        tdf = pd.read_csv(file2, index_col=None, header=0)
        attr_col = tdf.columns[0]
        val_col = tdf.columns[1]
        currency = tdf[(tdf[attr_col] == 'currency')][val_col].iloc[0]
        return str(currency).upper()
    else:
        return 'USD'

def get_currency_data(currency):
    currDF = pd.DataFrame(__main__.connection.execute(sa.text("SELECT * \
                FROM CurrencyRates WHERE AssetID='"+currency + "'")).fetchall(), \
                columns=["Date","AssetID","Currency","Div"])

    return currDF

def build_assetprices(DefaultCurrency):
    
    fl.missing_ticker_data(__main__.user_id)

    histpDF = pd.DataFrame(__main__.connection.execute(sa.text("SELECT * \
                FROM HistoryPrices")).fetchall(), columns=["Date","Open",\
                "High","Low","Close","Adj Close","Volume","AssetID","Currency"])

    if DefaultCurrency != "USD":
        defDF = histpDF[(histpDF["AssetID"] == DefaultCurrency)][["Date","AssetID",\
                "Close"]]
        defDF["Currency"] = "USD"
    else:
        defDF = histpDF[(histpDF["AssetID"] == DefaultCurrency)][["Date"]]
        defDF["AssetID"] = "USD"
        defDF["Close"] = 1
        defDF["Currency"] = "USD"
    defDF = defDF.sort_values(by='Date')
    defDF = defDF.rename(columns={"Close": "Div"})

    currency_tmp = histpDF.Currency
    currency_tmp = currency_tmp.str.upper()
    currency_tmp = currency_tmp.unique()
    currency_list = currency_tmp.tolist()

    currency_list.append('EUR')
    currency_list.append('CHF')
    currency_list.append('JPY')
    currency_list.append('CNY')

    print(list(set(currency_list)))
        
    for x in currency_list:
        # US$ is the central currency, if it is not the default
        # the reciprocal value is to be calculated from US$
        
        if x != "USD":
            tckr = fl.get_ticker(x, __main__.user_id)
            print("Currency:", x, tckr)
            fl.dl_ticker_data(x, tckr, 5)

        # Calc USD when it is not default currency
        if x == 'USD' and DefaultCurrency != 'USD':
            y = histpDF[(histpDF["AssetID"] == DefaultCurrency)]\
                [["Date","AssetID","Close"]].sort_values(by='Date')
            h = y.merge(defDF[['Date','Div']], how="inner", on="Date")
            h['AssetID'] = 'USD'
            h['Div'] = h['Close'] 
        
        # Calc other currency as default currency
        elif x != 'USD' and x == DefaultCurrency:
            y = histpDF[(histpDF["AssetID"] == x)]\
                [["Date","AssetID","Close"]].sort_values(by='Date')
            h = y.merge(defDF[['Date','Div']], how="inner", on="Date")
            h['AssetID'] = x
            h['Div'] = 1
            print("Default currency")

        # Calc other currency as non default currency    
        elif x != 'USD' and DefaultCurrency != 'USD':
            y = histpDF[(histpDF["AssetID"] == x)]\
                [["Date","AssetID","Close"]].sort_values(by='Date')
            h = y.merge(defDF[['Date','Div']], how="inner", on="Date")
            h['AssetID'] = x
            h['Div'] = 1 / (h['Close'] / h['Div'])
            print("Different currency", x)
        
        # Calc other currency
        else:
            y = histpDF[(histpDF["AssetID"] == x)]\
                [["Date","AssetID","Close"]].sort_values(by='Date')
            h = y.merge(defDF[['Date','Div']], how="inner", on="Date")
            h['Div'] = h['Close'] / h['Div']
            print("US Dollar")
        h.to_sql("CurrencyRates", con=__main__.connection, index=False, if_exists='append', chunksize=__main__.cz)

    for x in histpDF.AssetID.unique():
        # Just the non-currency values are being processed.
        if x in currency_list:
            continue
        currency = get_currency(x)
        cuffDF = get_currency_data(currency)
        y = histpDF[(histpDF["AssetID"] == x)]\
            [["Date","AssetID","Close"]].sort_values(by='Date')
        h = y.merge(cuffDF[['Date','Div']], how="inner", on="Date")
        new = pd.DataFrame()
        new['PriceTime'] = pd.to_datetime(h['Date'])
        new['AssetID'] = x
        new['AssetPrice'] = h['Close'] * h['Div']
        new['Currency'] = DefaultCurrency
        new.to_sql("AssetPrices", con=__main__.connection, index=False, if_exists='append', chunksize=__main__.cz)
        print(x, currency)

    # But USD needs to be added
    if DefaultCurrency != "USD":
        currency = get_currency(x)
        cuffDF = get_currency_data(currency)
        y = histpDF[(histpDF["AssetID"] == DefaultCurrency)]\
            [["Date","AssetID","Close"]].sort_values(by='Date')
        h = y.merge(cuffDF[['Date','Div']], how="inner", on="Date")
        new = pd.DataFrame()
        new['PriceTime'] = pd.to_datetime(h['Date'])
        new['AssetID'] = "USD"
        new['AssetPrice'] = 1/ h['Close']
        new['Currency'] = DefaultCurrency
        new.to_sql("AssetPrices", con=__main__.connection, index=False, if_exists='append', chunksize=__main__.cz)
        print(x, "USD")

    return

if __name__ == '__main__':
    # Get the start time
    start_time = time.time()

    cores = os.cpu_count()
    cz = 100
    
    # Get user ID from main process
    user_id = sys.argv[1]
    if len(user_id) == 0 or user_id == '-f':
        user_id = 'test'
    print(user_id)

    baseDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    myDir = baseDir + 'users/' + user_id + '/'
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

    # Iterating account directory entries
    dir_count = 0
    for cdir in config['Accounts']:
        print(cdir)
        if cdir[:3] == "dat":
            dir_count += 1
            if config['Accounts']['dat' + str(dir_count)] != "":
                accountDir.append(config['Accounts']['dat' + str(dir_count)])    

    print("Initialize database...")
    subprocess.run(["python3 " + baseDir + "init_schema.py " + user_id], shell=True, check=True)
    fl.del_images()

    # Create and start DB connection
    appdir = os.path.abspath(os.path.dirname(__file__))
    sql_uri = 'sqlite:///' + os.path.join(appdir, 'users/' + user_id + '/ffdm.sqlite')
    engine = sa.create_engine(sql_uri, echo=False) 
    connection = engine.connect()

    print('Import: Historical Asset Prices')
    history_list = list(glob.glob(baseDir+"assetdata/*.[cC][sS][vV]"))
    for f in history_list:
        print("File: "+f)
        if "_info." in f:
            td = pd.read_csv(f, header=None, skiprows=1, names=["Attribute", "Value"])
            x = os.path.basename(f).split(".")[0].split("_")[0]
            print(x)
            td["AssetID"] = x
            td.to_sql("AssetInfo", con=connection, if_exists='append', index=False, chunksize=__main__.cz)            
        else:
            td = pd.read_csv(f, header=0)
            td.to_sql("HistoryPrices", con=connection, if_exists='append', index=False, chunksize=__main__.cz)
    
    build_assetprices(DefaultCurrency)

    assetpriceDF = pd.DataFrame(connection.execute(sa.text("SELECT AssetID, PriceTime,\
                AssetPrice, Currency FROM AssetPrices")).fetchall(), \
                columns=["AssetID","PriceTime","AssetPrice","Currency"])

    print('Import: Accounts and Depots')
    files_list = list(glob.glob(myDir+"initdata/*.[cC][sS][vV]"))
    for sdir in accountDir:
        files_list.extend(list(glob.glob(myDir + sdir + "/*.[cC][sS][vV]")))

    account_entries = []
    depot_entries = []
    for f in files_list:
        print("File: "+f)
        account_entries, depot_entries = fl.readStatement(f)
        if (len(account_entries)<2 and len(depot_entries)<2):
            tableName = (os.path.splitext(os.path.split(f)[-1])[0])
            tableData = pd.read_csv(f, header=0, sep=";")
            if tableName == "AssetPrices":
                assetprices_tempDF = pd.DataFrame()
                for a in tableData.AssetID.unique():
                    pricetime = (assetpriceDF[['PriceTime','AssetID']]\
                    [(assetpriceDF['AssetID']==a)]["PriceTime"].max())
                    if pd.isna(pricetime) == False:
                        tempTable = tableData[(tableData['AssetID']==a) & \
                            (tableData['PriceTime'] > pricetime)]
                    else:
                        tempTable = tableData[(tableData['AssetID']==a)]
                    try:
                        assetprices_tempDF = pd.concat([assetprices_tempDF,tempTable])
                    except:
                        assetprices_tempDF = tempTable
                assetprices_tempDF['PriceTime'] = \
                    pd.to_datetime(assetprices_tempDF['PriceTime'])
                tableData = assetprices_tempDF

            tableData.to_sql(tableName, con=connection, if_exists='append', index=False, chunksize=__main__.cz)
        else:
            entriesToDB(account_entries, depot_entries)
    
    account_entries, depot_entries = fl.get_vl_plans(connection)
    entriesToDB(account_entries, depot_entries)

    accountDF = pd.DataFrame(connection.execute(sa.text("SELECT Bank,AccountNr,EntryDate,\
                Reference,Amount,Currency FROM Accounts")).fetchall(), \
                columns=["Bank","AccountNr","EntryDate","Reference","Amount","Currency"])

    accountBalanceDF = accountDF.groupby(['Bank','AccountNr'])['Amount'].sum()\
                        .reset_index()
    accountBalanceDF = accountBalanceDF.round(2)
    accountBalanceDF.to_sql("qAccountBalances", con=connection, if_exists='replace', \
                            index=False, chunksize=__main__.cz)

    accountDF = pd.DataFrame(connection.execute(sa.text("SELECT Bank,AccountNr,EntryDate,\
                Reference,Amount,Currency FROM Accounts")).fetchall(), \
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
    yearDF['SavingRate'] = np.where(yearDF['TotalIncome']>0,\
                            yearDF['Saving'] / yearDF['TotalIncome'] * 100,0)
    yearDF['PayMonths'] = countFilterDF(filterList[0][1])
    yearDF['PayMonths'] = yearDF['PayMonths'].fillna(0)
    yearDF['Months'] = getMonths(yearDF['Year'])
    yearDF.to_sql('qYearly', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Generate yearly cumulative dataframe
    print('Generate: Yearly Cumulative')
    cumyearDF = pd.DataFrame()
    cumyearDF = yearDF.cumsum()
    cumyearDF['Year'] = yearDF['Year']
    cumyearDF.to_sql('qCumulative', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Generate monthly average dataframe
    print('Generate: Monthly Data')
    monthDF = pd.DataFrame()
    monthDF['Year'] = tmpDF['Year']
    monthDF['Income'] = np.where(yearDF['PayMonths']>0,\
                        yearDF['TotalIncome'] / yearDF['PayMonths'], 0)
    monthDF['Spend'] = np.where(yearDF['Months']>0,\
                        yearDF['Spending'] / yearDF['Months'],0 )
    monthDF['Invest'] = np.where(yearDF['PayMonths']>0,\
                        yearDF['Invest'] / yearDF['PayMonths'], 0)
    monthDF['Saving'] = np.where(yearDF['PayMonths']>0,\
                        yearDF['Saving'] / yearDF['PayMonths'], 0)
    monthDF=monthDF.round(2)
    monthDF.to_sql('qMonthly', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Generate quarterly cashflow dataframe
    print('Generate: Quarterly Cashflow')
    quarterDF = pd.DataFrame()
    quarterDF['Cashflow'] = accountDF.groupby(accountDF['EntryDate']\
                .dt.to_period('Q'))['Amount'].sum()
    quarterDF['Quarter'] = quarterDF.index.astype(str).str.\
                            replace(r'(\d+)Q(\d)', r'\1-Q\2', regex=True)
    quarterDF = quarterDF.round(2)
    quarterDF.to_sql('qQuarterly', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Generate spending dataframe
    print('Generate: Spending')
    spendDF = pd.DataFrame()
    spendDF['Year'] = tmpDF['Year']
    for spendLine in spendList:
        spendDF[spendLine[0]] = filterDF(spendLine[1])
    spendDF['Total'] = spendDF.sum(axis=1, numeric_only=True)
    spendDF = spendDF.fillna(0)
    spendDF.to_sql('qSpending', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Generate depot dataframes
    print('Generate: Depots')
    depotDF = pd.DataFrame(connection.execute(sa.text("SELECT Bank,DepotNr,AssetID,\
                BankRef, AssetAmount, AssetBuyPrice, Currency FROM Depots")).fetchall(),\
                columns=["Bank","DepotNr","AssetID","BankRef","AssetAmount",\
                "AssetBuyPrice","Currency"])

    # Gold grams to ounce
    depotDF['AssetAmount'] = np.where(depotDF['AssetID'] == 'Gold',
                                            depotDF['AssetAmount'] / 31.1034768,
                                            depotDF['AssetAmount'])

    assetrefDF = pd.DataFrame(connection.execute(sa.text("SELECT AssetID, AssetType,\
                AssetName, Ticker, NetRef1, NetRef2 FROM AssetReferences")).fetchall(), \
                columns=["AssetID","AssetType","AssetName","Ticker","NetRef1","NetRef2"])

    assetpriceDF = pd.DataFrame(connection.execute(sa.text("SELECT AssetID, PriceTime,\
                AssetPrice, Currency FROM AssetPrices")).fetchall(), \
                columns=["AssetID","PriceTime","AssetPrice","Currency"])

    # Generate target prices dataframe
    targetpriceDF = pd.DataFrame(connection.execute(sa.text("SELECT AssetID,TargetPriceLow,\
                TargetPriceHigh,Currency FROM TargetPrices")).fetchall(), \
                columns=["AssetID","TargetPriceLow","TargetPriceHigh","Currency"])

    # Generate watchlist dataframe
    print('Generate: Watchlist')

    assetpriceDF['PriceTime']= pd.to_datetime(assetpriceDF['PriceTime'])

    # Get watchlist if it exists
    try:
        oldwlist = pd.read_sql_query(sa.text("SELECT * FROM qWatchlist"), connection)
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
                        'PriceTime','PrevPrice','Avg20Price','Avg200Price','TargetLow',\
                        'TargetHigh','MinPrice','MaxPrice','LowPrice','Fib_r618',\
                        'Fib_e382','Trend']
    
    # Additional key performance indicators
    watchlistDF['DeltaLow'] = watchlistDF['LastPrice'] - watchlistDF['MinPrice']
    watchlistDF['DeltaHigh'] = watchlistDF['MaxPrice'] - watchlistDF['LastPrice']
    watchlistDF['Avg20Diff'] = (watchlistDF['LastPrice'] - watchlistDF['Avg20Price']) / \
                        watchlistDF['Avg20Price'] * 100
    watchlistDF['Avg200Diff'] = (watchlistDF['LastPrice'] - watchlistDF['Avg200Price']) / \
                        watchlistDF['Avg200Price'] * 100
    watchlistDF['MaxDD']=(watchlistDF['MaxPrice'] - watchlistDF['MinPrice']) / \
                        watchlistDF['MaxPrice'] * -100

    # Finally writing the watchlist to database
    watchlistDF.to_sql('qWatchlist', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

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
    depotviewDF['TotReturn'] = depotviewDF['Return'] + depotviewDF['DivReturn']
    depotviewDF.to_sql('qDepotOverview', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Generate performance dataframe
    print('Generate: Performance')
    perfDF = pd.DataFrame()
    perfDF['TotalEarnings'] = [depotviewDF['Earn'].sum() + depotviewDF['Dividend'].sum()]
    perfDF['CoreEarnings'] = [depotviewDF['Earn'].sum()]
    perfDF['TotalInvest'] = [yearDF['Invest'].sum()]
    perfDF['BTCInvest'] = depotviewDF.loc[(depotviewDF['AssetID']=='BTC')]['AssetBuyPrice']
    perfDF['BTCEarn'] = depotviewDF.loc[(depotviewDF['AssetID']=='BTC')]['Earn']

    perfDF['TotalPerformance'] = (perfDF['TotalEarnings'] / perfDF['TotalInvest']) * 100
    perfDF['AverageInvest'] = (cumyearDF['Invest'].mean())
    perfDF['AveragePerformance'] = (perfDF['TotalEarnings'] / perfDF['AverageInvest'])
    perfDF['DividendPerformance'] = (yearDF['Dividend'].sum() / \
                                perfDF['TotalInvest']) * 100

    # Number of days of current year
    datenow = datetime.date.today()
    ydays = pd.Timestamp(datenow.year, datenow.month, datenow.day).dayofyear
    # Total time of investing
    year_factor = 1/(len(yearDF['Year']) - 1 + (ydays/365))

    perfDF['YearPerformance'] = (((1 + (perfDF['AveragePerformance'])) ** \
                                (year_factor)) - 1) * 100 
    
    coreearn = perfDF['TotalEarnings'] - perfDF['BTCEarn']
    coreinvest = perfDF['AverageInvest'] - perfDF['BTCInvest']
    coreperf = coreearn / coreinvest

    perfDF['YearCorePerformance'] = (((1 + (coreperf)) ** \
                                (year_factor)) - 1) * 100

    perfDF = perfDF.round(2)
    perfDF.to_sql('qPerformance', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Generate overview dataframe
    print('Generate: Overview')
    o_cash = accountBalanceDF['Amount'].sum()
    o_portfolio = depotviewDF['Value'].sum()
    o_etf = depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['Value'].sum()
    o_stock = depotviewDF[(depotviewDF['AssetType'] == 'STK')]['Value'].sum()
    o_bonds = depotviewDF[(depotviewDF['AssetType'] == 'BND')]['Value'].sum()
    o_fund = depotviewDF[(depotviewDF['AssetType'] == 'FND')]['Value'].sum()
    o_real = depotviewDF[(depotviewDF['AssetType'] == 'RET')]['Value'].sum()
    o_gold = depotviewDF[(depotviewDF['AssetID'] == 'Gold')]['Value'].sum()
    o_crypto = depotviewDF[(depotviewDF['AssetType'] == 'CRP')]['Value'].sum()

    o_portfolio_b = depotviewDF['AssetBuyPrice'].sum()
    o_etf_b = depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['AssetBuyPrice'].sum()
    o_stock_b = depotviewDF[(depotviewDF['AssetType'] == 'STK')]['AssetBuyPrice'].sum()
    o_bonds_b = depotviewDF[(depotviewDF['AssetType'] == 'BND')]['AssetBuyPrice'].sum()
    o_fund_b = depotviewDF[(depotviewDF['AssetType'] == 'FND')]['AssetBuyPrice'].sum()
    o_real_b = depotviewDF[(depotviewDF['AssetType'] == 'RET')]['AssetBuyPrice'].sum()
    o_gold_b = depotviewDF[(depotviewDF['AssetID'] == 'Gold')]['AssetBuyPrice'].sum()
    o_crypto_b = depotviewDF[(depotviewDF['AssetType'] == 'CRP')]['AssetBuyPrice'].sum()

    o_portfolio_e = depotviewDF['Earn'].sum()
    o_portfolio_e += depotviewDF['Dividend'].sum()
    o_etf_e = depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['Earn'].sum()
    o_etf_e += depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['Dividend'].sum()
    o_stock_e = depotviewDF[(depotviewDF['AssetType'] == 'STK')]['Earn'].sum()
    o_stock_e += depotviewDF[(depotviewDF['AssetType'] == 'STK')]['Dividend'].sum()
    o_bonds_e = depotviewDF[(depotviewDF['AssetType'] == 'BND')]['Earn'].sum()
    o_bonds_e += depotviewDF[(depotviewDF['AssetType'] == 'BND')]['Dividend'].sum()
    o_fund_e = depotviewDF[(depotviewDF['AssetType'] == 'FND')]['Earn'].sum()
    o_fund_e += depotviewDF[(depotviewDF['AssetType'] == 'FND')]['Dividend'].sum()
    o_gold_e = depotviewDF[(depotviewDF['AssetID'] == 'Gold')]['Earn'].sum()
    o_crypto_e = depotviewDF[(depotviewDF['AssetType'] == 'CRP')]['Earn'].sum()
    o_cash_e = yearDF['Interest'].sum()
    o_cash_b = o_cash - o_cash_e

    o_total = o_cash + o_portfolio
    o_total_e = o_portfolio_e + o_cash_e
    o_total_b = o_cash + o_portfolio_b

    # Counting types of assets
    num_etf = depotviewDF[(depotviewDF['AssetType'] == 'ETF')]['AssetID'].nunique()
    num_stock = depotviewDF[(depotviewDF['AssetType'] == 'STK')]['AssetID'].nunique()
    num_bonds = depotviewDF[(depotviewDF['AssetType'] == 'BND')]['AssetID'].nunique()
    num_fund = depotviewDF[(depotviewDF['AssetType'] == 'FND')]['AssetID'].nunique()
    num_crypto = depotviewDF[(depotviewDF['AssetType'] == 'CRP')]['AssetID'].nunique()
    
    overviewS = [['Total', o_total, 100, o_total_e, o_total_e/o_total_b*100, 1]]
    overviewS.append(['Cash', o_cash, o_cash/o_total*100, o_cash_e, o_cash_e/o_cash_b*100, 1])
    overviewS.append(['Invested', o_portfolio, o_portfolio/o_total*100, \
                        o_portfolio_e, o_portfolio_e/o_portfolio_b*100, 1])
    overviewS.append(['ETF', o_etf, o_etf/o_total*100, o_etf_e, o_etf_e/o_etf_b*100, \
                        num_etf])
    overviewS.append(['Stock', o_stock, o_stock/o_total*100, o_stock_e, \
                    o_stock_e/o_stock_b*100, num_stock])
    overviewS.append(['Bonds', o_bonds, o_bonds/o_total*100, o_bonds_e, \
                    o_bonds_e/o_bonds_b*100, num_bonds])
    overviewS.append(['Funds', o_fund, o_fund/o_total*100, o_fund_e, \
                    o_fund_e/o_fund_b*100, num_fund])
    overviewS.append(['Gold', o_gold, o_gold/o_total*100, o_gold_e, \
                    o_gold_e/o_gold_b*100, 1])
    overviewS.append(['Crypto', o_crypto, o_crypto/o_total*100, o_crypto_e, \
                    o_crypto_e/o_crypto_b*100, num_crypto])
    overviewDF = pd.DataFrame(overviewS, columns=['Position', 'Amount', 'Slice', \
                            'Earn','Return','Items'])
    overviewDF = overviewDF.round(2)
    overviewDF.to_sql('qOverview', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Important products dataframe: gold, USD, BTC
    print('Generate: USD-Prices')
    valuesDF = pd.DataFrame()
    prod = ['USD','Gold','BTC']
    for p in prod:
        valuesDF[p] = [(watchlistDF[['AssetID','LastPrice']]\
            [(watchlistDF['AssetID']==p)]['LastPrice']).iloc[0]]
    valuesDF.to_sql('qUSDValues', con=connection, if_exists='replace', index=False, chunksize=__main__.cz)

    # Closing the database
    connection.close()

    # End of FFDM
    print('Init FFDM DB took {} (h:min:s, wall clock time).' \
        .format(datetime.timedelta(seconds=round(time.time() - start_time))))
