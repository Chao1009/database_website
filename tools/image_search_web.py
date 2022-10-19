import os
import requests
import lxml
import re
import json
import urllib.request
import pandas as pd
from bs4 import BeautifulSoup
from serpapi import GoogleSearch


def get_original_images(cooked_soup):
    """
    https://kodlogs.com/34776/json-decoder-jsondecodeerror-expecting-property-name-enclosed-in-double-quotes
    if you try to json.loads() without json.dumps() it will throw an error:
    "Expecting property name enclosed in double quotes"
    """

    google_images = []

    all_script_tags = soup.select("script")

    # # https://regex101.com/r/48UZhY/4
    matched_images_data = "".join(re.findall(r"AF_initDataCallback\(([^<]+)\);", str(all_script_tags)))

    matched_images_data_fix = json.dumps(matched_images_data)
    matched_images_data_json = json.loads(matched_images_data_fix)

    # https://regex101.com/r/VPz7f2/1
    matched_google_image_data = re.findall(r'\"b-GRID_STATE0\"(.*)sideChannel:\s?{}}', matched_images_data_json)

    # https://regex101.com/r/NnRg27/1
    matched_google_images_thumbnails = ", ".join(
        re.findall(r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]',
                   str(matched_google_image_data))).split(", ")

    thumbnails = [
        bytes(bytes(thumbnail, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape") for thumbnail in
        matched_google_images_thumbnails
    ]

    # removing previously matched thumbnails for easier full resolution image matches.
    removed_matched_google_images_thumbnails = re.sub(
        r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]', "", str(matched_google_image_data))

    # https://regex101.com/r/fXjfb1/4
    # https://stackoverflow.com/a/19821774/15164646
    matched_google_full_resolution_images = re.findall(r"(?:'|,),\[\"(https:|http.*?)\",\d+,\d+\]",
                                                       removed_matched_google_images_thumbnails)

    full_res_images = [
        bytes(bytes(img, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape") for img in
        matched_google_full_resolution_images
    ]

    for index, (metadata, thumbnail, original) in enumerate(
            zip(cooked_soup.select('.isv-r.PNCib.MSM1fd.BUooTd'), thumbnails, full_res_images), start=1):
        google_images.append({
            'title': metadata.select_one('.VFACy.kGQAp.sMi44c.lNHeqe.WGvvNb')['title'],
            'link': metadata.select_one('.VFACy.kGQAp.sMi44c.lNHeqe.WGvvNb')['href'],
            'source': metadata.select_one('.fxgdke').text,
            'thumbnail': thumbnail,
            'original': original
        })

    return google_images


ROOT_DIR = r'D:\Development\Django\database_search'
DATA_DIR = os.path.join(ROOT_DIR, 'data')
DATA_PATH = os.path.join(DATA_DIR, 'Product-2022-10-12.csv')
IMAGE_DIR = os.path.join(ROOT_DIR,  'search', 'static', 'images')

dfp = pd.read_csv(DATA_PATH).fillna('').set_index('sku')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'
}

params = {
    'q': '',  # search query
    'tbm': 'isch',  # image results
    'hl': 'en',  # language of the search
    'gl': 'us',  # country where search comes from
    'ijn': '0'  # page number
}

for sku in dfp.index:
    # do not repeat the search for existing images
    if os.path.exists(os.path.join(IMAGE_DIR, '{}.png'.format(sku))):
        # print('skip SKU: {} because an image already exists.'.format(sku))
        # update image path
        dfp.loc[sku, 'image_src'] = '../static/images/{}.png'.format(sku)
        continue

    try:
        # search image
        print('try downloading image for SKU:{}'.format(sku))
        params.update({'q': '{} stockx'.format(sku)})
        html = requests.get('https://www.google.co.in/search', params=params, headers=headers, timeout=30)
        soup = BeautifulSoup(html.text, 'lxml')
        searched_images = get_original_images(soup)

        # save image
        image_url = searched_images[0]['original']
        img_data = requests.get(image_url).content
        with open(os.path.join(IMAGE_DIR, '{}.png'.format(sku)), 'wb') as handler:
            handler.write(img_data)
        print('downloading image from {}'.format(image_url))

        # update image path
        dfp.loc[sku, 'image_src'] = '../static/images/{}.png'.format(sku)

    except Exception as e:
        print(searched_images)
        print(e)
        pass


dfp.reset_index().to_csv(DATA_PATH.replace('.csv', '_img.csv'), index=False)
