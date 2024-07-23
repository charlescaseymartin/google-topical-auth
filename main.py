import os
import sys
import json
import random
import requests
import argparse
# from bs4 import BeautifulSoup
import urllib3
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
# from selenium.webdriver.common.by import By

prog = 'Google Topical Auth'
description = 'Given target keywords, this program will generate a topic authority map'
key_help = 'A list of space separated target keywords to use'
key_file_help = 'A text file of comma separated target keywords to use'
proxy_help = 'A text file path that contains a newline separated list of proxies.\nProxy format: <USERNAME>:<PASSWORD>@<IP-ADDRESS>:<PORT>'
data_path = os.path.join(os.getcwd(), 'data')
default_output_file = os.path.join(data_path, 'results.json')
suggestions_url = 'https://www.google.com/complete/search?client=firefox&q='
user_agent = 'Mozilla/23.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0'
keywords_key = 'keywords'
keywords_file_key = 'filename'
proxies_key = 'proxies'
urllib3.disable_warnings()
parser = argparse.ArgumentParser(prog=prog, description=description)

parser.add_argument('-k',
                    f'--{keywords_key}',
                    required=False,
                    nargs='*',
                    help=key_help)

parser.add_argument('-f',
                    f'--{keywords_file_key}',
                    required=False,
                    nargs=1,
                    help=key_file_help)

parser.add_argument('-p',
                    f'--{proxies_key}',
                    required=True,
                    nargs=1,
                    help=proxy_help)


def parse_args():
    args = parser.parse_args()
    keyword_args = args.keywords if isinstance(args.keywords, list) else []
    keyword_file_arg = args.filename[0] if args.filename else ''
    proxies_arg = args.proxies[0] if args.proxies else ''

    if len(keyword_args) < 1 or keyword_file_arg == '' and proxies_arg == '':
        parser.print_help()
        sys.exit(1)

    return {
        keywords_key: keyword_args,
        keywords_file_key: keyword_file_arg,
        proxies_key: os.path.join(os.getcwd(), f'{proxies_arg}'),
    }


def load_keyword_file(key_path: str):
    keywords = []
    if len(key_path) < 1 and os.path.isfile(key_path) is False:
        return keywords
    else:
        with open(key_path, 'r+') as keyword_file:
            lines = [line.strip().split(',')
                     for line in keyword_file.readlines()]
            keywords = [
                keyword.strip() for row in lines for keyword in row if len(keyword) > 1
            ]
    return keywords


def write_results(results: dict):
    json_data = json.dumps(results, indent=4)
    print(f'JSON results: {json_data}')
    print(f'output path: {default_output_file}')
    with open(default_output_file, 'w') as result_file:
        result_file.write(json_data)


def read_results():
    results = {}
    with open(default_output_file, 'r') as result_file:
        text_results = result_file.read()
        results = json.loads(text_results)
    return results


def expand_keywords(keywords: [str], proxy: dict):
    results = {}
    headers = {'User-Agent': user_agent}

    for keyword in keywords:
        url = f'{suggestions_url}{keyword}'
        try:
            res = requests.get(url,
                               headers=headers,
                               proxies=proxy,
                               allow_redirects=False,
                               verify=False)

            if res.status_code == 200:
                parsed_res = json.loads(res.text)[1]
                results[keyword] = parsed_res
                write_results(results)
            else:
                print(f'[!] Results not found for: {keyword}')
                return

        except IOError as ioerr:
            print(f'Keyword Expansion IOError: {ioerr}')
            return


def parse_proxy_file(proxies_file):
    proxies = []
    with open(proxies_file, 'r') as file:
        lines = file.readlines()
        for proxy in lines:
            proxies.append({
                'http': proxy,
                'https': proxy,
            })
    return proxies


def get_proxy(current_proxy=dict, proxies=[dict]):
    random_proxy = random.choice(proxies)

    if len(current_proxy.keys()) < 1:
        return random_proxy

    while random_proxy['http'] == current_proxy['http']:
        random_proxy = random.choice(proxies)

    return random_proxy


class BrowserWrapper():
    firefox_options = FirefoxOptions()
    wire_options = {}
    proxies = []
    proxy_string = None

    def __init__(self):
        self.firefox_options.add_argument('--headless')
        self.set_new_proxy()

    def set_new_proxy(self):
        print('[+] Selecting valid proxy...')
        try:
            self.get_proxy()
            self.wire_options = {
                'proxy': {
                    'http': f'socks5h://{self.proxy_string}',
                    'https': f'socks5h://{self.proxy_string}',
                }
            }
            print(f'[+] Valid proxy selected {self.proxy_string}')
        except Exception as error:
            print(error)
            sys.exit(1)

    def get_google_keyword_results(self, keyword: str):
        # THIS IS PROXY IP TEST WEB PAGE REQUEST
        # Real google searches should check for capchas blocks.
        # When blocked get new IP then recursively call this method
        with webdriver.Firefox(
                options=self.firefox_options,
                seleniumwire_options=self.wire_options) as browser:
            browser.get('http://azenv.net/')
            print(f'page: {browser.page_source}')
            print(f'page url: {browser.current_url}')
            print(f'current proxy: {self.proxy_string}')

    def get_keywords_results(self):
        keywords = ['test1', 'test2', 'test3']
        for keyword in keywords:
            self.get_google_results(keyword)


if __name__ == '__main__':
    proxy = {}
    keywords = []
    args = parse_args()
    keywords_file = args.get(keywords_file_key)
    keywords.extend(args.get(keywords_key))
    keywords.extend(load_keyword_file(keywords_file))
    print('[+] Loaded keywords.')
    proxies = parse_proxy_file(args.get(proxies_key))
    print('[+] Loaded proxies.')
    proxy = get_proxy(proxy, proxies)
    print('[+] Proxy selected.')
    print('[+] Expanding initial keywords.')
    expand_keywords(keywords, proxy=proxy)
    # scrape key results page.
