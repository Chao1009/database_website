import os
import requests
import lxml
import re
import json
import urllib.request
import pandas as pd
from bs4 import BeautifulSoup
from serpapi import GoogleSearch


ROOT_DIR = r'D:\Development\Django\database_search'
DATA_DIR = os.path.join(ROOT_DIR, 'data')
DATA_PATH = os.path.join(DATA_DIR, 'Product-2022-10-11_img.csv')
IMAGE_DIR = os.path.join(ROOT_DIR,  'search', 'static', 'images')

dfp = pd.read_csv(DATA_PATH).fillna('').set_index('sku')
sku_images = [
    ('CD0461-016', 'https://images.stockx.com/images/Air-Jordan-1-Retro-High-Satin-Black-Toe-W-Product.jpg?fit=fill&bg=FFFFFF&w=1200&h=857&fm=webp&auto=compress&dpr=2&trim=color&updated_at=1606319735&q=75'),
    ('CU0449-641', 'https://images.stockx.com/images/Air-Jordan-1-Retro-High-OG-Atmosphere-PS-Product.jpg?fit=fill&bg=FFFFFF&w=700&h=500&fm=webp&auto=compress&q=90&dpr=2&trim=color&updated_at=1641565520'),
]

for sku, image_url in sku_images:
    # do not repeat the search for existing images
    if os.path.exists(os.path.join(IMAGE_DIR, '{}.png'.format(sku))):
        # print('skip SKU: {} because an image already exists.'.format(sku))
        # update image path
        dfp.loc[sku, 'image_src'] = '../static/images/{}.png'.format(sku)
        continue

    try:
        # search image
        print('try downloading image for SKU:{}'.format(sku))
        img_data = requests.get(image_url).content
        with open(os.path.join(IMAGE_DIR, '{}.png'.format(sku)), 'wb') as handler:
            handler.write(img_data)
        print('downloading image from {}'.format(image_url))

        # update image path
        dfp.loc[sku, 'image_src'] = '../static/images/{}.png'.format(sku)

    except Exception as e:
        print(e)
        pass


dfp.reset_index().to_csv(DATA_PATH, index=False)
