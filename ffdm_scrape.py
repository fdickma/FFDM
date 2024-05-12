import requests
import subprocess
import re
import ffdm_lib as fl

global refAvailable
refAvailable = []

# Check the service to be online
def check_online():
    refAvailable.append(check_url("https://boerse.de"))
    refAvailable.append(check_url("https://tagesschau.de"))
    refAvailable.append(check_url("https://ariva.de"))
    refAvailable.append(check_url("https://alleaktien.de"))

# Check a service to be online
def check_url(url):
    if len(url)<8:
        print("Not a URL...")
        return False

    try:
        page = requests.get(url)
        print(page.status_code)
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
        print("Service not available...")
        return False
    return True

# Alternative data source
def get_Alt_data(a_type, a_id, refFnet):
    link = ""
    if a_type == "STK":
        link = refFnet + " | grep Kurs | grep -o '[0-9.,]* €'"
    if link != "":
        return link
    else:
        return 0

# Links for ariva.de
def get_Ref2_data(a_type, a_id, refFnet):
    link = ""
    if a_type == "COM":
        link = "https://www.ariva.de/" + refFnet \
            +" | grep -m 1 '[0-9] €' | grep -o [0-9.,]* | head -1"
    elif a_type == "CRP" and a_id == "BTC":
        link = "https://www.coinbase.com/de/converter/btc/eur" \
            +" | grep -m 1 'entspricht' | grep -m 1 -o '[0-9.]*,[0-9]*'"
    elif a_type == "CRP" and a_id == "ETH":
        link = "https://www.coinbase.com/de/converter/eth/eur" \
            +" | grep -m 1 'entspricht' | grep -m 1 -o '[0-9.]*,[0-9]*'"
    else:
        link = "https://www.ariva.de/" + a_id \
            +" | grep -m 1 '[0-9] €' | grep -o [0-9.,]* | head -1"
    if link != "":
        return link
    else:
        return 0

# Links for ariva.de
def get_Ref3_data(a_type, a_id, refFnet):
    link = ""
    link = "https://www.alleaktien.de/data/" + a_id \
            +" | grep -m 1 ' EUR' | grep -o [0-9.,]* | head -1"
    if link != "":
        return link
    else:
        return 0

# Links for boerse.de
def get_Ref0_data(a_type, a_id, refFnet):
    link = ""
    link = "https://boerse.de/wertpapier/" \
         + a_id +" | grep -m 1 '[0-9] EUR' | grep -o [0-9.,]* | head -1"
    if link != "":
        return link
    else:
        return 0

# Links for ard-Boerse
def get_ARD_data(a_type, a_id):
    link = "https://www.tagesschau.de/wirtschaft/boersenkurse/"\
            +"suche/?suchbegriff="
    extract = ""
    if a_type == "COM":
        extract = r" | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +r"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{2}' | grep -o [0-9.,]*$"
    if a_type == "CUR" and a_id == "USD":
        link = "https://www.tagesschau.de/wirtschaft/boersenkurse/eu0009652759-25108390/"
        extract = r" | grep '[$]' | grep Kurs | grep -o [0-9,.]*"
        return link + extract
    if a_type == "CRP" and len(a_id) < 5:
        extract = r" | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +r"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{2}' | grep -o [0-9.,]*$"
    if a_type == "FND" or a_type == "ETF" or a_type == "STK":
        extract = r" | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +r"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{2}' | grep -o [0-9.,]*$"
    if extract != "":
        return link + a_id + extract
    else:
        return 0

def retrieveWebData(link):
    webheader = "'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'"
    Browser = "w3m -header " + webheader + " -no-cookie -dump "
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
def assetDataScraping(asset, old_price):
    return_price=-1
    a_type = asset['AssetType']
    a_id = asset['AssetID'] 
    refNet0 = asset['NetRef1']
    refNet1 = asset['NetRef2']
    if return_price <= 0 and a_id[:2] == 'CH':
        print("Checking alternative first")
        return_price = retrieveWebData(get_Alt_data(a_type, a_id, refNet0))
    if (refAvailable[2] == True) and (return_price <= 0):
        return_price = retrieveWebData(get_Ref2_data(a_type, a_id, refNet1))
    print(a_id, return_price, ' -- Old:', old_price)
    if (old_price > 0):
        if (abs(old_price-return_price)/old_price > 0.5) and (return_price > 0):
            print("Major difference to old price")
            return_price = -1
    if return_price <= 0:
        print("first service failed...")
        if (refAvailable[1] == True):
            return_price = retrieveWebData(get_ARD_data(a_type, a_id))
    if (old_price > 0):
        if (abs(old_price-return_price)/old_price > 0.5) and (return_price > 0):
            print("Major difference to old price")
            return_price = -1
    if return_price <= 0:
        print("second service failed...")
        if (refAvailable[3] == True):
            return_price = retrieveWebData(get_Ref3_data(a_type, a_id, refNet1))
    return return_price
