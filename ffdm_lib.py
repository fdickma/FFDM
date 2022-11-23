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
import configparser

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

    vlplans = connection.execute("SELECT * FROM VLplans ORDER BY PlanID").fetchall()
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
             '\"([A-Za-z0-9]*)\"\;'            # Konto.
             '\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Wertstellung.
             '\"(.*)\"\;'                      # Bezeichnung.
             '\"([-\d.]*\,\d*)\"\;'            # Betrag (EUR).
             '\"(.*)\"\n')                     # Waehrung.             
        p_init_assets = re.compile(
            r'\"([A-Za-z0-9]{3,10})\"\;'       # Bank.
             '\"([A-Za-z0-9]*)\"\;'            # Konto.
             '\"([A-Za-z0-9]*)"\;'             # WKN/ISIN.
             '\"(.*)\"\;'                      # Bezeichnung.
             '\"([\d.]*\,\d*)\"\;'             # Stück.
             '\"([-\d.]*\,\d*)\";'             # Betrag (EUR).
             '\"(.*)\"\n')                     # Waehrung.             
        p_dkb_depot = re.compile(
            r'\"([\d.]*\,\d*)\"\;'             # Bestand.
             '"Stück"\;'                       # Stück.
             '\"([A-Za-z0-9]{6,12})\"\;'       # ISIN/WKN.
             '\"(.*)\"\;'                      # Bezeichnung.
             '\"(.*)\"\;'                      # Kurs.
             '\"(.*)\"\;'                      # Gewinn/Verlust.
             '".*"\;'                          # "".
             '\"(.*)\"\;'                      # Einstandskurs.
             '".*"\;".*"\;'                    # ""; Dev. Kurs.
             '\"(.*)\"\;'                        # "Kurswert in Euro".
             '\"Frei\"\;')                     # Konto Gegenbuchung.
        p_dkb_cash = re.compile(
            r'\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Buchungstag.
             '\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Wertstellung.
             '\"(.*)\"\;'                      # Buchungstext.
             '\"(.*)\"\;'                      # Auftraggeber / Begünstigter.  
             '\"(.*)\"\;'                      # Verwendungszweck.
             '\"([A-Za-z0-9]*)\"\;'            # Kontonummer.
             '\"([A-Za-z0-9]*)\"\;'            # BLZ.
             '\"([-\d.]*\,\d*)\"\;'            # Betrag (EUR).
             '\"(.*)\"\;'                      # Gläubiger-ID.
             '\"(.*)\"\;'                      # Mandatsreferenz.
             '\"(.*)\"\;')                     # Kundenreferenz.
        p_dkb_visa = re.compile(
            r'\"(Ja|ja|Nein|nein|NEIN|JA)\"\;' # Umsatz abgerechnet.
             '\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Wertstellung.
             '\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Belegdatum.
             '\"(.*)\"\;'                      # Beschreibung.
             '\"([-\d.]*\,\d*)\"\;'            # Betrag (EUR).
             '\"(.*)\"\;')                     # Ursprünglicher Betrag.
        p_spk = re.compile(
            r'\"([A-Za-z0-9]*)"\;'             # Auftragskonto.
             '\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Buchungstag.
             '\"(\d{2}\.\d{2}\.\d{2,4})\"\;'   # Valutadatum.
             '\"(.*)\"\;'                      # Buchungstext.
             '\"(.*)\"\;'                      # Verwendungszweck.
             '\"(.*)\"\;'                      # Beguenstigter.
             '\"([A-Za-z0-9]*)\"\;'            # Kontonummer.
             '\"([A-Za-z0-9]*)\"\;'            # BLZ.
             '\"([-\d.]*\,\d*)\"\;'            # Betrag.
             '\"(.*)\"\;'                      # Waehrung.
             '\"(.*)\"')                       # Info.
        p_dkb_account = re.compile(
            r'\"([A-Za-z]*\:)\"\;'
             '\"([A-Za-z]{2}[0-9]*|'
             '[0-9]{4}[\*]{8}[0-9]{4}|'
             '[0-9]*).*[A-Za-z]*'
             '(.*)\"\;')
        
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
        #print(chn)
        config.set(chn[0], chn[1], chn[2].replace('%','%%'))
    #print(config.items(section))
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
