from typing import Tuple, List, Dict
import re
import json
from lzstring import LZString
import requests
from bs4 import BeautifulSoup
import pyjsparser

ROOT_URL = 'https://www.mhgui.com'

def to_base_36_str(n: int) -> str:
    if n == 0:
        return '0'

    chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    m = 36
    res = []

    while n > 0:
        res.append(chars[n % m])
        n //= m

    return ''.join(res[::-1])

def extract_secret_js(url: str) -> str:
    res = requests.get(url)
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, 'html.parser')
    js = soup.select('script')
    js = next(filter(lambda j: len(j.text) and j.attrs.get('id') is None, js))
    return js.text

def compose(p: str, a: int, c: int, k: List[str], e: int):
    d = {}
    def e(c):
        # original JS implementation
        #return (c < a ? "" : e(parseInt(c / a))) + ((c = c % a) > 35 ? String.fromCharCode(c + 29) : c.toString(36))
        hi = '' if c < a else e(c // a)
        c = c % a
        lo = chr(c + 29) if c > 35 else to_base_36_str(c)
        return hi + lo

    while c > 0:
        c -= 1
        d[e(c)] = k[c] if k[c] != '' else e(c)

    results = re.split(r'(\b\w+\b)', p)
    result = ''.join(d[r] if r in d else r for r in results)
    result = re.search(r'^.*\((\{.*\})\).*$', result).group(1)
    return json.loads(result)

    # original JS implementation
    # if (!''.replace(/^/, String)) {
    #     while (c--)
    #         d[e(c)] = k[c] || e(c);
    #     k = [function(e) {
    #         return d[e]
    #     }
    #     ];
    #     e = function() {
    #         return '\\w+'
    #     }
    #     ;
    #     c = 1;
    # }
    # ;while (c--)
    #     if (k[c])
    #         p = p.replace(new RegExp('\\b' + e(c) + '\\b','g'), k[c]);
    # return p;


def decode_img_infos(js_str: str):
    i = js_str.find('(')
    j = js_str.rfind(')')
    js_str = js_str[i+1:j]
    parsed = pyjsparser.parse(js_str)
    args = parsed['body'][1]['expression']['expressions']
    p = args[0]['value']
    a = int(args[1]['raw'])
    c = int(args[2]['raw'])
    k = args[3]['callee']['object']['value']
    e = int(args[4]['raw'])
    return compose(p, a, c, decode_k(k), e)

def get_volumes(url: str) -> Tuple[str]:
    res = requests.get(url)
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, 'html.parser')
    sections = soup.select('.chapter-list a')
    return tuple((s.attrs.get('title'), s.attrs.get('href')) for s in sections)

def decode_k(k: str):
    decoded = LZString.decompressFromBase64(k)
    return decoded.split('|')

if __name__ == '__main__':
    # print(get_volumes('https://www.mhgui.com/comic/751/'))
    i = to_base_36_str(1000)
    k = decode_k('O4UwRgDgPlEHYHMoEYCsAGZUBWEkQCcQBJOASwBcoBxagZXQHYB9dAZgDYwb6nXOeDFu1TdaQ/qkF92AFjG9hbWdKVsFE9mxjiZbAEwa9+1f2RGlWU+3QX+6HYtb6AnHfSvr+gBzufXxj9GLy4Qr1Fw6zZg3SVAqN8veWsMdwxrWTcMlwzE2NZZbwz4/PRZGKcy0NLZDgyI0rYimqkalRr1DO0awwyTGvMMrBrbDIdGrImM5NL9dsr9XtnuyvRm1ZKN63Rq1brS9AbV1tWZ0+3Og5XNNfcPO+HVhwAzMgAbEABnKEAabyZAd2UoABjOAAQwAtiAUGw2OgHECyAATKCQMhAqCAZb9ADKugAg9FFgyEopHbfqrHIHSaVZDjSqoR6aRZeQazekyfSjWY0zTISnc8lUvIC6zITbcirc3YS4VHbknblneXCy5U64yZBLKmk7nMqms4TUvzKzR0tJamSoDWaFxm4QuHVWvWsFwcyrO6zeXkyD3uwWabzrP2ir3ir2S0PumVeuVehUx91Gr2q4TeS1em2sbz2r2O9DW9wuJNOhO2lTeAwAWQAYgA1ACCzAACgBpesuACiAA0ACIAewgzwAnp8kMgOKhvLJFqg2FhPm9oa4coQQAA3YjI5AwzBQOAgAAeFHXKLePaBAGtmED0Z8KKCKABXb5MKAAKRfdCgZHBCC7d9BsE+LAeRUD44CgCgCHvKFXnIT4AAsQGRUoXCDW0Q1tMMMOsFxI1taMS24CA7zg90uS9F1NEYflKM9YQOHmTQOGLVgmOsDhUzo9MdizOicw4CiZH4lJaJY/DWFQajzQDc1UPE9DxMwhSUlw8SxMOWNhFQBjzWYw5C0OX1BJUnYNJYxSmEM4RGGkqzZKYeSmHMxh9kqRhjLc6xGFMphtLolzKP0xhdI4SS6Icjg7I4GyWMs1hGA4lisjocsAAlPIEqyc0YHi4q4xh0CAA===')
    t = extract_secret_js('https://www.mhgui.com/comic/1501/13299.html')
    info = decode_img_infos(t)
    print(info)
