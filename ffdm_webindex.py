import requests
from bs4 import BeautifulSoup as bs
import urllib.request, urllib.parse, urllib.error
import ssl
import os
import time
import re
import subprocess
import shutil
import pandas as pd
from datetime import datetime
from datetime import date
from datetime import timedelta

def clean_text(text):
    cleaned = re.sub(r'[^a-zA-Z0-9.,\s]', '', text)
    return cleaned

def set_directory():
    baseDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    return baseDir + "indices/"

def set_time():
    return datetime.today().strftime('%Y-%m-%d-%H-') + str(int(int(datetime.today().strftime('%M')) / 5))

def get_filecheckdate(filename):
    tempdate = str(datetime.fromtimestamp(os.path.getmtime(filename)))
    datevar = datetime.strptime(tempdate[:16], "%Y-%m-%d %H:%M")
    return str(datevar.strftime('%Y-%m-%d-%H-')) + str(int(int(datevar.strftime('%M')) / 5))

def get_filedate(filename):
    if os.path.exists(filename):
    #return str(datetime.fromtimestamp(os.path.getmtime(filename)))[:16]
        return str(datetime.fromtimestamp(os.path.getmtime(filename)))
    else:
        return "0"

def set_date_filename():
    return set_directory() + 'index_data_' + set_time() + '.html'

def set_filename(filename):
    return set_directory() + filename

def retrieve_indices(current_file):

    update_required = False

    try:
        if not get_filecheckdate(current_file) == set_time():
            update_required = True
    except:
        pass

    if not os.path.exists(current_file):
        update_required = True

    print(update_required)

    if update_required:

        print("Retrieving web indices...")
        url = 'https://de.marketscreener.com/boerse/indizes/'
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1) AppleWebKit/534.23.7 (KHTML, like Gecko) Version/4.0.5 Safari/534.23.7',
        }
        # Get HTML Content
        proxies = { 'http': "http://174.137.134.182:2999",
                'https': "http://174.137.134.182:2999"}

        proxy = "128.140.113.110:8080"
        proxy = "154.197.75.25:80"

        proxies = { 'http': proxy,
                'https': proxy}

        #r = requests.get(url, headers=header, proxies=proxies)

        session = requests.Session()
        r = session.get(url, headers=header, timeout=10)

        #html = urllib.request.urlopen(url, context=ctx).read()

        #soup = bs(html, 'html.parser')
        print("Status", r.status_code)
        if r.status_code == 200:
            #soup = bs(r.content, 'html.parser')
            #print(soup)

            #webheader = "'User-Agent:Mozilla/5.0 (X11; Linux x86_64; rv:151.0) Gecko/20100101 Firefox/151.0'"
            #Browser = "w3m -header " + webheader + " -no-cookie -dump "
            #URL = "https://de.marketscreener.com/boerse/indizes/"
            #proc = subprocess.Popen(Browser + URL, shell=True, text=True,\
            #                        stdout=subprocess.PIPE)
            #try:
            #    outs, errs = proc.communicate(timeout=10)
            #except subprocess.TimeoutExpired:
            #    proc.kill()
            #    outs, errs = proc.communicate()

            with open(current_file, "w") as file:
                    file.write(str(r.content).replace('\\n', ''))

        return True

    else:

        return False

def convert_indices_bs(filename, idx_date):

    if idx_date == "0":
        retrieve_indices(filename)

    with open(filename, 'r', encoding="utf8") as file:
        html_file = file.read()

    soup = bs(html_file, 'html.parser')

    idx_data = []
    name_dat = []
    #idx_divs = soup.find_all('div', {'class' : "quotation_table"})
    idx_divs = soup.find_all('div', {'class' : "card-content table-responsive"})
    #print(idx_divs)
    iteration = 0
    ind_name = soup.find_all('a', {'class' : "link link--blue"})
    #print(ind_name)
    for i in ind_name:
        if i:
            data = clean_text(i.text).strip()
            name = data.split("        ")
            name_dat.append(name[0])

    idx_list =['DAX', 'SMI', 'TECDAX', 'NASDAQ', 'DOW', 'S&P']

    for item in idx_divs:
        #print(item)
        #x = item.find_all('a', {'class' : "last c-inline h-100 last--no-pad px-5"})
        x = item.find_all(class_ = "last c-inline h-100 last--no-pad px-5")
        #x = item.find_all('a', {'class' : "link link--blue"})
        for y in x:
            #print(y)
            if y:
                data = clean_text(y.text).strip()
                row = data.split("        ")
                #print(row)
                if len(row) > 0:
                    curr_name = name_dat[iteration]
                    if str(curr_name) == "INDUSTRIAL":
                        curr_name = "Dow"
                    if str(curr_name) == "DOW":
                        curr_name = "Dow"
                    if str(curr_name) == "DOW JONES INDUSTRIAL":
                        curr_name = "Dow"
                    if str(curr_name) == "SP 500":
                        curr_name = "S&P"
                    if str(curr_name) == "NASDAQ 100":
                        curr_name = "NASDAQ"

                    if curr_name.lower() in (item.lower() for item in idx_list):
                        row.insert(0, curr_name)
                        row.append(idx_date)
                        if len(str(row[1])) > 0:
                            row[1] = float(row[1].replace(".", "").replace(",", "."))
                        else:
                            row[1] = float( "0")
                        #print(row)
                        idx_data.append(row)
                    iteration += 1

    print(idx_data)
    return pd.DataFrame(idx_data, columns=["ind_title", "ind_num", "ind_date"])

def convert_indices(filename, idx_date):
    cmd = "cat " + filename + " | grep -A 24 Name | grep PTS"

    proc = subprocess.Popen(cmd, shell=True, text=True,\
                            stdout=subprocess.PIPE)
    try:
        outs, errs = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()

    outs = outs.replace('Index','').splitlines()
    #print(outs)
    idx_data = []

    idx_list =['DAX', 'SMI', 'TECDAX', 'NASDAQ', 'DOW', 'S&P']

    for o in outs:
        if o.split()[0].lower() in (item.lower() for item in idx_list):
        #if o[:3] != 'CAC' and o[1:5] != "Euro" and o[1:6] != "INDEX":
            row = o.split('PTS', 1)[0].split()
            if len(row) > 2:
                del row[1]
            row.append(idx_date)
            row[1] = re.sub(r'[^\d,]', '', row[1])
            if len(str(row[1])) > 0:
                row[1] = float(row[1].replace(",", "."))
            else:
                del row[1]
                row[1] = re.sub(r'[^\d,]', '', row[1])
                row[1] = float(row[1].replace(",", "."))

            if str(row[0]) == "INDUSTRIAL":
                row[0] = "Dow"
            if str(row[0]) == "DOW":
                row[0] = "Dow"

            idx_data.append(row)
    
    print(idx_data)
    return pd.DataFrame(idx_data, columns=["ind_title", "ind_num", "ind_date"])

def get_indices():

    current_file = set_filename('index_data.html')
    datafile = set_directory() + "indices.csv"
    today = date.today()
    last_update = pd.DataFrame()

    if os.path.exists(datafile):
        indDF = pd.read_csv(datafile, sep=';')
        indDF['ind_date'] = pd.to_datetime(indDF['ind_date'])
        print(indDF)
        last_update = indDF[indDF['ind_date'].dt.strftime('%Y-%m-%d').between(str(today), str(today))] 
   
    weekday_num = date.today().weekday()
    
    if weekday_num < 5 or len(last_update) < 1:
        new = retrieve_indices(current_file)
    else:
        new = False

    #current_ind = convert_indices(current_file, get_filedate(current_file))
    current_ind = convert_indices_bs(current_file, get_filedate(current_file))

    if new == True:
        if os.path.exists(datafile):
            indDF = pd.read_csv(datafile, sep=';')
            indDF = pd.concat([indDF, current_ind])
            indDF.to_csv(datafile, sep=';', index=False) 
        else:
            indDF = current_ind
            indDF.to_csv(datafile, sep=';', index=False) 
    else:
        if os.path.exists(datafile):
            indDF = pd.read_csv(datafile, sep=';')
        else:
            indDF = current_ind
            indDF.to_csv(datafile, sep=';', index=False) 

    indDF['ind_date'] = pd.to_datetime(indDF['ind_date'])
    prev_date = indDF['ind_date'].drop_duplicates().nlargest(2).iloc[-1]
    prev_ind = indDF[indDF['ind_date'] == prev_date].copy()

    yesterday = today - timedelta(days = 1)
    lastyear = today - timedelta(days = 365)

    past_df = indDF[indDF['ind_date'].dt.strftime('%Y-%m-%d').between(str(lastyear), str(yesterday))] 
    prev_ind = past_df[past_df['ind_date'] == past_df['ind_date'].max()].copy()
    if len(prev_ind) < 1:
        today_df = indDF[indDF['ind_date'].dt.strftime('%Y-%m-%d').between(str(today), str(today))] 
        prev_ind = today_df[today_df['ind_date'] == today_df['ind_date'].min()].copy()

    current_ind = indDF[indDF['ind_date'] == indDF['ind_date'].max()].copy()
    if len(prev_ind) > 0:
        try:
            current_ind['prev_num'] = prev_ind['ind_num'].values

            current_ind['ind_diff'] = round((current_ind['ind_num'] - \
                current_ind['prev_num']) / current_ind['prev_num'] * 100, 2)
        except:
            current_ind['ind_diff'] = 0
    else:
        current_ind['ind_diff'] = 0

    current_ind['ind_date'] = current_ind['ind_date'].map(str)
    
    print(prev_ind)
    print()
    print(current_ind)

    return current_ind

get_indices()
#current_file = set_filename('index_data.html')
#print(convert_indices_bs(current_file, get_filedate(current_file)))
