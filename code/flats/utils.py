import re
import requests
from PIL import Image
from bs4 import BeautifulSoup


class CaptchaRequired(Exception):
    pass


class QuotaExceeded(Exception):
    pass


def find_plan_avito(url: str) -> str:
    min_percent = 0.90
    min_light_value = 127

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Android 4.4; Tablet; rv:41.0) '
                      'Gecko/41.0 Firefox/41.0',
    })

    # headers = requests.utils.default_headers()
    # headers['User-Agent'] = 'Mozilla/5.0 (Android 4.4; Tablet; rv:41.0) ' \
    #     'Gecko/41.0 Firefox/41.0'
    r = session.get(url)
    if 'js-form-captcha' in r.text:
        r = session.get(url)
        if '<meta http-equiv="refresh" content="1">' in r.text:
            r = session.get(url)
            print(r.text)
            raise CaptchaRequired(url)

    bs = BeautifulSoup(r.text, 'html.parser')  # 'html5lib'

    image_url_list = [
        'https:' + re.findall(r'url\((.*?)\)', im['style'])[0]
        for im in bs.select('.gallery-list-item-link')
    ]

    if not image_url_list:
        im = bs.select_one('.gallery-img-cover')
        if im:
            image_url_list = [
                'https:' + re.findall(
                    r'url\(\'(.*?)\'\)',
                    im['style'],
                )[0].replace(
                    '640x480',
                    '80x60',
                )
            ]

    max_brightness = 0.0
    max_white_url = None
    for image_url in image_url_list:
        response = requests.get(image_url, stream=True)
        img = Image.open(response.raw).convert('L')
        data = img.getdata()

        total = len(data)

        light = 0
        for pix in data:
            if pix > min_light_value:
                light += 1
        brightness = light / total

        if brightness > min_percent and brightness > max_brightness:
            max_brightness = brightness
            max_white_url = image_url
            print(image_url, brightness)

    return max_white_url


def extract_ymap_feature_member(response: dict):
    return response.get('response', {}).get(
        'GeoObjectCollection', {}).get('featureMember') or [{}]


# unused function yet
def get_closest_metro(address: str, city: str):
    """
    https://geocode-maps.yandex.ru/1.x/
    ?geocode=30.355490%2059.924371&kind=metro&results=1
    """
    address = "{} {}".format(city, address)
    url = 'https://geocode-maps.yandex.ru/1.x/?geocode={}' \
          '&format=json&results=1'.format(
              requests.utils.quote(address)
          )
    r = requests.get(url)
    response = r.json()
    point = extract_ymap_feature_member(response)[0].get('GeoObject', {}).get(
        'Point', {}).get('pos', '')
    if not point:
        return None

    url = 'https://geocode-maps.yandex.ru/1.x/?geocode={}' \
        '&kind=metro&format=json&results=1'.format(
            requests.utils.quote(point)
        )
    r = requests.get(url)
    response = r.json()
    closest_subway_obj = extract_ymap_feature_member(response)[0].get(
        'GeoObject', {})

    closest_subway = closest_subway_obj.get('name')
    if not closest_subway:
        return None

    return closest_subway


def real_distance_to_subway(address: str, station: str, city: str) \
        -> dict or None:

    url = 'https://maps.googleapis.com/maps/api/distancematrix/json?' \
        'origins={}&destinations={}&mode=walking'.format(
            requests.utils.quote('{}, {}'.format(city, address)),
            requests.utils.quote('{}, метро {}'.format(city, station))
        )
    r = requests.get(url)
    try:
        data = r.json()
        if data['status'] == 'OVER_QUERY_LIMIT':
            raise QuotaExceeded(data['error_message'])
        distance = data.get('rows', [{}])[0].get('elements', [{}])[0].get(
            'distance', {}).get('value')
    except IndexError:
        return None

    return {'station': station, 'distance': distance, 'url': url}

# http://maps.googleapis.com/maps/api/directions/json?sensor=false&origin=%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F%2C+%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%2C+%D1%83%D0%BB%D0%B8%D1%86%D0%B0+%D0%94%D0%B5%D0%BD%D0%B8%D1%81%D0%B0+%D0%94%D0%B0%D0%B2%D1%8B%D0%B4%D0%BE%D0%B2%D0%B0%2C+7&language=ru&destination=%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F%2C+%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%2C+%D1%83%D0%BB%D0%B8%D1%86%D0%B0+%D0%9A%D1%83%D0%BB%D1%8C%D0%BD%D0%B5%D0%B2%D0%B0+3&mode=walking
