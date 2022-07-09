from typing import List
from bs4 import BeautifulSoup
from lzstring import LZString
from functools import lru_cache
import requests
import re
import json
import pyjsparser

IMG_ROOT_URL = 'https://i.hamreus.com'
MHG_URL = 'https://www.mhgui.com'

class MHGMetaFetcher:
    def __init__(self, url: str):
        self.url = url
        self.volumes = self._get_volumes()

    @lru_cache(maxsize=100)
    def get_volume_infos(self, i: int):
        vol_url = MHG_URL + self.volumes[i][1]
        js = self._extract_secret_js(vol_url)
        return self._decode_volume_infos(js)

    def get_volume_page_content(self, vol_idx: int, page: int):
        info = self.get_volume_infos(vol_idx)
        page_url = IMG_ROOT_URL + info['path'] + info['files'][page]
        params = {'e': info['sl']['e'], 'm': info['sl']['m']}
        headers = {'Referer': 'https://www.mhgui.com/'}
        res = requests.get(page_url, params=params, headers=headers)
        assert res.status_code == 200
        return res.content

    def _decode_volume_infos(self, js_str: str):
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
        return self._compose_meta_infos(p, a, c,self._decode_k(k), e)

    def _get_volumes(self):
        res = requests.get(self.url)
        assert res.status_code == 200
        soup = BeautifulSoup(res.text, 'html.parser')
        sections = soup.select('.chapter-list a')
        return tuple((s.attrs.get('title'), s.attrs.get('href')) for s in sections)

    def _decode_k(self, k) -> List[str]:
        decoded = LZString.decompressFromBase64(k)
        return decoded.split('|')

    def _extract_secret_js(self, vol_url: str):
        res = requests.get(vol_url)
        assert res.status_code == 200
        soup = BeautifulSoup(res.text, 'html.parser')
        js = soup.select('script')
        js = next(filter(lambda j: len(j.text) and j.attrs.get('id') is None, js))
        return js.text

    def _compose_meta_infos(self, p: str, a: int, c: int, k: List[str], e: int):
        d = {}
        def e(c):
            # original JS implementation
            #return (c < a ? "" : e(parseInt(c / a))) + ((c = c % a) > 35 ? String.fromCharCode(c + 29) : c.toString(36))
            hi = '' if c < a else e(c // a)
            c = c % a
            lo = chr(c + 29) if c > 35 else MHGMetaFetcher.to_base_36_str(c)
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

    @staticmethod
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