import requests
from bs4 import BeautifulSoup
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
    #return str(datetime.fromtimestamp(os.path.getmtime(filename)))[:16]
    return str(datetime.fromtimestamp(os.path.getmtime(filename)))

def set_date_filename():
    return set_directory() + 'index_data_' + set_time() + '.html'

def set_filename(filename):
    return set_directory() + filename

def retrieve_indices(current_file):

    if not get_filecheckdate(current_file) == set_time():

        print("Retrieving web indices...")
        webheader = "'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/122.0'"
        Browser = "w3m -header " + webheader + " -no-cookie -dump "
        URL = "https://de.marketscreener.com/boerse/indizes/"
        proc = subprocess.Popen(Browser + URL, shell=True, text=True,\
                                stdout=subprocess.PIPE)
        try:
            outs, errs = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()

        with open(current_file, "w") as file:
                file.write(str(outs))

        return True

    else:

        return False

def convert_indices_bs(filename, idx_date):

    soup = BeautifulSoup(open(filename, encoding="utf8"), 'html.parser')

    for match in soup.find_all('div', {'class' : "quotation_table__row__variation"}):
        match.decompose()

    idx_data = []
    idx_divs = soup.find_all('div', {'class' : "quotation_table"})
    for item in idx_divs:
        x = item.find_all('div', {'class' : "quotation_table__row"})
        for y in x:
            if y:
                data = clean_text(y.text).strip()
                row = data.split("        ")
                if len(row) > 1:
                    row.append(idx_date)
                    idx_data.append(row)                    

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
    idx_data = []

    idx_list =['DAX', 'SMI', 'TECDAX', 'NASDAQ', 'Dow', 'S&P']

    for o in outs:
        if o.split()[0].lower() in (item.lower() for item in idx_list):
        #if o[:3] != 'CAC' and o[1:5] != "Euro" and o[1:6] != "INDEX":
            row = o.split('PTS', 1)[0].split()
            if len(row) > 2:
                del row[1]
            row.append(idx_date)
            row[1] = re.sub(r'[^\d,]', '', row[1])
            row[1] = float(row[1].replace(",", "."))
            print(row)
            idx_data.append(row)

    return pd.DataFrame(idx_data, columns=["ind_title", "ind_num", "ind_date"])

def get_indices():

    current_file = set_filename('index_data.html')
    
    weekday_num = date.today().weekday()
    
    if weekday_num < 5:
        new = retrieve_indices(current_file)
    else:
        new = False

    current_ind = convert_indices(current_file, get_filedate(current_file))

    datafile = set_directory() + "indices.csv"
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

    today = date.today()
    yesterday = today - timedelta(days = 1)
    lastyear = today - timedelta(days = 365)

    past_df = indDF[indDF['ind_date'].dt.strftime('%Y-%m-%d').between(str(lastyear), str(yesterday))] 
    prev_ind = past_df[past_df['ind_date'] == past_df['ind_date'].max()].copy()
    if len(prev_ind) < 1:
        today_df = indDF[indDF['ind_date'].dt.strftime('%Y-%m-%d').between(str(today), str(today))] 
        prev_ind = today_df[today_df['ind_date'] == today_df['ind_date'].min()].copy()

    current_ind = indDF[indDF['ind_date'] == indDF['ind_date'].max()].copy()
    if len(prev_ind) > 0:
        current_ind['prev_num'] = prev_ind['ind_num'].values

        current_ind['ind_diff'] = round((current_ind['ind_num'] - \
            current_ind['prev_num']) / current_ind['prev_num'] * 100, 2)

    else:
        current_ind['ind_diff'] = 0

    current_ind['ind_date'] = current_ind['ind_date'].map(str)
    
    print(prev_ind)
    print()
    print(current_ind)

    return current_ind

get_indices()
