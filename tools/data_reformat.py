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

# datetime tags
# DATE = datetime.date.today().strftime('%Y-%m-%d')
# DATETIME = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
DATE = '2022-10-20'
DATETIME = '2022-10-20 00:00:00'


def regulated_size(cat_size_book, vcat, vsize, verbose=0, null_value='NULL'):
    # print(vcat, vsize)
    # check category
    if vcat not in cat_size_book.keys():
        for key in cat_size_book.keys():
            if vcat in key.split('/'):
                vcat = key
                break
    if vcat not in cat_size_book.keys():
        if verbose > 0:
            print('Category {} is not found in the book!'.format(vcat))
        return null_value

    sizes = [s for s in cat_size_book[vcat]]
    vsize = str(vsize)
    if vsize in sizes:
        return vsize

    for s in sizes:
        ratio = SequenceMatcher(None, s, vsize).ratio()
        if ratio >= 0.5:
            if verbose > 0:
                print('Size {} has no exact match in cateogry {}, '
                      'but we found a similar one {} with matching ratio {:.2f}.'.format(vsize, vcat, s, ratio))
            return s
    if verbose > 0:
        print('Size {} has no exact match in cateogry {}, and no similar one found!'.format(vsize, vcat))
    return null_value


if __name__ == '__main__':
    # read category/size dictionary
    cat_size = json.load(open(CAT_SIZE_PATH))

    # read data file and regulate header names
    df = pd.read_excel(RAWDATA_PATH, header=0).rename(columns={'Category1': 'Brand', 'Category2': 'Category'})
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
    df.loc[:, 'rsize'] = df.apply(lambda x: regulated_size(cat_size, x['category'], x['size']), axis=1)
    mask = df['rsize'] == 'NULL'
    if sum(mask):
        print('WARNING')
        print('{} entries cannot find correct size in the size book.'.format(sum(mask)))
        print(df.loc[df['rsize'] == 'NULL'])

    # get product table
    dfp = df.groupby('sku').agg({'name': 'first', 'brand': 'first', 'category': 'first'})\
            .reset_index()
    dfp.loc[:, 'id'] = ''
    dfp.loc[:, 'image_src'] = ''
    dfp.columns = [x.lower() for x in dfp.columns]
    dfp.to_csv(os.path.join(DATA_DIR, 'Product-{}.csv'.format(DATE)), index=False)

    # get product item table
    item_data = []
    begin = 1
    stockx_price_inc = 100
    for sku, size, stockx_price, count in df[['sku', 'rsize', 'stock_x', 'count']].values:
        ref_price = np.max([float(x) for x in str(stockx_price).split('/')])
        price = ref_price + stockx_price_inc
        for i in np.arange(begin, count+begin):
            item_id = '{}-{:06d}'.format(DATE, i)
            item_data.append([
                    item_id, sku, price, stockx_price, size, DATETIME, 'N/A', 'Kickz Maryland',
            ])
        begin += count
    dfi = pd.DataFrame(columns=['id', 'product', 'price', 'stockx_price', 'size', 'added_on', 'storage_loc', 'storage_addr'],
                       data=item_data)
    dfi['price'] = dfi['price'].fillna(1500)
    dfi.to_csv(os.path.join(DATA_DIR, 'Product-Item-{}.csv'.format(DATE)), index=False)
