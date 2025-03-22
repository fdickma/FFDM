import sys
import os
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import datetime

user_id = sys.argv[1]
if len(user_id) == 0 or user_id == '-f':
    user_id = 'test'
print(user_id)

def del_table(t_name, metadata_obj, engine):
    pre_table = sa.Table(t_name, metadata_obj)
    metadata_obj.remove(pre_table)
    pre_table.drop(engine, checkfirst=True)

appdir = os.path.abspath(os.path.dirname(__file__))
sql_uri = 'sqlite:///' + os.path.join(appdir, 'users/' + user_id + '/ffdm.sqlite')
engine = sa.create_engine(sql_uri, echo=False)
connection = engine.connect()

Session = sessionmaker(bind=engine)
session = Session()
session.begin()

metadata_obj = sa.MetaData()

for t in ['Accounts', 'HistoryPrices', 'AssetInfo', 'CurrencyRates', \
    'AssetReferences', 'AssetPrices', 'AssetTypes', 'TargetPrices', \
    'Depots', 'VLplans', 'index_FearAndGreed']:
    del_table(t, metadata_obj, engine)

accounts_t = sa.Table(
    'Accounts',
    metadata_obj,     
    sa.Column('ID', sa.Integer, primary_key=True),
    sa.Column('Bank', sa.String(10), default='None', nullable=False),
    sa.Column('AccountNr', sa.String(34), default='00000', nullable=False),
    sa.Column('EntryDate', sa.Date, default=datetime.datetime, nullable=False),
    sa.Column('Reference', sa.String(4096),default="FFDM default reference text", nullable=False),
    sa.Column('Amount', sa.Float, default=0, nullable=False),
    sa.Column('Currency', sa.String(4), default="EUR", nullable=False),
)

assetref_t = sa.Table(
    'AssetReferences',
    metadata_obj,     
    sa.Column('ID', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('AssetID', sa.String(12), default='NO0000000000', nullable=False),
    sa.Column('AssetType', sa.String(3), default='', nullable=False),
    sa.Column('AssetName', sa.String(254),default="FFDM default asset name", nullable=False),
    sa.Column('Ticker', sa.String(254), default=None, nullable=True),
    sa.Column('NetRef1', sa.String(254),default='', nullable=True),
    sa.Column('NetRef2', sa.String(254),default='', nullable=True),
)

assetprice_t = sa.Table(
    'AssetPrices',
    metadata_obj,     
    sa.Column('ID', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('AssetID', sa.String(12), default='NO0000000000', nullable=False),
    sa.Column('PriceTime', sa.Date, default=datetime.datetime, nullable=False),
    sa.Column('AssetPrice', sa.Float, default=0, nullable=False),
    sa.Column('Currency', sa.String(4), default='EUR', nullable=False),
)

assettypes_t = sa.Table(
    'AssetTypes',
    metadata_obj,     
    sa.Column('ID', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('AssetType', sa.String(3), default='', nullable=False),
    sa.Column('AssetTypeName', sa.String(254), default='', nullable=False),
)

targetprice_t = sa.Table(
    'TargetPrices',
    metadata_obj,     
    sa.Column('ID', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('AssetID', sa.String(12), default='NO0000000000', nullable=False),
    sa.Column('TargetPriceLow', sa.Float, default=0, nullable=False),
    sa.Column('TargetPriceHigh', sa.Float, default=0, nullable=False),
    sa.Column('Currency', sa.String(4), default='EUR', nullable=False),
)

depot_t = sa.Table(
    'Depots',
    metadata_obj,     
    sa.Column('ID', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('Bank', sa.String(10), default='None', nullable=False),
    sa.Column('DepotNr', sa.String(34), default='00000', nullable=False),
    sa.Column('AssetID', sa.String(12), default='NO0000000000', nullable=False),
    sa.Column('BankRef', sa.String(254), default='', nullable=False),
    sa.Column('AssetAmount', sa.Float, default=0, nullable=False),
    sa.Column('AssetBuyPrice', sa.Float, default=0, nullable=False),
    sa.Column('Currency', sa.String(4), default='EUR', nullable=False),
)

vlplans_t = sa.Table(
    'VLplans',
    metadata_obj,     
    sa.Column('ID', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('PlanID', sa.String(11), default='', nullable=False),
    sa.Column('StartDate', sa.Date, default=datetime.datetime, nullable=False),
    sa.Column('EndDate', sa.Date, default=None, nullable=True),
    sa.Column('AssetID', sa.String(12), default='NO0000000000', nullable=False),
    sa.Column('Bank', sa.String(10), default='None', nullable=False),
    sa.Column('AccountNr', sa.String(34), default='00000', nullable=False),
    sa.Column('Amount', sa.Float, default=0, nullable=False),
    sa.Column('Pieces', sa.Float, default=0, nullable=False),
    sa.Column('Currency', sa.String(4), default='EUR', nullable=False),
)

# Create all tables
metadata_obj.create_all(engine)
session.commit()
connection.close()