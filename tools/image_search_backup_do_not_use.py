import os
import pandas as pd
import numpy as np
from google_images_search import GoogleImagesSearch

ROOT_DIR = r'D:\Development\Django\database_search'
DATA_DIR = os.path.join(ROOT_DIR, 'data')
DATA_PATH = os.path.join(DATA_DIR, 'Product-2022-10-11.csv')
IMAGE_DIR = os.path.join(ROOT_DIR,  'search', 'static', 'images')

dfp = pd.read_csv(DATA_PATH).fillna('').set_index('sku')

# you can provide API key and CX using arguments,
# or you can set environment variables: GCS_DEVELOPER_KEY, GCS_CX
gis = GoogleImagesSearch('AIzaSyAqGl2oK_omWrzJ-iH3EdN9odEhk5XP9qk', '573b9d580fe294018')


def get_proper_image(gis_results):
    for img in gis_results:
        if 'stockx' in img.url:
            return img
    return gis_results[0]


# define search params
# option for commonly used search param are shown below for easy reference.
# For param marked with '##':
#   - Multiselect is currently not feasible. Choose ONE option only
#   - This param can also be omitted from _search_params if you do not wish to define any value
_search_params = {
    'num': 3,
    'fileType': 'png|jpg',
    'imgColorType': 'color'
}

for sku in np.random.choice(dfp.index, 5):
    if os.path.exists(os.path.join(IMAGE_DIR, '{}.png'.format(sku))):
        print('skip SKU: {} because an image already exists.'.format(sku))
        dfp.loc[sku, 'image_src'] = '../static/images/{}.png'.format(sku)
        continue
    print('try to search image for SKU: {}'.format(sku))
    _search_params.update({'q': '{} stockx'.format(sku)})
    try:
        gis.search(search_params=_search_params)
        image = get_proper_image(gis.results())
        image.download(IMAGE_DIR)
        # image.resize(500, 500)
        os.rename(image.path, os.path.join(IMAGE_DIR, '{}.png'.format(sku)))
        print('downloaded image from {}'.format(image.url))
        dfp.loc[sku, 'image_src'] = '../static/images/{}.png'.format(sku)
    except Exception as e:
        print(e)
        pass

dfp.reset_index().to_csv(DATA_PATH.replace('.csv', '_img.csv'), index=False)
