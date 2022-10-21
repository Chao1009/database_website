# reformat migrated data to product and productitem data to be imported
import os
import pandas as pd
import numpy as np
import json
import datetime
from difflib import SequenceMatcher


# it is likely to be changed
ROOT_DIR = r'E:\Django\database_search'

DATA_DIR = os.path.join(ROOT_DIR, 'data')
RAWDATA_PATH = os.path.join(DATA_DIR, 'MD_Inv.xlsx')
CAT_SIZE_PATH = os.path.join(ROOT_DIR, 'search', 'static', 'cat_size.json')


def regulated_size(cat_size_book, vcat, vsize):
    # check category
    if vcat not in cat_size_book.keys():
        for key in cat_size_book.keys():
            if vcat in key.split('/'):
                vcat = key
                break
    if vcat not in cat_size_book.keys():
        print('Category {} is not found in the book!'.format(vcat))
        return 'NULL'

    sizes = [s for s in cat_size_book[vcat]]
    vsize = str(vsize)
    if vsize in sizes:
        return vsize

    for s in sizes:
        if SequenceMatcher(None, s, vsize).ratio() > 0.5:
            print('Size {} has no exact match in cateogry {}, but we found a similar one {}.'.format(vsize, vcat, s))
            return s
    print('Size {} has no exact match in cateogry {}, and no similar one found!'.format(vsize, vcat))
    return 'NULL'


if __name__ == '__main__':
    # read category/size dictionary
    cat_size = json.load(open(CAT_SIZE_PATH))

    # read data file and regulate header names
    df = pd.read_excel(RAWDATA_PATH, header=0).rename(columns={'Catogary1': 'Brand', 'Catogary2': 'Category'})
    df.columns = [x.lower().replace(' ', '_') for x in df.columns]
    # header checks
    required = ['brand', 'category', 'name', 'sku', 'size', 'stock_x', 'count']
    check_pass = True
    for r in required:
        if r not in df.columns:
            print('Require column {} from the data table, did not find it!'.format(r))
            check_pass = False
    if not check_pass:
        exit(-1)

    # regulate the category/size
    df['size'] = df['size'].astype(str).str.upper()
    df.loc[:, 'rsize'] = df.apply(lambda x: regulated_size(cat_size, x.category, x.size), axis=1)

    # get product table
    dfp = df.groupby('sku').agg({'name': 'first', 'brand': 'first', 'category': 'first'})\
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
    for sku, size, stockx_price, count in df[['sku', 'rsize', 'stock_x', 'count']].values:
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
