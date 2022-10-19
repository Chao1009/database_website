# reformat migrated data to product and productitem data to be imported
import os
import pandas as pd
import numpy as np
import datetime


ROOT_DIR = r'D:\Development\Django\database_search'
DATA_DIR = os.path.join(ROOT_DIR, 'data')
RAWDATA_PATH = os.path.join(DATA_DIR, 'MD_Inv.xlsx')

df = pd.read_excel(RAWDATA_PATH, header=0).rename(columns={'Catogary': 'Category'})

# get product table
dfp = df.groupby('SKU').agg({'Name': 'first', 'Category': 'first'})\
        .rename(columns={'Category': 'Brand'})\
        .reset_index()
dfp.loc[:, 'id'] = ''
dfp.loc[:, 'image_src'] = ''
dfp.columns = [x.lower() for x in dfp.columns]
dfp.to_csv(os.path.join(DATA_DIR, 'Product-{}.csv'.format(datetime.date.today().strftime('%Y-%m-%d'))), index=False)

# get product item table
item_data = []
begin = 1
stockx_price_inc = 100
today = datetime.date.today().strftime('%Y-%d-%m')
now = datetime.datetime.now().strftime('%Y-%d-%m %H:%M:%S')
for _, _, sku, size, stockx_price, count in df.values:
    ref_price = np.max([float(x) for x in str(stockx_price).split('/')])
    price = ref_price + stockx_price_inc
    for i in np.arange(begin, count+begin):
        item_id = '{}-{:06d}'.format(today, i)
        item_data.append([
                item_id, sku, price, stockx_price, size, now, 'N/A', 'Kickz Maryland',
        ])
    begin += count
dfi = pd.DataFrame(columns=['id', 'product', 'price', 'stockx_price', 'size', 'added_on', 'storage_loc', 'storage_addr'],
                   data=item_data)
dfi['price'] = dfi['price'].fillna(1500)
dfi.to_csv(os.path.join(DATA_DIR, 'Product-Item-{}.csv'.format(datetime.date.today().strftime('%Y-%m-%d'))), index=False)
