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
                +" | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]{0,3}\.)?"\
                +"[[:digit:]]{1,3},[[:digit:]]{2}EUR' | " \
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

# Links for ariva.de
def get_Ref2_data(a_type, a_id, refFnet):
    link = ""
    link = "https://www.ariva.de/" + refFnet \
            +" | grep -m 1 '[0-9] €' | grep -o [0-9.,]* | head -1"
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
def get_Ref1_data(a_type, a_id, refARD):
    link = "https://www.tagesschau.de/wirtschaft/boersenkurse/"\
            +"suche/?suchbegriff="
    extract = ""
    if a_type == "COM":
        extract = " | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{2}' | grep -o [0-9.,]*$"
    if a_type == "CUR" and a_id == "USD":
        extract = " | grep -E -m1 '([[:digit:]]{0,3}\.)?([[:digit:]]"\
        +"{0,3}\.)?[[:digit:]]{1,3},[[:digit:]]{4}' | grep -o [0-9.,]*$"
    if a_type == "CRP" and len(a_id) < 5:
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
    webheader = "'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; rv:110.0)'"
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
    if (refAvailable[0] == True):
        return_price = retrieveWebData(get_Ref0_data(a_type, a_id, refNet0))
    if (abs(old_price-return_price)/old_price > 0.5) and (return_price > 0):
        print("Major difference to old price")
        return_price = -1
    if return_price <= 0:
        print("first service failed...")
        if (refAvailable[1] == True):
            return_price = retrieveWebData(get_Ref1_data(a_type, a_id, refNet1))
    return return_price
