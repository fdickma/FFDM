import os
import shutil

def check_files(user_path):

    if not os.path.exists(user_path):
        os.mkdir(user_path)
        os.mkdir(user_path + 'initdata')

    ffdm_files = ['initdata/AccountRegistry.csv', \
        'initdata/Accounts.csv', 'initdata/AssetPrices.csv', \
        'initdata/TargetPrices.csv', 'initdata/VLplans.csv', \
        'initdata/AssetReferences.csv', 'initdata/Depots.csv']
    for f in ffdm_files:
        if not os.path.exists(user_path + f):
            os.mknod(user_path + f)

    app_path = os.path.abspath(os.path.dirname(__file__)) + \
        "/static/"
    ffdm_files = ['AccountTypes.csv', 'AssetTypes.csv', 'Currencies.csv']
    for f in ffdm_files:
        if not os.path.exists(user_path + 'initdata/' + f):
            shutil.copy(app_path + f, user_path + 'initdata/' + f)

    ffdm_files = ['ffdm.ini']
    for f in ffdm_files:
        if not os.path.exists(user_path + f):
            shutil.copy(app_path + f, user_path + f)
