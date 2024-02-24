import sqlalchemy as db
from sqlalchemy.orm import sessionmaker
import datetime

def del_table(t_name, metadata_obj, engine):
    pre_table = db.Table(t_name, metadata_obj)
    metadata_obj.remove(pre_table)
    pre_table.drop(engine, checkfirst=True)

engine = db.create_engine('sqlite:///ffdm.sqlite', echo=False) 
connection = engine.connect()

Session = sessionmaker(bind=engine)
session = Session()
session.begin()

metadata_obj = db.MetaData()

for t in ['Accounts', 'HistoryPrices', 'AssetInfo', 'CurrencyRates', \
    'AssetReferences', 'AssetPrices', 'AssetTypes', 'TargetPrices', \
    'Depots', 'VLplans']:
    del_table(t, metadata_obj, engine)

accounts_t = db.Table(
    'Accounts',
    metadata_obj,     
    db.Column('ID', db.Integer, primary_key=True),
    db.Column('Bank', db.String(10), default='None', nullable=False),
    db.Column('AccountNr', db.String(34), default='00000', nullable=False),
    db.Column('EntryDate', db.Date, default=datetime.datetime, nullable=False),
    db.Column('Reference', db.String(4096),default="FFDM default reference text", nullable=False),
    db.Column('Amount', db.Float, default=0, nullable=False),
    db.Column('Currency', db.String(4), default="EUR", nullable=False),
)

assetref_t = db.Table(
    'AssetReferences',
    metadata_obj,     
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('AssetID', db.String(12), default='NO0000000000', nullable=False),
    db.Column('AssetType', db.String(3), default='', nullable=False),
    db.Column('AssetName', db.String(254),default="FFDM default asset name", nullable=False),
    db.Column('Ticker', db.String(254), default=None, nullable=True),
    db.Column('NetRef1', db.String(254),default='', nullable=False),
    db.Column('NetRef2', db.String(254),default='', nullable=False),
)

assetprice_t = db.Table(
    'AssetPrices',
    metadata_obj,     
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('AssetID', db.String(12), default='NO0000000000', nullable=False),
    db.Column('PriceTime', db.Date, default=datetime.datetime, nullable=False),
    db.Column('AssetPrice', db.Float, default=0, nullable=False),
    db.Column('Currency', db.String(4), default='EUR', nullable=False),
)

assettypes_t = db.Table(
    'AssetTypes',
    metadata_obj,     
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('AssetType', db.String(3), default='', nullable=False),
    db.Column('AssetTypeName', db.String(254), default='', nullable=False),
)

targetprice_t = db.Table(
    'TargetPrices',
    metadata_obj,     
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('AssetID', db.String(12), default='NO0000000000', nullable=False),
    db.Column('TargetPriceLow', db.Float, default=0, nullable=False),
    db.Column('TargetPriceHigh', db.Float, default=0, nullable=False),
    db.Column('Currency', db.String(4), default='EUR', nullable=False),
)

depot_t = db.Table(
    'Depots',
    metadata_obj,     
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('Bank', db.String(10), default='None', nullable=False),
    db.Column('DepotNr', db.String(34), default='00000', nullable=False),
    db.Column('AssetID', db.String(12), default='NO0000000000', nullable=False),
    db.Column('BankRef', db.String(254), default='', nullable=False),
    db.Column('AssetAmount', db.Float, default=0, nullable=False),
    db.Column('AssetBuyPrice', db.Float, default=0, nullable=False),
    db.Column('Currency', db.String(4), default='EUR', nullable=False),
)

vlplans_t = db.Table(
    'VLplans',
    metadata_obj,     
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('PlanID', db.String(11), default='', nullable=False),
    db.Column('StartDate', db.Date, default=datetime.datetime, nullable=False),
    db.Column('EndDate', db.Date, default=None, nullable=True),
    db.Column('AssetID', db.String(12), default='NO0000000000', nullable=False),
    db.Column('Bank', db.String(10), default='None', nullable=False),
    db.Column('AccountNr', db.String(34), default='00000', nullable=False),
    db.Column('Amount', db.Float, default=0, nullable=False),
    db.Column('Pieces', db.Float, default=0, nullable=False),
    db.Column('Currency', db.String(4), default='EUR', nullable=False),
)

# Create all tables
metadata_obj.create_all(engine)
session.commit()
connection.close()