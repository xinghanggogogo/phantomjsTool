import logging
import copy
import json
import time
import codecs 
    
from bs4 import BeautifulSoup

import tornado.httpclient
from tornado.curl_httpclient import CurlAsyncHTTPClient
import tornado.ioloop

class Fetcher(object):

    default_options = {
        'method': 'GET',
        'headers': {},
        'allow_redirects': True,
        'use_gzip': True,
        'timeout': 120,
    }

    def __init__(self, phantomjs_proxy='http://localhost:25555', user_agent='', pool_size=100, async=False):

        self.phantomjs_proxy = phantomjs_proxy
        self.user_agent = user_agent
        self.async = async
        if self.async:
            self.http_client = CurlAsyncHTTPClient(max_clients=pool_size, io_loop=tornado.ioloop.IOLoop())
        else:
            self.http_client = tornado.httpclient.HTTPClient(max_clients=pool_size)

    @staticmethod
    def parse_option(default_options, url, user_agent, **kwargs):
        fetch = copy.deepcopy(default_options)
        fetch['url'] = url
        fetch['headers']['User-Agent'] = user_agent
        js_script = kwargs.get('js_script')
        if js_script:
            fetch['js_script'] = js_script
            fetch['js_run_at'] = kwargs.get('js_run_at', 'document-end')
        fetch['load_images'] = kwargs.get('load_images', False)
        return fetch

    def phantomjs_fetch(self, url, **kwargs):

        start_time = time.time()
        fetch = self.parse_option(self.default_options, url, user_agent=self.user_agent, **kwargs)
        request_conf = {'follow_redirects': False}

        if 'timeout' in fetch:
            request_conf['connect_timeout'] = fetch['timeout']
            request_conf['request_timeout'] = fetch['timeout'] + 1

        request = tornado.httpclient.HTTPRequest(url='%s' % self.phantomjs_proxy, method='POST', body=json.dumps(fetch), **request_conf)

        res = self.http_client.fetch(request)
        res = json.loads(res.body.decode())
        return res['content']

if __name__ == '__main__':

    fetcher = Fetcher()
    url = 'http://index.sogou.com/index/searchHeat?kwdNamesStr=Oh Wonder&timePeriodType=MONTH&dataType=SEARCH_ALL&queryType=INPUT'
    res = fetcher.phantomjs_fetch(url)
    soup = BeautifulSoup(res, 'html.parser')
    table = soup(class_='infoTABLE')
    tr = list(table[0].children)[2]
    hot_issue = list(tr.children)[4]
    print('The Hot Num in Sougou is:' + hot_issue.string)

