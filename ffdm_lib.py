#
# Free Financial Data Management - FFDM/OSS.
# Functions library
# 
# Frank Dickmann, Germany, 2021.04.07
# 
# Version 1.0
#

import re
import datetime
import time
import csv
import os
import locale
import glob
import configparser
import requests
import ast
import yfinance as yf
import pandas as pd
import numpy as np
import sqlalchemy as sa
from dateutil.relativedelta import relativedelta

def get_db_data(sql_string, u_id):
    db_data = []
    try:
        appdir = os.path.abspath(os.path.dirname(__file__))
        sql_uri = 'sqlite:///' + os.path.join(appdir, 'users/' + u_id + '/ffdm.sqlite')
        engine = sa.create_engine(sql_uri, echo=False) 
        with engine.connect() as connection:
            result = connection.execute(sa.text(sql_string))
            for row in result:
                db_data.append(row)
        return db_data
    except:
        return None

def get_user_db(sql_string):
    db_data = []
    try:
        appdir = os.path.abspath(os.path.dirname(__file__))
        sql_uri = 'sqlite:///' + os.path.join(appdir, 'userdb.sqlite')
        engine = sa.create_engine(sql_uri, echo=False) 
        with engine.connect() as connection:
            result = connection.execute(sa.text(sql_string))
            for row in result:
                db_data.append(row)
        return db_data
    except:
        return None

def del_images():
    baseDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    del_list = list(glob.glob(baseDir+"static/charts/*.*"))
    for d in del_list:
        os.remove(d)
    return

# Return a float or integer depending on an existing dot
def check_float(num):
    try:
        if "." in num:
            return float(num)
        else:
            return int(num)
    except ValueError:
       return -1

# Return a short date from a datetime input
def shortDate(inDate):
    try:
        date_object = time.strptime(inDate, '%d.%m.%Y')
    except:
        date_object = time.strptime(inDate, '%d.%m.%y')                    
    return datetime.date(date_object[0],\
                         date_object[1],\
                         date_object[2])

def vl_fund(bank, account, start_date, end_date, ref_text, curr, amnt, pcs):
    now = datetime.datetime.now()
    now_str = str(now.year) + "-" + str(now.month) + "-" + str(now.day)
    #start = time.strptime(start_date, '%d.%m.%Y')
    if end_date == "None" or end_date == None:
        max_date = datetime.datetime.strptime(now_str, '%Y-%m-%d')
    else:
        max_date = datetime.datetime.strptime(end_date,'%Y-%m-%d')
    start = datetime.datetime.strptime(start_date,'%Y-%m-%d')
    start_y = start.year
    ref_1 = "LOHN GEHALT VL "
    ref_2 = "Wertpapiere VL "
    VL_sum = 0
    account_entries = []
    depot_entries = []
    # Iterate all years
    for y in range(start_y, now.year +1, 1):
        # Iterate 12 months
        for m in range(1, 13, 1):
            e_date = "01."+str(m)+"."+str(y)
            if (datetime.datetime.strptime(e_date, '%d.%m.%Y') < \
               max_date) and \
               (datetime.datetime.combine(start, \
                datetime.datetime.min.time()) <= \
               datetime.datetime.strptime(e_date, '%d.%m.%Y')):
                if (y==now.year) and (m==now.month):
                    continue
                entry_date = shortDate("01."+str(m)+"."+str(y))
                account_entries.append([bank, account, entry_date, \
                            ref_1 + ref_text, amnt, curr])
                account_entries.append([bank, account, entry_date, \
                            ref_2 + ref_text, amnt * -1, curr])
                print("VL:", entry_date)
                VL_sum += amnt
    depot_entries.append([bank, account, ref_text, \
                ref_text, pcs, VL_sum, curr])    
    return account_entries, depot_entries

def get_vl_plans(connection):
    print("VL Plans")

    account_entries = []
    account_entries.append(["Bank","AccountNr","EntryDate","Reference","Amount",\
                        "Currency"])
    depot_entries = []
    depot_entries.append(["Bank","DepotNr","AssetID","BankRef","AssetAmount",\
                        "AssetBuyPrice","Currency"])

    vlplans = connection.execute(sa.text("SELECT * FROM VLplans ORDER BY PlanID")).fetchall()
    for plan in vlplans:
        account_tmp, depot_tmp = vl_fund(plan[5], plan[6], plan[2], plan[3], \
                                        plan[4], plan[9], plan[7], plan[8])
        account_entries.extend(account_tmp)
        depot_entries.extend(depot_tmp)

    return account_entries, depot_entries

# Get a 10 character account ID / number
def get_account(account):
    
    # Replace credit card anonymizing stars and fill up to 10 digits
    account = account.replace("********", "00")

    # Cut down to a max of 10 digits
    account = account[-10:]
   
    # Fill up to 10 digits
    if len(account) < 10:
        account = account.zfill(10)
    
    return account

# Read data files
def readStatement(File):
    account_entries = []
    account_entries.append(["Bank","AccountNr","EntryDate","Reference","Amount",\
                        "Currency"])
    depot_entries = []
    depot_entries.append(["Bank","DepotNr","AssetID","BankRef","AssetAmount",\
                        "AssetBuyPrice","Currency"])
    try:
        rf = open(File, encoding='latin-1')
    except FileNotFoundError:
        print('File ' + File + ' not found.')
    else:
               
        p_init_accounts = re.compile(
            r'\"([A-Za-z0-9]{3,10})\"\;'       # Bank.
            r'\"([A-Za-z0-9]*)\"\;'            # Konto.
            r'\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Wertstellung.
            r'\"(.*)\"\;'                      # Bezeichnung.
            r'\"([-\d.]*\,\d*)\"\;'            # Betrag (EUR).
            r'\"(.*)\"\n')                     # Waehrung.             
        p_init_assets = re.compile(
            r'\"([A-Za-z0-9]{3,10})\"\;'       # Bank.
            r'\"([A-Za-z0-9]*)\"\;'            # Konto.
            r'\"([A-Za-z0-9]*)"\;'             # WKN/ISIN.
            r'\"(.*)\"\;'                      # Bezeichnung.
            r'\"([\d.]*\,\d*)\"\;'             # Stück.
            r'\"([-\d.]*\,\d*)\";'             # Betrag (EUR).
            r'\"(.*)\"\n')                     # Waehrung.             
        p_dkb_depot = re.compile(
            r'\"([\d.]*\,\d*)\"\;'             # Bestand.
            r'"Stück"\;'                       # Stück.
            r'\"([A-Za-z0-9]{6,12})\"\;'       # ISIN/WKN.
            r'\"(.*)\"\;'                      # Bezeichnung.
            r'\"(.*)\"\;'                      # Kurs.
            r'\"(.*)\"\;'                      # Gewinn/Verlust.
            r'".*"\;'                          # "".
            r'\"(.*)\"\;'                      # Einstandskurs.
            r'".*"\;".*"\;'                    # ""; Dev. Kurs.
            r'\"(.*)\"\;'                        # "Kurswert in Euro".
            r'\"Frei\"\;')                     # Konto Gegenbuchung.
        p_dkb_cash = re.compile(
            r'\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Buchungstag.
            r'\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Wertstellung.
            r'\"(.*)\"\;'                      # Buchungstext.
            r'\"(.*)\"\;'                      # Auftraggeber / Begünstigter.  
            r'\"(.*)\"\;'                      # Verwendungszweck.
            r'\"([A-Za-z0-9]*)\"\;'            # Kontonummer.
            r'\"([A-Za-z0-9]*)\"\;'            # BLZ.
            r'\"([-\d.]*\,\d*)\"\;'            # Betrag (EUR).
            r'\"(.*)\"\;'                      # Gläubiger-ID.
            r'\"(.*)\"\;'                      # Mandatsreferenz.
            r'\"(.*)\"\;')                     # Kundenreferenz.
        p_dkb_visa = re.compile(
            r'\"(Ja|ja|Nein|nein|NEIN|JA)\"\;' # Umsatz abgerechnet.
            r'\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Wertstellung.
            r'\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Belegdatum.
            r'\"(.*)\"\;'                      # Beschreibung.
            r'\"([-\d.]*\,\d*)\"\;'            # Betrag (EUR).
            r'\"(.*)\"\;')                     # Ursprünglicher Betrag.
        p_spk = re.compile(
            r'\"([A-Za-z0-9]*)"\;'             # Auftragskonto.
            r'\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Buchungstag.
            r'\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Valutadatum.
            r'\"(.*)\"\;'                      # Buchungstext.
            r'\"(.*)\"\;'                      # Verwendungszweck.
            r'\"(.*)\"\;'                      # Beguenstigter.
            r'\"([A-Za-z0-9]*)\"\;'            # Kontonummer.
            r'\"([A-Za-z0-9]*)\"\;'            # BLZ.
            r'\"([-\d.]*\,\d*)\"\;'            # Betrag.
            r'\"(.*)\"\;'                      # Waehrung.
            r'\"Umsatz.*\"')                   # Info.
        p_dkb_account = re.compile(
            r'\"([A-Za-z]*\:)\"\;'
            r'\"([A-Za-z]{2}[0-9]*|'
            r'[0-9]{4}[\*]{8}[0-9]{4}|'
            r'[0-9]*).*[A-Za-z]*'
            r'(.*)\"\;')
        
        account = None
        i = 0

        for line in rf:
            line_check = False
         
            if account == None:
                account_test = p_dkb_account.match(line)
                if account_test:
                    account = account_test.group(2)
        
            init_acc = p_init_accounts.match(line)
            if init_acc and not line_check:
                i += 1
                line_check = True
                price = str(init_acc.group(5))
                price = price.replace('.', '').replace(',', '.')
                date = shortDate(init_acc.group(3))
                text = init_acc.group(4)
                account = get_account(init_acc.group(2))
                bank = str(init_acc.group(1))
                curr = str(init_acc.group(6))
                account_entries.append([bank, account, date, text, \
                                    check_float(price), curr])
            
            init_ass = p_init_assets.match(line)
            if init_ass and not line_check:
                i += 1
                line_check = True
                amount = str(init_ass.group(5))
                amount = amount.replace('.', '').replace(',', '.')
                price = str(init_ass.group(6))
                price = price.replace('.', '').replace(',', '.')
                text = init_ass.group(4)
                account = get_account(init_ass.group(2))
                bank = str(init_ass.group(1))
                curr = str(init_ass.group(7))
                depot_entries.append([bank, account, init_ass.group(3),
                                    text, check_float(amount), \
                                    check_float(price), curr])
            
            spk = p_spk.match(line)
            if spk and not line_check:
                i += 1
                line_check = True
                price = str(spk.group(9))
                price = price.replace('.', '').replace(',', '.')
                account = get_account(spk.group(1))
                date = shortDate(spk.group(2))
                text = spk.group(4) + " " + spk.group(5) + \
                        " " + spk.group(6)
                curr = str(spk.group(10))
                account_entries.append(["SPK", account, date, text, \
                                    check_float(price), curr])
            
            dkb_depot = p_dkb_depot.match(line)
            if dkb_depot and not line_check:
                i += 1
                line_check = True
                amount = str(dkb_depot.group(1))
                price = str(dkb_depot.group(6))
                account = get_account(account)
                amount = amount.replace('.', '').replace(',', '.')
                price = price.replace('.', '').replace(',', '.')
                #print("Reading depot entry:", dkb_depot.group(2), "-"+price+"-")
                if price == "":
                    print("Depot entry without price", dkb_depot.group(2))
                    price = "1"
                curr = DefaultCurrency
                depot_entries.append(["DKB", account, \
                                    dkb_depot.group(2), dkb_depot.group(3), \
                                    check_float(amount), check_float(price), \
                                    curr])
            
            dkb_cash = p_dkb_cash.match(line)
            if dkb_cash and not line_check:
                i += 1
                line_check = True
                price = str(dkb_cash.group(8))
                price = price.replace('.', '').replace(',', '.')
                account = get_account(account)
                date = shortDate(dkb_cash.group(1))
                text = dkb_cash.group(3) + " " + dkb_cash.group(4) + \
                        " " + dkb_cash.group(5)
                curr = DefaultCurrency
                account_entries.append(["DKB", account, date, text, \
                                    check_float(price), curr])
            
            dkb_visa = p_dkb_visa.match(line)
            if dkb_visa and not line_check:
                i += 1
                line_check = True
                price = str(dkb_visa.group(5))
                price = price.replace('.', '').replace(',', '.')
                date = shortDate(dkb_visa.group(3))
                account = get_account(account)
                text = dkb_visa.group(4)
                curr = DefaultCurrency
                account_entries.append(["DKB", account, date, text, \
                                    check_float(price), curr])

        rf.close()
    return account_entries, depot_entries

# Checking if entries already exist
def checkDuplicates(file_entries):
    return file_entries

# Export data into CSV file
def gen_dataFile(filename, export_lines):
    with open(filename, 'w', newline='') as csvfile:
        datawriter = csv.writer(csvfile, delimiter=';', 
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for line in export_lines:
            datawriter.writerow(line)

# Process investment payments
def processInvest(invest_lines):
    for line in invest_lines:
        if (line[3].count("Wertpapiere") or line[3].count("Wertpapiere")) > 0:
            print(line[4])
    return invest_lines

# Read config file
def readConfig(filename, section):
    myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    config = configparser.ConfigParser()
    config.sections()
    config.read(myDir + filename)
    return dict(config.items(section))

# Write config file
def writeConfig(filename, section, changes):
    myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    config = configparser.ConfigParser()
    config.sections()
    config.read(myDir + filename)
    for chn in changes:
        chn.insert(0, section)
        config.set(chn[0], chn[1], chn[2].replace('%','%%'))
    with open(myDir + filename, 'w') as configfile:
        config.write(configfile)
    configfile.close()

def format_number(number):
    
    decNum = number % 1

    if number > 0:
    
        if number < 10 and number >= 1 and decNum != 0:
            p_number = str(locale.format_string(\
                '%.2f', round(number,2),1))
        elif number < 1 and decNum != 0:
            p_number = str(locale.format_string(\
                '%.3f', round(number,3),1))
        elif number > 1000:
            p_number = str(locale.format_string(\
                '%.0f', round(number,1),1))
        else:
            p_number = str(locale.format_string(\
                '%.1f', round(number,1),1))

    elif number < 0:

        if number > -10 and number <= -1 and decNum != 0:
            p_number = str(locale.format_string(\
                '%.2f', round(number,2),1))
        elif number > -1 and decNum != 0:
            p_number = str(locale.format_string(\
                '%.3f', round(number,3),1))
        elif number < -1000:
            p_number = str(locale.format_string(\
                '%.0f', round(number,1),1))
        else:
            p_number = str(locale.format_string(\
                '%.1f', round(number,1),1))
    else:

        p_number = 0

    return p_number

def format_snumber(number):
    
    decNum = number % 1

    if number > 0:
    
        if number < 10 and number >= 1:
            p_number = str(locale.format_string(\
                '%.1f', round(number,1),1))
        elif number < 1 and decNum != 0:
            p_number = str(locale.format_string(\
                '%.2f', round(number,2),1))
        elif number > 1000:
            p_number = str(locale.format_string("%d",int(number),1))
        else:
            p_number = str(locale.format_string(\
                '%d', int(number),1))

    elif number < 0:

        if number > -10 and number <= -1:
            p_number = str(locale.format_string(\
                '%.1f', round(number,1),1))
        elif number > -1 and decNum != 0:
            p_number = str(locale.format_string(\
                '%.2f', round(number,2),1))
        elif number < -1000:
            p_number = str(locale.format_string("%d",int(number),1))
        else:
            p_number = str(locale.format_string(\
                '%d', int(number),1))
    else:

        p_number = 0

    return p_number

def format_percent(number):
    return round(number, 1)

def get_of_ticker(isin):
    myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    ticker_dir = myDir + "of_ticker" + "/"
    ticker_file = ticker_dir + isin + ".csv"
    if not os.path.exists(ticker_dir):
        os.makedirs(ticker_dir)
    if os.path.exists(ticker_file):
        data = pd.read_csv(ticker_file)        
    else:
        response = requests.post(url='https://api.openfigi.com/v3/mapping',
                            headers={'Content-Type': 'text/json'},
                            json=[{
                                'idType': 'ID_ISIN',
                                'idValue': isin
                            }])
        try:
            full_data = str(response.json())
            full_data = full_data.replace("{'data': [", '')
            full_data = full_data.replace("]}", '')
            full_data = full_data.replace("]", '')
            full_data = full_data.replace("[", '')
            full_data = full_data.replace("'", '"')
            data = ast.literal_eval(full_data)
            if type(data) is tuple:
                pd.DataFrame(data).to_csv(ticker_file, header=True, index=False)
            else:
                return None
        except:
            return None
    data = pd.read_csv(ticker_file)
    for idx, entry in data.iterrows():
        return entry['ticker']

def get_yf_ticker(isin):
    url = 'https://query1.finance.yahoo.com/v1/finance/search'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36',
    }

    params = dict(
        q=isin,
        quotesCount=1,
        newsCount=0,
        listsCount=0,
        quotesQueryId='tss_match_phrase_query'
    )

    resp = requests.get(url=url, headers=headers, params=params)
    data = resp.json()
    if 'quotes' in data and len(data['quotes']) > 0:
        return data['quotes'][0]['symbol']
    else:
        return None
        
def get_existing_ticker(isin, u_id):
    aDF = get_assets(u_id)
    usd_values = [['EUR=X', 'EUR'], ['CHF=X', 'CHF'], ['JPY=X', 'JPY'], \
                ['BTC-USD', 'BTC'], ['GC=F', 'Gold'], ['GBP=X', 'GBP'], \
                ['HKD=X', 'HKD'], ['CNY=X', 'CNY'], ['DKK=X', 'DKK']]
    cyDF = pd.DataFrame(usd_values, columns =['Ticker', 'AssetID'])
    try:
        return cyDF[(cyDF['AssetID'] == isin)]['Ticker'].iloc[0]
    except:
        try:
            return aDF[(aDF['AssetID'] == isin)]['Ticker'].iloc[0]
        except:
            return None
        
def get_ticker(isin, u_id):   
    ticker = get_existing_ticker(isin, u_id)
    if ticker != None and str(ticker) != "nan":
        return ticker
    ticker = get_of_ticker(isin)
    if ticker is None:
        ticker = get_yf_ticker(isin)
    return ticker

def convert_date(now):
    return str(now.year) + "-" + str(now.month) + "-" + str(now.day)

def get_ticker_info(ticker, file):
    ticker_object = yf.Ticker(ticker)
    try:
        temp = pd.DataFrame.from_dict(ticker_object.info, orient="index")
        temp.to_csv(file, header=True)
    except:
        return

def get_ticker_currency(ticker, file):
    if os.path.exists(file):
        tdf = pd.read_csv(file, index_col=None, header=0)
        attr_col = tdf.columns[0]
        val_col = tdf.columns[1]
        currency = tdf[(tdf[attr_col] == 'currency')][val_col].iloc[0]
        return str(currency).upper()
    else:
        return 'USD'

def dl_ticker_data(isin, ticker, years):
    if ticker != None:
        now_date = datetime.datetime.now()
        end_d = convert_date(now_date)
        start_year = int(end_d[0:4]) - years
        myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
        ticker_dir = myDir + "assetdata/"
        if not os.path.exists(ticker_dir):
            os.makedirs(ticker_dir)
        li = []
        data_missing = list()
        for tyear in range(0, years + 1, 1):
            ticker_file = ticker_dir + isin + "_" + str(start_year + tyear) + ".csv"
            if os.path.exists(ticker_file):
                df = pd.read_csv(ticker_file, index_col=None, header=0)
                li.append(df)
            else:
                data_missing.append(start_year + tyear)
        infofile = ticker_dir + isin + "_info.csv"
        if not os.path.exists(infofile):
            get_ticker_info(ticker, infofile)
        currency = get_ticker_currency(ticker, infofile)
        if len(data_missing) > 0:
            start_year = min(data_missing)
        else:
            start_year = end_d[0:4]
        start_d = str(start_year) + "-01-01"
        if len(li) > 0:
            ticker_data = pd.concat(li, axis=0, ignore_index=True)
        # Check if the data file is older than today
        if os.path.exists(ticker_dir + isin + "_" + str(end_d)[:4] + ".csv") == True:
            filetime = os.path.getmtime(ticker_dir + isin + "_" + str(end_d)[:4] + ".csv")
            day_date = str(now_date)[:10]
            lastfile = time.strftime("%Y-%m-%d",time.localtime(filetime))
            fileDate = datetime.datetime.strptime(lastfile, "%Y-%m-%d")
            nowDate = datetime.datetime.strptime(day_date, "%Y-%m-%d")
            if fileDate >= nowDate:
                return
            dload = yf.download(ticker, 
                    start=start_d, 
                    end=end_d, 
                    progress=True, timeout=10)
            dload['AssetID'] = isin
            dload['Currency'] = currency
            li = []
            df = pd.DataFrame(dload)
            for i, x in df.groupby(df.index.year):
                ticker_file = ticker_dir + isin + "_" + str(i) + ".csv"
                x.to_csv(ticker_file, header=True)
                df = pd.read_csv(ticker_file, index_col=None, header=0)
                li.append(df)
            ticker_data = pd.concat(li, axis=0, ignore_index=True)
    else:
        return None

def get_currencies():
    # Main currencies
    usd_values = [['EUR=X', 'EUR'], ['CHF=X', 'CHF'], ['JPY=X', 'JPY'], \
                ['BTC-USD', 'BTC'], ['GC=F', 'Gold']]
    for v in usd_values:
        dl_ticker_data(v[1], v[0], 5)
    return

def get_assets(u_id):
    myDir = os.path.abspath(os.path.dirname(__file__)) + '/' + 'users/' + u_id + '/'
    assetRefFile = myDir+"initdata/AssetReferences.csv"
    if os.path.isfile(assetRefFile) and os.path.getsize(assetRefFile) > 0:
        assetRefsDF = pd.read_csv(assetRefFile, quotechar='"', sep=";")
    else:
        assetRefsDF = pd.DataFrame(columns=["AssetID"])    
    return assetRefsDF

def isin_data(isin, last_update, u_id):
    ticker = get_ticker(isin, u_id)
    print(isin, ticker)
    past_years = 5
    if ticker == None:
        print("Failed to get ticker for", isin)
        return None
    if len(ticker) == 0:
        print("Failed to get ticker for", isin)
        return None
    now_date = datetime.datetime.now()
    last_update_date = datetime.datetime.strptime(last_update, '%Y-%m-%d')
    last_update_date += datetime.timedelta(days=1)
    print(last_update_date)
    # print(bool(len(pd.bdate_range(last_update_date, now_date))))
    end_d = convert_date(now_date)
    start_year = int(end_d[0:4]) - past_years
    myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    isin_dir = myDir + "assetdata/"
    if not os.path.exists(isin_dir):
        os.makedirs(ticker_dir)
    infofile = isin_dir + isin + "_info.csv"
    if not os.path.exists(infofile):
        get_ticker_info(ticker, infofile)
    currency = get_ticker_currency(ticker, infofile)
    start_d = str(last_update[0:4]) + "-01-01"
    # Check if the data file is older than today
    if os.path.exists(isin_dir + isin + "_" + str(end_d)[:4] + ".csv") == True:
        filetime = os.path.getmtime(isin_dir + isin + "_" + str(end_d)[:4] + ".csv")
        day_date = str(now_date)[:10]
        lastfile = time.strftime("%Y-%m-%d",time.localtime(filetime))
        fileDate = datetime.datetime.strptime(lastfile, "%Y-%m-%d")
        nowDate = datetime.datetime.strptime(day_date, "%Y-%m-%d")
        if fileDate >= nowDate:
            return
    # Downloading the data from Yahoo with a timeout of 10 seconds.
    dload = yf.download(ticker, 
            start=start_d, 
            end=end_d, 
            progress=True, timeout=10)
    dload['AssetID'] = isin
    dload['Currency'] = currency
    li = []
    df = pd.DataFrame(dload)
    print(df)
    try:
        for i, x in df.groupby(df.index.year):
            isin_file = isin_dir + isin + "_" + str(i) + ".csv"
            x.to_csv(isin_file, header=True)
    except:
        return

def missing_ticker_data(u_id, user_aIDs):
    print("Retrieve missing ticker data")
    myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    asset_files = list(glob.glob(myDir+"assetdata/*.[cC][sS][vV]"))
    asset_list = []
    li = []
    for f in asset_files:
        if any(aID in f for aID in user_aIDs):
            print(f)
            if "_info." in f:
                continue
            else:
                x = os.path.basename(f).split(".")[0].split("_")[0]
                if x not in asset_list:
                    asset_list.append(x)
                li.append(pd.read_csv(f, header=0))
    if len(asset_list) > 0 and len(li) > 0:
        frame = pd.concat(li, axis=0, ignore_index=True)
        for a in asset_list:
            aDF = frame[(frame["AssetID"] == a)]
            last = aDF.sort_values(['Date']).drop_duplicates('Date', keep='last')\
                ['Date'].max()
            isin_data(a, last, u_id)
    return

def in_list(citem, clist):
    for a in clist:
        if citem[0] == a[0]:
            return True
    return False

# Get filesystem information for a file
def getFileTimestamp(File):
    ftime = os.popen("ls -la "+File).read()
    ftime = ftime.replace("\n",'')
    return ftime

def ffdm_version(myDir):
    tmpPath = myDir + "/*.[pP][yY]"
    tmpFiles = list(glob.glob(tmpPath))
    ts = datetime.datetime(2019, 1, 1, 0, 0, 1)
    for f in tmpFiles:
        tmp_ts = datetime.datetime.fromtimestamp(os.path.getmtime(f))
        if tmp_ts > ts:
            ts = tmp_ts
    return str(ts)[:7]