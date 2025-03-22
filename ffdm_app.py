from flask import Flask, render_template, request, url_for, flash, redirect, g, session
from werkzeug.exceptions import abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from fileinput import filename
from werkzeug.utils import secure_filename
import sqlalchemy as sa
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
import bcrypt
import ffdm_lib as fl
import ffdm_init as fi
import init_db as init_run

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

def check_db(dbt, u_id):    
    appdir = os.path.abspath(os.path.dirname(__file__))
    sql_uri = 'sqlite:///' + os.path.join(appdir, 'users/' + u_id + '/ffdm.sqlite')
    engine = sa.create_engine(sql_uri, echo=False) 
    inspector = sa.inspect(engine)
    tables_dbo = inspector.get_table_names()
    if dbt in tables_dbo:
        conn = engine.connect() 
        query = 'SELECT count(*) FROM ' + dbt + ';'
        exe = conn.execute(sa.text(query)) 
        count = exe.scalar()
        return count
    else:
        return 0

def get_db_idxdata():
    idx_db_data = []
    try:
        appdir = os.path.abspath(os.path.dirname(__file__))
        idx_sql_uri = 'sqlite:///' + os.path.join(appdir, 'indexes.sqlite')
        idx_engine = sa.create_engine(idx_sql_uri, echo=False) 
        with idx_engine.connect() as idx_connection:
            idx_db_data = pd.read_sql('SELECT * FROM index_FearAndGreed', idx_connection)
        return idx_db_data
    except:
        return None

def get_myDir(user_id):
    baseDir = os.path.abspath(os.path.dirname(__file__)) + '/'
    return baseDir + 'users/' + user_id + '/'

def get_account_dirs(user_id):
    myDir = get_myDir(user_id)
    user_config = configparser.ConfigParser()
    user_config.sections()
    user_config.read(myDir + 'ffdm.ini')
    accountDir = []

    # Iterating account directory entries
    dir_count = 0
    for cdir in user_config['Accounts']:
        if cdir[:3] == "dat":
            dir_count += 1
            if user_config['Accounts']['dat' + str(dir_count)] != "":
                accountDir.append(user_config['Accounts']['dat' + str(dir_count)])
    return accountDir

def get_account_files(user_id):
    myDir = get_myDir(user_id)
    accountDir = get_account_dirs(user_id)
    # Now generate the files list from the directories
    files_list = []
    for sdir in accountDir:
        files_list.extend(list(glob.glob(myDir + sdir + "/*.[cC][sS][vV]")))
    files_list.sort(key=os.path.getmtime, reverse=True)
    files_list.extend(list(glob.glob(myDir + 'initdata' + "/Accounts.[cC][sS][vV]")))
    #files_list.extend(list(glob.glob(myDir + 'initdata' + "/*.[cC][sS][vV]")))
    return files_list

# The app key is stored separately
baseDir = os.path.abspath(os.path.dirname(__file__)) + '/'
keyconf = configparser.ConfigParser()
keyconf.read(baseDir + 'ffdm.key')

app = Flask(__name__)
# Load the app key
app.config['SECRET_KEY'] = keyconf['Key']['key']
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = True
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
locale.setlocale(locale.LC_ALL, 'de_DE.utf-8')

# The user database is stored separately
appdir = os.path.abspath(os.path.dirname(__file__))
sql_uri = 'sqlite:///' + os.path.join(appdir, 'userdb.sqlite')
app.config["SQLALCHEMY_DATABASE_URI"] = sql_uri
userdb = SQLAlchemy()
login_manager = LoginManager()
login_manager.init_app(app)

# Import config data
# Set default variables including database parameters
config = configparser.ConfigParser()
config.sections()
config.read(baseDir + 'ffdm.ini')
DB=config['DB']['DB']
dataDir=config['Accounts']['Dir']
serverPort=int(config['Server']['Port'])
serverName=config['Server']['Name']
DefaultCurrency=config['Accounts']['DefaultCurrency']

# Secure file uploads
ALLOWED_EXTENSIONS = {'csv'}
UPLOAD_FOLDER = baseDir
# With a max file size of 32 Megabyte
app.config['MAX_CONTENT_LENGTH'] = 32 * 1000 * 1000

# Initialize user database structure
class Users(UserMixin, userdb.Model):
    id = userdb.Column(userdb.Integer, primary_key=True)
    name = userdb.Column(userdb.String(250), unique=True, nullable=False)
    username = userdb.Column(userdb.String(12), unique=True, nullable=False)
    password = userdb.Column(userdb.String(250), nullable=False)

# Initialize the user database
userdb.init_app(app)
with app.app_context():
    userdb.create_all()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_dir(filename):
    return filename[:len(UPLOAD_FOLDER)] == UPLOAD_FOLDER

@login_manager.user_loader
def loader_user(user_id):
    return userdb.session.get(Users, int(user_id))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = Users(name=request.form.get("name"),
                     username=request.form.get("username"),
                     password=request.form.get("password"))
        userdb.session.add(user)
        userdb.session.commit()
        try:
            myDir = baseDir + 'users/' + \
                request.form.get("username") + '/'
            dir1 = myDir+"initdata"
            os.mkdir(myDir)
            os.mkdir(dir1)
        except Exception as e:
            print(e)
            return redirect(url_for('error'))        
    
        return redirect(url_for("login"))
    return render_template("sign_up.html", serverName=serverName)

@app.route('/userpass', methods=["GET", "POST"])
def userpass():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)

    try:
        user = Users.query.filter_by(
            username=current_user.username).first()
        name = user.name
        password = user.password
        username = user.username
        old_username = username

    except Exception as e:
        print(e)
        return redirect(url_for('error'))

    if request.method == "POST":
        upd = (sa.update(Users).where(Users.username ==
                old_username).values(
                     name=request.form.get("name"),
                     username=request.form.get("username"),
                     password=request.form.get("password")))
        userdb.session.execute(upd, 
            execution_options={"synchronize_session": False})
        userdb.session.commit()
        return redirect(url_for("userpass"))
    return render_template("userpass.html", username=username, \
        password=password, name=name, serverName=serverName)

@app.route('/userdelete', methods=["GET", "POST"])
def userdelete():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)

    try:
        user = Users.query.filter_by(
            username=current_user.username).first()
        username = user.username
        name = user.name

    except Exception as e:
        print(e)
        return redirect(url_for('error'))

    if request.method == "POST":
        del_str = sa.delete(Users).where(Users.username == username)
        userdb.session.execute(del_str, 
            execution_options={"synchronize_session": False})
        userdb.session.commit()

        try:
            myDir = baseDir + 'users/' + \
                request.form.get("username") + '/'
            os.system("rm -rf " + myDir)

        except Exception as e:
            print(e)
            return redirect(url_for('error'))

        return redirect(url_for("userdelete"))
    return render_template("userdelete.html", username=username,
            name=name, serverName=serverName)

@app.route("/login", methods=["GET", "POST"])
def login():
    # If a post request was made, find the user by 
    # filtering for the username
    if request.method == "POST":
        user = Users.query.filter_by(
            username=request.form.get("username")).first()
        try:
            # Check if the password entered is the 
            # same as the user's password
            if user.password == request.form.get("password"):
                # Use the login_user method to log in the user
                login_user(user)
                return redirect(url_for("index"))
            # Redirect the user back to the home
        except:
            return redirect(url_for("login"))
    return render_template("login.html", serverName=serverName)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route('/file_upload', methods=["GET", "POST"])
def file_upload():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        myDirs = get_account_dirs(current_user.username)
        myFiles = get_account_files(current_user.username)
    except Exception as e:
        print(e)
    return render_template("file_upload.html", myFiles=myFiles, myDirs=myDirs)  

@app.route('/ack_upload', methods=["POST"])
def ack_upload():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    if request.method == 'POST':
        f = request.files['file']
        if len(f.filename) > 0:
            try:
                if request.form['targetPath'][-3:].upper() == 'CSV':
                    saveName = request.form['targetPath']
                else:
                    saveName = get_myDir(current_user.username) + \
                        request.form['targetPath'] + '/' + f.filename
                if saveName != "":
                    # Double security check
                    if allowed_file(saveName) == True and allowed_dir(saveName) == True:
                        f.save(saveName)
                        return render_template("ack_upload.html", name = saveName)
            except:
                return redirect(url_for('error'))
        else:
            return redirect(url_for('error'))
    return render_template('index.html', serverName=serverName)

# Set long valid session duration
@app.before_request
def before_request():
    session.permanent = True
    # Set 30 days of lifetime
    app.permanent_session_lifetime = datetime.timedelta(minutes=43200)
    session.modified = True
    g.user = current_user

@app.route("/manage_accounts", methods=('GET', 'POST'))
def manage_accounts():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)

    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/AccountRegistry.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            accountRegDF = pd.read_csv(fileName, sep=';')
        else:
            accountRegDF = pd.DataFrame(columns=["Type","Name","Bank","AccountNr","Currency"])
        accountRegDF.loc[len(accountRegDF)] = pd.Series(dtype='float64')
        accountRegDF = accountRegDF.fillna('')
        accountRegDF = accountRegDF.sort_values(by=['Name'])
        atypesDF = pd.read_csv(myDir+"initdata/AccountTypes.csv", sep=';')
    except Exception as e:
        print(e)
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
            myDir = baseDir + 'users/' + '/' + current_user.username + '/'
            requestDF = requestDF.loc[requestDF['Name'] != '']
            requestDF = requestDF.loc[requestDF['Bank'] != '']
            requestDF.to_csv(myDir+"initdata/AccountRegistry.csv", sep=';', \
                header=True, index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('manage_accounts'))
 
    return render_template('manage_accounts.html', accountReg=accountRegDF, \
        currency=DefaultCurrency, atypes=atypesDF, serverName=serverName)

@app.route("/manage_depots")
def manage_depots():
    return redirect(url_for("index"))

@app.route('/assets', methods=('GET', 'POST'))
def assets():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/AssetReferences.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            assetsDF = pd.read_csv(fileName, sep=';')
        else:
            assetsDF = pd.DataFrame(columns=["AssetType","AssetID","AssetName",\
                "Ticker","NetRef1","NetRef2"])
        assetsDF = assetsDF.sort_values(by=['AssetType','AssetName'], ascending=True)
        assetsDF.loc[len(assetsDF)] = pd.Series(dtype='float64')
        assetsDF = assetsDF.fillna('')
        assetTypesDF = pd.read_csv(myDir+"initdata/AssetTypes.csv", sep=';')
    except:
        return redirect(url_for('nodata'))
    
    if request.method == 'POST':
        requestDF = pd.DataFrame()
        assets_data = request.form.to_dict(flat=False)
        for a in assets_data:
            column = []
            empty_col = 0
            for value in assets_data[a]:
                column.append(value)
            requestDF[a] = column
        requestDF = requestDF[requestDF['AssetID'].str.len() > 2]

        if len(requestDF) < 1:
            flash('Error!')
        else:
            for i, asset in requestDF.iterrows():
                if asset['Ticker'] == "None" or asset['Ticker'] == None \
                or len(asset['Ticker']) < 1 or str(asset['Ticker']) == "nan" \
                and len(asset['AssetID']) > 1:
                    print((asset['AssetID']))
                    newTicker = fl.get_ticker(asset['AssetID'], current_user.username)
                    if newTicker is not None:
                        requestDF.loc[(requestDF.AssetID == asset['AssetID']), \
                            'Ticker'] = newTicker

            requestDF.to_csv(myDir+"initdata/AssetReferences.csv", sep=';', \
                index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('assets'))

    return render_template('assets.html', assets=assetsDF, serverName=serverName, \
            assetTypes=assetTypesDF)

@app.route('/edit_accounts', methods=('GET', 'POST'))
def edit_accounts():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)

    today_date = datetime.date.today()
    
    # Read the account registry
    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        accountRegDF = pd.read_csv(myDir+"initdata/AccountRegistry.csv", \
                            sep=';')
        depot_list = ['Depot', 'Wallet']
        accountRegDF = accountRegDF[~accountRegDF['Type'].isin(depot_list)]
        accountRegDF = accountRegDF.sort_values(by=['Name'])
    except:
        return redirect(url_for('nodata'))

    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/Accounts.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            accountsDF = pd.read_csv(fileName, sep=';')
            accountsDF['EntryDate'] = pd.to_datetime(accountsDF['EntryDate'], \
                format="%d.%m.%y").dt.date
        else:
            accountsDF = pd.DataFrame(columns=["Bank","AccountNr","EntryDate",\
                "Reference","Amount","Currency"])
        try:
            accountsDF['Amount'] = accountsDF['Amount']\
                    .str.replace(",", ".").astype(float)
        except:
            accountsDF['Amount'] = accountsDF['Amount']\
                    .astype(float)
        accountsDF.loc[len(accountsDF)] = pd.Series(dtype='float64')
        accountsDF.loc[len(accountsDF) -1, 'EntryDate'] = today_date 
        accountsDF = accountsDF.sort_values(by=['EntryDate', 'AccountNr'], \
            ascending=False, na_position='first')
        accountsDF = accountsDF.fillna('')
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
        requestDF = requestDF[((requestDF['AccountNr'] != "None") & \
            (requestDF['AccountNr'] != "Select Account...") & \
            (requestDF['Amount'] != "None") & \
            (requestDF['Reference'] != "None"))]
        requestDF['EntryDate'] = pd.to_datetime(requestDF['EntryDate'])\
                            .dt.strftime("%d.%m.%y")
        requestDF['Amount'] = requestDF['Amount'].astype(float)\
                            .map('{:.2f}'.format).str.replace(".", ",", regex=False)

        requestDF = requestDF.merge(accountRegDF[["AccountNr", "Bank"]], on=["AccountNr"], how="left")
        requestDF = requestDF[["Bank","AccountNr","EntryDate","Reference","Amount","Currency"]]

        if len(requestDF) < 1:
            flash('Error!')
        else:
            requestDF.to_csv(myDir+"initdata/Accounts.csv", sep=';', \
                            index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('edit_accounts'))

    return render_template('edit_accounts.html', accounts=accountsDF, \
        accountReg=accountRegDF, today_date=str(today_date), serverName=serverName, \
            currency=DefaultCurrency)

@app.route('/edit_depots', methods=('GET', 'POST'))
def edit_depots():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)

    # Read the account registry and assets
    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/AccountRegistry.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            accountRegDF = pd.read_csv(fileName, sep=';')
        else:
            accountRegDF = pd.DataFrame(columns=["Type","Name","Bank","AccountNr","Currency"])

        depot_list = ['Depot', 'Wallet']
        accountRegDF = accountRegDF[accountRegDF['Type'].isin(depot_list)]
        accountRegDF = accountRegDF.sort_values(by=['Name'])

        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/AssetReferences.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            assetsDF = pd.read_csv(fileName, sep=';')
        else:
            assetsDF = pd.DataFrame(columns=["AssetType","AssetID","AssetName",\
                "Ticker","NetRef1","NetRef2"])
            assetsDF.loc[len(assetsDF)] = pd.Series(dtype='float64')
            assetsDF = assetsDF.fillna('')
            
        assetsDF = assetsDF.sort_values(by=['AssetType', 'AssetName'])
    except:
        return redirect(url_for('nodata'))

    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/Depots.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            depotsDF = pd.read_csv(fileName, sep=';')
        else:
            depotsDF = pd.DataFrame(columns=["Bank","AccountNr","AssetID","BankRef",\
                "AssetAmount","AssetBuyPrice","Currency"])

        # Sort the depot entries and ignore case; lambda iterates lower case
        # over all entries in the dataframe
        depotsDF = depotsDF.sort_values(by=['Bank', 'AccountNr', 'BankRef'],
                ignore_index=True, key=lambda x: x.str.lower())
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
        depotsDF.loc[len(depotsDF)] = pd.Series(dtype='float64')
        depotsDF = depotsDF.sort_values(by=['AccountNr'], \
            ascending=False, na_position='first')
        depotsDF = depotsDF.fillna('')
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
        requestDF = requestDF[((requestDF['AssetAmount'] != "None") & \
            (requestDF['AssetID'] != "None"))]
        requestDF['AssetAmount'] = requestDF['AssetAmount']\
                            .str.replace(".", ",", regex=False)
        requestDF['AssetBuyPrice'] = requestDF['AssetBuyPrice'].astype(float)\
                            .map('{:.4f}'.format).str.replace(".", ",", regex=False)

        requestDF = requestDF.merge(assetsDF[["AssetID", "AssetName"]], on=["AssetID"], how="left")
        requestDF = requestDF.rename(columns={"AssetName": "BankRef"})
        requestDF = requestDF.merge(accountRegDF[["AccountNr", "Bank"]], on=["AccountNr"], how="left")
        requestDF = requestDF[["Bank","AccountNr","AssetID","BankRef","AssetAmount",\
            "AssetBuyPrice","Currency"]]

        if len(requestDF) < 1:
            flash('Error!')
        else:
            requestDF.to_csv(myDir+"initdata/Depots.csv", sep=';', \
                            index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('edit_depots'))

    return render_template('edit_depots.html', depots=depotsDF, assets=assetsDF, \
        accountReg=accountRegDF, currency=DefaultCurrency, serverName=serverName)

@app.route('/vlplans', methods=('GET', 'POST'))
def vlplans():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)

    # Read the account registry and assets
    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        accountRegDF = pd.read_csv(myDir+"initdata/AccountRegistry.csv", \
                            sep=';')
        depot_list = ['Depot', 'Wallet']
        accountRegDF = accountRegDF[accountRegDF['Type'].isin(depot_list)]
        accountRegDF = accountRegDF.sort_values(by=['Name'])

        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/AssetReferences.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            assetsDF = pd.read_csv(fileName, sep=';')
        else:
            assetsDF = pd.DataFrame(columns=["AssetType","AssetID","AssetName",\
                "Ticker","NetRef1","NetRef2"])
            assetsDF.loc[len(assetsDF)] = pd.Series(dtype='float64')
            assetsDF = assetsDF.fillna('')
            
        assetsDF = assetsDF.sort_values(by=['AssetType', 'AssetName'])

    except Exception as e:
        print(e)
        return redirect(url_for('nodata'))
                
    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/VLplans.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            vlplansDF = pd.read_csv(fileName, sep=';')
        else:
            vlplansDF = pd.DataFrame(columns=["PlanID","Bank","AccountNr","AssetID",\
                "StartDate","EndDate","Amount","Pieces","Currency"])

        try:
            vlplansDF['Amount'] = vlplansDF['Amount']\
                    .str.replace(",", ".").astype(float)
        except:
            vlplansDF['Amount'] = vlplansDF['Amount']\
                    .astype(float)
        vlplansDF['AccountNr'] = vlplansDF['AccountNr'].astype(str)
        vlplansDF.loc[len(vlplansDF)] = pd.Series(dtype='float64')
        vlplansDF = vlplansDF.sort_values(by=['StartDate'], \
            ascending=False, na_position='first')
        vlplansDF = vlplansDF.fillna('')
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
        requestDF = requestDF[((requestDF['AssetID'] != "") & \
            (requestDF['Amount'] != ""))]

        requestDF = requestDF.merge(accountRegDF[["AccountNr", "Bank"]], on=["AccountNr"], how="left")
        requestDF = requestDF[["PlanID","Bank","AccountNr","AssetID","StartDate","EndDate",\
            "Amount","Pieces","Currency"]]

        if len(requestDF) < 1:
            flash('Error!')
        else:
            requestDF.to_csv(myDir+"initdata/VLplans.csv", sep=';', \
                            index = False, quoting=csv.QUOTE_ALL, quotechar='"')
            return redirect(url_for('vlplans'))

    return render_template('vlplans.html', vlplans=vlplansDF, assets=assetsDF, \
        accountReg=accountRegDF, currency=DefaultCurrency, serverName=serverName)

@app.route('/settings', methods=('GET', 'POST'))
def settings():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        myDir = baseDir + 'users/' + '/' + current_user.username + '/'
        config = configparser.ConfigParser()
        config.sections()
        config.read(myDir + "ffdm.ini")
        confdatf = pd.DataFrame(config.items('Filter'), columns=['Param', 'Setting'])
        confdatf['Section'] = 'Filter'
        confdata = pd.DataFrame(config.items('Accounts'), columns=['Param', 'Setting'])
        confdata['Section'] = 'Accounts'
        confdat = pd.concat([confdatf, confdata])
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
            myDir = baseDir + 'users/' + '/' + current_user.username + '/'
            config = configparser.ConfigParser()
            config.sections()
            config.read(myDir + 'ffdm.ini')
            dat_count = 0
            for crow in requestDF.iterrows():
                config.set(crow[1][0], crow[1][1], crow[1][2].replace('%','%%'))
                if crow[1][1][:3] == "dat":
                    dat_count += 1
                    print(crow[1][1][3])
                if crow[1][2] == "" and crow[1][1][:3] == "dat":
                    dat_count -= 1
                    config.remove_option(crow[1][0], crow[1][1])
            # Adding one more line for accounts
            config.set(crow[1][0], "dat"+str(dat_count + 1), "")
            with open(myDir + 'ffdm.ini', 'w') as configfile:
                config.write(configfile)
            configfile.close()

            return redirect(url_for('settings'))

    return render_template('settings.html', confdat=confdat, serverName=serverName)

# Update ticker data
@app.route('/tdu')
def tdu():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        subprocess.run(["python3 ffdm.py -d " \
            + current_user.username], shell=True, check=True)
    except:
        return redirect(url_for('error'))

    return redirect(request.referrer)

@app.route('/acc')
def acc():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        subprocess.run(["python3 ffdm.py -f " \
            + current_user.username], shell=True, check=True)
    except:
        return redirect(url_for('error'))

    return redirect(request.referrer)

@app.route('/web')
def web():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        subprocess.run(["python3 ffdm.py -w " \
            + current_user.username], shell=True, check=True)
    except:
        return redirect(url_for('error'))

    return redirect(request.referrer)

@app.route('/unlock')
def unlock():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        subprocess.run(["python3 ffdm.py -u"], shell=True, check=True)
    except:
        return redirect(url_for('error'))
        
    return redirect(request.referrer)

@app.route('/fix')
def fix():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        subprocess.run(["python3 ffdm.py -u"], shell=True, check=True)
        subprocess.run(["python3 ffdm.py -f"], shell=True, check=True)
    except:
        return redirect(url_for('error'))
        
    return redirect(request.referrer)

@app.route('/targets', methods=('GET', 'POST'))
def targets():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        myDir = baseDir + 'users/' + current_user.username + '/'
        fileName = myDir+"initdata/TargetPrices.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            assetsDF = pd.read_csv(fileName, sep=';')            
        else:
            assetsDF = pd.DataFrame(columns=["AssetID","TargetPriceLow",\
                "TargetPriceHigh","Currency"])
            assetsDF.loc[len(assetsDF)] = pd.Series(dtype='float64')
            assetsDF = assetsDF.fillna('')
        fileName = myDir+"initdata/Currencies.csv"
        if os.path.isfile(fileName) and os.path.getsize(fileName) > 0:
            currencyDF = pd.read_csv(fileName, sep=';')            
        else:
            currencyDF = pd.DataFrame(columns=["Currency","CurrencyName",\
                "YF_USD"])
            currencyDF.loc[len(currencyDF)] = pd.Series(dtype='float64')
            currencyDF = currencyDF.fillna('')

        asset_cols = list(assetsDF.columns)
        namesDF = pd.read_csv(myDir+"initdata/AssetReferences.csv", \
                            sep=';')
        if check_db("qWatchlist", current_user.username) > 0:
            prices = get_db_data('SELECT qWatchlist.AssetID, qWatchlist.AssetName, \
                            qWatchlist.LastPrice FROM qWatchList', current_user.username)
            pricesDF = pd.DataFrame(prices, columns=['AssetID', 'AssetName', 'AssetPrice'])
        else:
            pricesDF = pd.DataFrame(columns=['AssetID', 'AssetName', 'AssetPrice'])
        # Filter all non active assets
        assetsDF = assetsDF[assetsDF['AssetID'].isin(namesDF['AssetID'])]

        # Add all new assets
        if len(namesDF[~namesDF['AssetID'].isin(assetsDF['AssetID'])]) > 0:
            newonesDF = namesDF[~namesDF['AssetID'].isin(assetsDF['AssetID'])] 
            assetsDF = pd.concat([assetsDF, newonesDF]).fillna(0)
            assetsDF['Currency'] = assetsDF['Currency'].replace(0,DefaultCurrency) 
     
        assetsDF['AssetName'] = assetsDF['AssetID']\
                    .map(pricesDF.set_index('AssetID')['AssetName'])
        assetsDF['LastPrice'] = assetsDF['AssetID']\
                    .map(pricesDF.set_index('AssetID')['AssetPrice'])
        assetsDF = assetsDF.sort_values(by=['AssetName'], ascending=True)

    except:
        return redirect(url_for('nodata'))
    
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

    return render_template('targets.html', assets=assetsDF, serverName=serverName,\
                currencies=currencyDF, DefaultCurrency=DefaultCurrency)

@app.route('/split', methods=('GET', 'POST'))
def split():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    try:
        if check_db("qWatchlist", current_user.username) > 0:
            assets = get_db_data('SELECT AssetID, AssetName \
                            FROM qWatchlist ORDER BY AssetID \
                            COLLATE NOCASE ASC;', current_user.username)
        else:
            return redirect(url_for('nodata')) 
    except Exception as e:
        print(e)
        return redirect(url_for('nodata'))

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
            subprocess.run(["python3 ffdm.py -f " \
                + current_user.username], shell=True, check=True)
        except:
            return redirect(url_for('error'))
                
        if len(requestDF) < 1:
            flash('Error!')
        else:
            return redirect(url_for('split'))

    return render_template('split.html', assets=assets, serverName=serverName)

@app.route('/watchlist')
def watchlist():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)
    if check_db("qWatchlist", current_user.username) > 0:
        try:
            watchlist = get_db_data('SELECT * FROM qWatchlist WHERE AssetID NOT IN \
                (SELECT AssetID FROM qDepotOverview) ORDER BY Delta DESC', current_user.username)
            investlist = get_db_data('SELECT * FROM qWatchlist WHERE AssetID IN \
                    (SELECT AssetID FROM qDepotOverview) ORDER BY Delta DESC', current_user.username)
        except:
            return redirect(url_for('error'))
    else:
        return redirect(url_for('nodata'))
    return render_template('watchlist.html', watchlist=watchlist, \
                            investlist=investlist, serverName=serverName)

@app.route('/about') 
def about():
    ffdm_ver = fl.ffdm_version(myDir=baseDir)

    if current_user.is_authenticated == False:
        return render_template('about.html', serverName=serverName, ver=ffdm_ver)
    else:
        try:
            filesToCheck = ["AccountRegistry.csv", "Accounts.csv", "AssetReferences.csv", \
                "Depots.csv", "VLplans.csv"]
            failedText = ""
            for cFile in filesToCheck:
                myDir = baseDir + 'users/' + current_user.username + '/'
                fileName = myDir+"initdata/" + cFile
                if os.path.isfile(fileName) and os.path.getsize(fileName) == 0:
                    if cFile == "AccountRegistry.csv":
                        failedText = failedText + "  No accounts or depots have been defined!\n"
                    if cFile == "Accounts.csv":
                        failedText = failedText + "  No account data has been entered!\n"
                    if cFile == "AssetReferences.csv":
                        failedText = failedText + "  No financial assets have been defined!\n"
                    if cFile == "Depots.csv":
                        failedText = failedText + "  No depot data has been entered!\n"
                    if cFile == "VLplans.csv":
                        failedText = failedText + "  No savings plans have been defined!\n"
            print(failedText)
            return render_template('about.html', failedText=failedText, serverName=serverName,\
                ver=ffdm_ver)
        except:
            return render_template('about.html', serverName=serverName, ver=ffdm_ver)
    return render_template('index.html', serverName=serverName, ver=ffdm_ver)

@app.route('/') 
def index():
    ffdm_ver = fl.ffdm_version(myDir=baseDir)

    if current_user.is_authenticated == False:
        return render_template('about.html', serverName=serverName, ver=ffdm_ver)
    if not os.path.exists(baseDir + '/indexes.sqlite'):
        try:
            subprocess.run(["python3 ffdm.py -i"], shell=True, check=True)
        except:
            return render_template('about.html', serverName=serverName, ver=ffdm_ver)
    else:
        try:
            idxDF = get_db_idxdata()
            fng = int(round(idxDF["y"].tail(1).values[0], 0))
            fngf = idxDF["rating"].tail(1).values[0]

            return render_template('index.html', fng=fng, fngf=fngf, failedText=failedText, \
                serverName=serverName, ver=ffdm_ver)
        except:
            return render_template('index.html', fng=fng, fngf=fngf, serverName=serverName, ver=ffdm_ver)
    return render_template('index.html', fng=fng, fngf=fngf, serverName=serverName, ver=ffdm_ver)

@app.route('/nodata') 
def nodata():
    #if current_user.is_authenticated == True:
    fi.check_files(baseDir + 'users/' + current_user.username + '/')
    return render_template('nodata.html')

@app.route('/error') 
def error():
    #if current_user.is_authenticated == True:
    fi.check_files(baseDir + 'users/' + current_user.username + '/')
    return render_template('error.html', serverName=serverName)

@app.route('/finance')
def finance():
    if current_user.is_authenticated == False:
        return render_template('index.html', serverName=serverName)

    if check_db("qOverview", current_user.username) > 0:

        # Read the account registry and assets
        try:
            myDir = baseDir + 'users/' + current_user.username + '/'
            accountRegDF = pd.read_csv(myDir+"initdata/AccountRegistry.csv", \
                                sep=';')
            accountRegDF['AccountNr'] = accountRegDF['AccountNr'].map(fl.get_account)
        except:
            return redirect(url_for('error'))

        try:
            overview = get_db_data('SELECT * FROM qOverview ORDER BY Slice DESC', current_user.username)
            monthly = get_db_data('SELECT * FROM qMonthly ORDER BY Year DESC', current_user.username)
            yearly = get_db_data('SELECT * FROM qYearly ORDER BY Year DESC', current_user.username)
            cumyear = get_db_data('SELECT * FROM qCumulative ORDER BY Year DESC', current_user.username)
            spend = get_db_data('SELECT * FROM qSpending ORDER BY Year DESC', current_user.username)
            quarterly = get_db_data('SELECT * FROM qQuarterly ORDER BY Quarter DESC', current_user.username)
            perf = get_db_data('SELECT * FROM qPerformance', current_user.username)
            usd = get_db_data('SELECT * FROM qUSDValues', current_user.username)
            balance = get_db_data('SELECT * FROM qAccountBalances WHERE Amount > 0 '+ \
                                ' ORDER BY Bank', current_user.username)
            depot = get_db_data('SELECT * FROM qDepotOverview '+ \
                                ' ORDER BY Value DESC', current_user.username)

            balanceDF = pd.DataFrame(balance, columns =['Bank', 'AccountNr', 'Balance']) 
            balanceDF = balanceDF.merge(accountRegDF[["AccountNr", "Name"]], \
                on=["AccountNr"], how="left")

            return render_template('finance.html', overview=overview, monthly=monthly, \
                                perf=perf, usd=usd, balance=balanceDF, depot=depot, \
                                yearly=yearly, cumyear=cumyear, spend=spend, \
                                quarterly=quarterly, serverName=serverName)
        except:
            return redirect(url_for('error'))
    else:
        return redirect(url_for('nodata'))
    
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
            DataDate = get_db_data('SELECT PriceTime FROM AssetPrices ORDER BY PriceTime \
                        DESC LIMIT 1', current_user.username)
            dtime = str(DataDate[0][0]).replace(' ', ' / ')[:18]
            dtime = dtime + " (" + DefaultCurrency + ")"
            return dtime
        except:
            return "No time..."

    def get_lastupdtime():
        try:    
            DataDate = get_db_data('SELECT PriceTime FROM AssetPrices \
                        ORDER BY PriceTime DESC LIMIT 1', current_user.username)
            dtime = str(DataDate[0][0])
            return dtime
        except:
            return "No time..."

    def get_prices(AssetID):
        try:    
            prices = get_db_data('SELECT AssetID, PriceTime, AssetPrice \
                        FROM AssetPrices WHERE AssetID="' + AssetID + '"GROUP BY \
                        PriceTime ORDER BY PriceTime DESC LIMIT 100', current_user.username)
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

