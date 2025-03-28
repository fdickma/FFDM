import pandas as pd
import requests
import datetime
import os
import time
import matplotlib.pyplot as plt
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import matplotlib.dates as mdates

def get_user_agent() -> str:
    """Get a random User-Agent strings from a list of some recent real browsers

    Parameters
    ----------
    None

    Returns
    -------
    str
        random User-Agent strings
    """
    user_agent_strings = [
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:86.1) Gecko/20100101 Firefox/86.1",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:86.1) Gecko/20100101 Firefox/86.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:82.1) Gecko/20100101 Firefox/82.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:83.0) Gecko/20100101 Firefox/83.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:84.0) Gecko/20100101 Firefox/84.0",
    ]

    return random.choice(user_agent_strings)

# Generate graphs
def idx_graph(idx_name, df, baseDir):
    plt.rcParams["figure.dpi"] = 150
    chartDF = (df[['date','y']]).set_index('date').copy()
    chartDF['SMA20'] = chartDF['y'].rolling(20).mean()
    #chartDF['SMA50'] = chartDF['y'].rolling(50).mean()
    chartDF.plot(title=idx_name,figsize=(8,4), linewidth = '2.0')
    plt.grid(color = 'grey', linestyle = '--', linewidth = 0.25)
    if idx_name == 'fearandgreed':
        plt.ylim(0, 100)
        plt.yticks([25, 45, 50, 55, 75], ['Extreme \nFear', ' Fear', 'Neutral', 'Greed', 'Extreme \nGreed'])
    # Put a legend below the graph
    plt.legend().remove()
    plt.gca().set_xlabel("")
    plt.gca().set_title("")
    plt.gcf().autofmt_xdate()
    
    # Remove the unnecessary x-axis title 
    frame1 = plt.gca()
    frame1.axes.get_xaxis().set_label_text('')
    currVal = int(round(chartDF["y"].tail(1).values[0], 0))
    
    # currDate = chartDF.index.values[-1]
    bbox_props = dict(boxstyle='round',fc='w', ec='k',lw=1)
    frame1.annotate(str(currVal), (100, currVal), xytext = (260, currVal), bbox=bbox_props)

    try:
        plt.savefig(baseDir + "static/idxcharts/" + idx_name + ".png")
    except:
        print("Plot for " + idx_name + " not saved!")

# Downloading data for an index
def index_data():

    baseDir = os.path.abspath(os.path.dirname(__file__)) + '/'

    # Create and start DB connection
    sql_uri = 'sqlite:///' + os.path.join(baseDir + '/indices.sqlite')
    engine = sa.create_engine(sql_uri, echo=False) 
    idx_connection = engine.connect()

    print('Updating indices')
    IndicesList = ['fearandgreed']
    for indexName in IndicesList: 
        print(indexName)
        doUpdate = False
        indexDir = baseDir + "indices/"
        if not os.path.exists(indexDir):
            os.makedirs(indexDir)
        indexFile = indexDir + indexName + ".csv"
        # Check if the data file is older than today
        if os.path.exists(indexFile) == True:
            filetime = os.path.getmtime(indexFile)
            filetimeConv = time.strftime("%Y-%m-%d",time.localtime(filetime))
            fileDate = datetime.datetime.strptime(filetimeConv, "%Y-%m-%d")
            nowDate = datetime.datetime.strptime(str(datetime.datetime.now())[:10], "%Y-%m-%d")
            if fileDate >= nowDate:
                doUpdate = True
        if os.path.exists(indexFile) == False or doUpdate == True:
            # Downloading index data
            if indexName == 'fearandgreed':
                readidxDF = fear_n_greed()
            if len(readidxDF) < 1:
                print("Error downloading data")
                continue    
            try:
                readidxDF.to_csv(indexFile, header=True)
                print("Saving", indexName)
            except:
                print("Error saving index data")
        indexDF = pd.read_csv(indexFile)
        print(indexDF)
        if len(indexDF) > 0:
            indexDF.to_sql("index_FearAndGreed", con=idx_connection, if_exists='replace', index=False, chunksize=100)
            # Make sure data is committed to database
            idx_connection.commit()
            idx_graph(indexName, indexDF, baseDir)
    # Closing the database
    idx_connection.close()    
    return

def fear_n_greed():
    # Public URL for fear and greed data
    url = 'https://production.dataviz.cnn.io/index/fearandgreed/graphdata'
    headers = dict()
    headers['user-agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36'
    req = requests.get(url, headers=headers)

    # Checking availability
    if req.status_code == 200:
        # Requesting data
        fng_req = req.json()
        # Checking if the fear and greed data is in the response
        if 'fear_and_greed_historical' in fng_req.keys() and 'data' in fng_req['fear_and_greed_historical'].keys():
            # Creating dataframe from response data
            df = pd.DataFrame(fng_req['fear_and_greed_historical']['data'])
            # Converting x column to a new date column
            df['date'] = pd.to_datetime(df['x'].apply(lambda x: x), unit='ms').dt.date
    return(df)

