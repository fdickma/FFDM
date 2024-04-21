### **FFDM - Free Financial Data Management**

FFDM is a web based financial data management software which display the finance data from data files by DKB and Sparkasse, including DKB depot data. In addition a watchlist for stock, ETF, funds and gold can be managed.

Most parameters can be changed via the web interface. Manual accounts and depots can be directly edited in the web interface or in the corresponding CSV files. CSV files can be uploaded via the web interface. This includes replacing files with different names (a necessity for files from Sparkasse).

Current prices of financial products are retrieved by scraping web pages. The main sources have changed over time because some sources block these requests. Long term price data is downloaded via Yahoo finance.

#### Requirements

All can be met by Linux distributions like Debian 11 or Arch Linux.

* Python 3.10+
* Pandas
* Flask
* yfinance
* SQLalchemy

#### Parameters for the command line module

```
usage: python ffdm.py [-t] [-w] [-u] [-f] [-a]
                          [-c] [-r] [-b] [-c]

-t, --test      start in test mode 
-w, --web       update finance data from web source
-u, --unlock    delete the lock file
-f, --force     force account data updates
-a, --all       force all data update (web and accounts)
-c, --clean     clean price data from errors
-r, --restore   restore price data from backup file
-b, --backup    back up price data to file
-c, --target    check target prices
```

#### Provided example data

The data files provided contain only generated information not related to any person or organization. However, the example data supports a test of all functions.

### Screenshots

#### Main view

![alt text](img/ffdm_01.png)

#### Watchlist

![alt text](img/ffdm_02.png)

#### Finance overview

![alt text](img/ffdm_03.png)
![alt text](img/ffdm_04.png)

#### Menu example

![alt text](img/ffdm_05.png)

#### Manual account data

![alt text](img/ffdm_06.png)

#### Manual depot data

![alt text](img/ffdm_07.png)

#### Setting up accounts and depots

![alt text](img/ffdm_08.png)

#### Setting up assets

![alt text](img/ffdm_09.png)

#### Defining target values for assets

![alt text](img/ffdm_10.png)
