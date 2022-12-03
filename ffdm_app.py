import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
import io
import os
import subprocess
import glob
import sys
import datetime
import time
import csv
import locale
import pandas as pd
import numpy as np
import configparser
import init_db as init_run

# Import config data
# Set default variables including database parameters
myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
config = configparser.ConfigParser()
config.sections()
config.read(myDir + 'ffdm.ini')
DB=config['DB']['DB']
dataDir=config['Accounts']['Dir']
serverPort=int(config['Server']['Port'])
serverName=config['Server']['Name']
DefaultCurrency=config['Accounts']['DefaultCurrency']
    
def get_db_connection():
    try:
        conn = sqlite3.connect(myDir + DB)
        conn.row_factory = sqlite3.Row
        return conn
    except:
        return None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DM4g7th2Juz1'
app.config["TEMPLATES_AUTO_RELOAD"] = True
locale.setlocale(locale.LC_ALL, 'de_DE.utf-8')

@app.route('/assets', methods=('GET', 'POST'))
def assets():
    try:
        assetsDF = pd.read_csv(myDir+"initdata/AssetReferences.csv", \
                            sep=';')
        assetsDF = assetsDF.sort_values(by=['AssetType','AssetName'], ascending=True)
    except:
        return redirect(url_for('error'))
    
    if request.method == 'POST':
        requestDF = pd.DataFrame()
        assets_data = request.form.to_dict(flat=False)
        for a in assets_data:
            column = []
            for value in assets_data[a]:
                if len(str(value)) > 0:
                    column.append(value)
                else:
                    column.append("None")
            requestDF[a] = column
        requestDF = requestDF[requestDF['AssetID'].str.len() > 0]

        if len(requestDF) < 1:
            flash('Error!')
        else:
            requestDF.to_csv(myDir+"initdata/AssetReferences.csv", sep=';', \
                index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('assets'))

    return render_template('assets.html', assets=assetsDF, serverName=serverName)

@app.route('/inita', methods=('GET', 'POST'))
def inita():
    try:
        accountsDF = pd.read_csv(myDir+"initdata/Accounts.csv", \
                            sep=';')
        accountsDF['EntryDate'] = pd.to_datetime(accountsDF['EntryDate']).dt.date
        try:
            accountsDF['Amount'] = accountsDF['Amount']\
                    .str.replace(",", ".").astype(float)
        except:
            accountsDF['Amount'] = accountsDF['Amount']\
                    .astype(float)            
    except:
        return redirect(url_for('error'))
    
    if request.method == 'POST':

        requestDF = pd.DataFrame()
        init_data = request.form.to_dict(flat=False)
        for a in init_data:
            column = []
            for value in init_data[a]:
                if len(str(value)) > 0:
                    column.append(value)
                else:
                    column.append("None")
            requestDF[a] = column
        requestDF = requestDF[((requestDF['Bank'] != "None") & \
            (requestDF['EntryDate'] != "None") & \
            (requestDF['Amount'] != "None") & \
            (requestDF['Reference'] != "None") & \
            (requestDF['AccountNr'] != "None"))]
        requestDF['EntryDate'] = pd.to_datetime(requestDF['EntryDate'])\
                            .dt.strftime("%d.%m.%y")
        requestDF['Amount'] = requestDF['Amount'].astype(float)\
                            .map('{:.2f}'.format).str.replace(".", ",", regex=False)

        if len(requestDF) < 1:
            flash('Error!')
        else:
            requestDF.to_csv(myDir+"initdata/Accounts.csv", sep=';', \
                            index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('inita'))

    return render_template('inita.html', accounts=accountsDF, serverName=serverName)

@app.route('/initd', methods=('GET', 'POST'))
def initd():
    try:
        depotsDF = pd.read_csv(myDir+"initdata/Depots.csv", \
                            sep=';')
        try:
            depotsDF['AssetAmount'] = depotsDF['AssetAmount']\
                    .str.replace(",", ".").astype(float)
            depotsDF['AssetBuyPrice'] = depotsDF['AssetBuyPrice']\
                    .str.replace(",", ".").astype(float)
        except:
            depotsDF['AssetAmount'] = depotsDF['AssetAmount']\
                    .astype(float)            
            depotsDF['AssetBuyPrice'] = depotsDF['AssetBuyPrice']\
                    .astype(float)
    except:
        return redirect(url_for('error'))
    
    if request.method == 'POST':

        requestDF = pd.DataFrame()
        init_data = request.form.to_dict(flat=False)
        for a in init_data:
            column = []
            for value in init_data[a]:
                if len(str(value)) > 0:
                    column.append(value)
                else:
                    column.append("None")
            requestDF[a] = column
        requestDF = requestDF[((requestDF['BankRef'] != "None") & \
            (requestDF['AssetAmount'] != "None") & \
            (requestDF['BankRef'] != "None") & \
            (requestDF['AssetID'] != "None"))]
        requestDF['AssetAmount'] = requestDF['AssetAmount']\
                            .str.replace(".", ",", regex=False)
        requestDF['AssetBuyPrice'] = requestDF['AssetBuyPrice'].astype(float)\
                            .map('{:.2f}'.format).str.replace(".", ",", regex=False)

        if len(requestDF) < 1:
            flash('Error!')
        else:
            requestDF.to_csv(myDir+"initdata/Depots.csv", sep=';', \
                            index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('initd'))

    return render_template('initd.html', depots=depotsDF, serverName=serverName)

@app.route('/vlplans', methods=('GET', 'POST'))
def vlplans():
    try:
        vlplansDF = pd.read_csv(myDir+"initdata/VLplans.csv", \
                            sep=';')
        try:
            vlplansDF['Amount'] = vlplansDF['Amount']\
                    .str.replace(",", ".").astype(float)
        except:
            vlplansDF['Amount'] = vlplansDF['Amount']\
                    .astype(float)            
    except:
        return redirect(url_for('error'))

    if request.method == 'POST':
        
        requestDF = pd.DataFrame()
        vlplans_data = request.form.to_dict(flat=False)
        for a in vlplans_data:
            column = []
            for value in vlplans_data[a]:
                column.append(value)
            requestDF[a] = column
        requestDF = requestDF[requestDF['AssetID'].str.len() > 0]

        if len(requestDF) < 1:
            flash('Error!')
        else:
            print()
            requestDF.to_csv(myDir+"initdata/VLplans.csv", sep=';', \
                            index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('vlplans'))

    return render_template('vlplans.html', vlplans=vlplansDF, serverName=serverName)

@app.route('/settings', methods=('GET', 'POST'))
def settings():
    try:
        myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
        config = configparser.ConfigParser()
        config.sections()
        config.read(myDir + "ffdm.ini")
        confdatf = pd.DataFrame(config.items('Filter'), columns=['Param', 'Setting'])
        confdatf['Section'] = 'Filter'
        confdata = pd.DataFrame(config.items('Server'), columns=['Param', 'Setting'])
        confdata['Section'] = 'Server'
        confdat = pd.concat([confdatf, confdata])
        confdata = pd.DataFrame(config.items('Accounts'), columns=['Param', 'Setting'])
        confdata['Section'] = 'Accounts'
        confdat = pd.concat([confdat, confdata])
    except:
        return redirect(url_for('error'))

    if request.method == 'POST':
        
        requestDF = pd.DataFrame()
        form_data = request.form.to_dict(flat=False)
        for a in form_data:
            column = []
            for value in form_data[a]:
                column.append(value)
            requestDF[a] = column

        if len(requestDF) < 1:
            flash('Error!')
        else:
            myDir = os.path.abspath(os.path.dirname(__file__)) + '/'
            config = configparser.ConfigParser()
            config.sections()
            config.read(myDir + 'ffdm.ini')
            for crow in requestDF.iterrows():
                config.set(crow[1][0], crow[1][1], crow[1][2].replace('%','%%'))
            with open(myDir + 'ffdm.ini', 'w') as configfile:
                config.write(configfile)
            configfile.close()

            return redirect(url_for('settings'))

    return render_template('settings.html', confdat=confdat, serverName=serverName)

@app.route('/acc')
def acc():
    try:
        subprocess.run(["python3 ffdm.py -f"], shell=True, check=True)
    except:
        return redirect(url_for('error'))

    return redirect(request.referrer)

@app.route('/web')
def web():
    try:
        subprocess.run(["python3 ffdm.py -w"], shell=True, check=True)
    except:
        return redirect(url_for('error'))

    return redirect(request.referrer)

@app.route('/unlock')
def unlock():
    try:
        subprocess.run(["python3 ffdm.py -u"], shell=True, check=True)
    except:
        return redirect(url_for('error'))
        
    return redirect(request.referrer)

@app.route('/targets', methods=('GET', 'POST'))
def targets():
    try:
        assetsDF = pd.read_csv(myDir+"initdata/TargetPrices.csv", \
                            sep=';')
        asset_cols = list(assetsDF.columns)
        namesDF = pd.read_csv(myDir+"initdata/AssetReferences.csv", \
                            sep=';')
        conn = get_db_connection()
        prices = conn.execute('SELECT qWatchlist.AssetID, qWatchlist.AssetName, \
                            qWatchlist.LastPrice FROM qWatchList').fetchall()
        conn.close()
        pricesDF = pd.DataFrame(prices, columns=['AssetID', 'AssetName', 'AssetPrice'])
        assetsDF['AssetName'] = assetsDF['AssetID']\
                    .map(pricesDF.set_index('AssetID')['AssetName'])
        assetsDF['LastPrice'] = assetsDF['AssetID']\
                    .map(pricesDF.set_index('AssetID')['AssetPrice'])
        assetsDF = assetsDF.sort_values(by=['AssetName'], ascending=True)
    except:
        return redirect(url_for('error'))
    
    if request.method == 'POST':

        requestDF = pd.DataFrame()
        assets_data = request.form.to_dict(flat=False)
        for a in assets_data:
            column = []
            for value in assets_data[a]:
                column.append(value)
            if a in asset_cols:
                requestDF[a] = column
        
        requestDF[['TargetPriceLow', 'TargetPriceHigh']] = \
            requestDF[['TargetPriceLow', 'TargetPriceHigh']].fillna(0)
        requestDF.loc[requestDF["Currency"] == "None", "Currency"] = DefaultCurrency
        requestDF.loc[requestDF["Currency"] == "", "Currency"] = DefaultCurrency
        requestDF.loc[requestDF["TargetPriceLow"] == "", "TargetPriceLow"] = 0
        requestDF.loc[requestDF["TargetPriceHigh"] == "", "TargetPriceHigh"] = 0
        requestDF[['Currency']] = requestDF[['Currency']].fillna(DefaultCurrency)

        if len(requestDF) < 1:
            flash('Error!')
        else:
            requestDF.to_csv(myDir+"initdata/TargetPrices.csv", sep=';', \
                index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('targets'))

    return render_template('targets.html', assets=assetsDF, serverName=serverName)

@app.route('/split', methods=('GET', 'POST'))
def split():
    try:
        conn = get_db_connection()
        assets = conn.execute('SELECT AssetID, AssetName \
                            FROM qWatchList ORDER BY AssetID \
                            COLLATE NOCASE ASC;').fetchall()
        conn.close()
    except Exception as e:
        print(e)
        return redirect(url_for('error'))

    if request.method == 'POST':

        requestDF = pd.DataFrame()
        assets_data = request.form.to_dict(flat=False)
        for a in assets_data:
            column = []
            for value in assets_data[a]:
                column.append(value)
            requestDF[a] = column
        
        apricesDF = pd.read_csv(myDir+"initdata/AssetPrices.csv", \
                            sep=';')
        apricesDF['PriceTime'] = pd.to_datetime(apricesDF['PriceTime'])
        for i, asset in requestDF.iterrows():
            if str(asset['Split']) != "1":
                apricesDF['AssetPrice'] = \
                apricesDF['AssetPrice'].mask(((apricesDF['PriceTime'] <= \
                datetime.datetime.strptime(str(asset['SplitDate'][:19]), \
                "%Y-%m-%d %H:%M:%S")) & (apricesDF['AssetID'] == asset['AssetID'])), \
                apricesDF['AssetPrice'] / float(asset['Split']))
        apricesDF.to_csv(myDir+"initdata/AssetPrices.csv", \
                            sep=';', index = False)
        try:
            subprocess.run(["python3 ffdm.py -f"], shell=True, check=True)
        except:
            return redirect(url_for('error'))
                
        if len(requestDF) < 1:
            flash('Error!')
        else:
            return redirect(url_for('split'))

    return render_template('split.html', assets=assets, serverName=serverName)

@app.route('/watchlist')
def watchlist():
    try:
        conn = get_db_connection()
        watchlist = conn.execute('SELECT * FROM qWatchlist WHERE AssetID NOT IN \
                (SELECT AssetID FROM qDepotOverview) ORDER BY Delta DESC')\
                .fetchall()
        investlist = conn.execute('SELECT * FROM qWatchlist WHERE AssetID IN \
                (SELECT AssetID FROM qDepotOverview) ORDER BY Delta DESC')\
                .fetchall()
        conn.close()
    except:
        return redirect(url_for('error'))
    return render_template('watchlist.html', watchlist=watchlist, \
                            investlist=investlist, serverName=serverName)

@app.route('/') 
def index():
    return render_template('index.html', serverName=serverName)

@app.route('/error') 
def error():
    return render_template('error.html', serverName=serverName)

@app.route('/finance')
def finance():
    try:
        conn = get_db_connection()
        overview = conn.execute('SELECT * FROM qOverview ORDER BY Slice DESC')\
                    .fetchall()
        monthly = conn.execute('SELECT * FROM qMonthly ORDER BY Year DESC')\
                    .fetchall()
        yearly = conn.execute('SELECT * FROM qYearly ORDER BY Year DESC')\
                    .fetchall()
        cumyear = conn.execute('SELECT * FROM qCumulative ORDER BY Year DESC')\
                    .fetchall()
        spend = conn.execute('SELECT * FROM qSpending ORDER BY Year DESC')\
                    .fetchall()
        quarterly = conn.execute('SELECT * FROM qQuarterly ORDER BY Quarter DESC')\
                    .fetchall()
        perf = conn.execute('SELECT * FROM qPerformance')\
                    .fetchall()
        usd = conn.execute('SELECT * FROM qUSDValues')\
                    .fetchall()
        balance = conn.execute('SELECT * FROM qAccountBalances WHERE Amount > 0 '+ \
                            ' ORDER BY Bank').fetchall()
        depot = conn.execute('SELECT * FROM qDepotOverview '+ \
                            ' ORDER BY Value DESC').fetchall()
        conn.close()
        return render_template('finance.html', overview=overview, monthly=monthly, \
                            perf=perf, usd=usd, balance=balance, depot=depot, \
                            yearly=yearly, cumyear=cumyear, spend=spend, \
                            quarterly=quarterly, serverName=serverName)
    except:
        return redirect(url_for('error'))

@app.context_processor
def my_utility_processor():

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
        return str(locale.format_string(\
                '%.1f', round(number,1),1))

    def format_dec(number):
        return str(locale.format_string(\
                '%.0f', round(number,0),1))

    def format_eur(number):
        return str(locale.format_string(\
                '%.2f', round(number,2),1))

    def format_shares(number):
        if (number % 1) > 0 and number < 1:
            pcs = str(locale.format_string('%.3f', number,2))
        elif (number % 1) > 0 and number > 1 and number < 10:
            pcs = str(locale.format_string('%.2f', number,2))
        elif (number % 1) > 0 and number >= 10:
            pcs = str(locale.format_string('%.1f', number,2))
        else:
            pcs = str(locale.format_string('%.0f', number,1))
        return pcs

    def get_time():
        try:    
            conn = get_db_connection()
            DataDate = conn.execute('SELECT PriceTime FROM AssetPrices ORDER BY PriceTime \
                        DESC LIMIT 1').fetchall()
            dtime = str(DataDate[0][0]).replace(' ', ' / ')[:18]
            conn.close()
            return dtime
        except:
            return "No time..."

    def get_lastupdtime():
        try:    
            conn = get_db_connection()
            DataDate = conn.execute('SELECT PriceTime FROM AssetPrices ORDER BY PriceTime \
                        DESC LIMIT 1').fetchall()
            dtime = str(DataDate[0][0])
            conn.close()
            return dtime
        except:
            return "No time..."

    def get_prices(AssetID):
        try:    
            conn = get_db_connection()
            prices = conn.execute('SELECT AssetID, PriceTime, AssetPrice \
                        FROM AssetPrices WHERE AssetID="' + AssetID + '"GROUP BY \
                        PriceTime ORDER BY PriceTime DESC LIMIT 100').fetchall()
            conn.close()
            return prices
        except Exception as e:
            print(e)
            return []

    return dict(format_snumber=format_snumber, format_number=format_number,\
                format_percent=format_percent, format_dec=format_dec,\
                format_eur=format_eur, format_shares=format_shares, get_time=get_time, 
                get_prices=get_prices, get_lastupdtime=get_lastupdtime)

@app.errorhandler(404) 
def invalid_route(e): 
    return "Invalid route."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=serverPort)

