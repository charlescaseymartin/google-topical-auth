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


def get_all_keywords(direct_keys: [str], key_file_dir: str):
    keywords = []
    loaded_file_keywords = load_keyword_file(key_file_dir)
    keywords.extend(direct_keys)
    keywords.extend(loaded_file_keywords)
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


def expand_keywords(keywords: [str], keyword_file: str, proxy: str):
    results = {}
    all_keywords = get_all_keywords(keywords, keywords_file)
    headers = {'User-Agent': user_agent}
    proxies = {
        'http': f'socks5h://{proxy}',
        'https': f'socks5h://{proxy}',
    }

    for keyword in all_keywords:
        url = f'{suggestions_url}{keyword}'
        # url = 'http://azenv.net/'
        try:
            with requests.Session() as ses:
                res = ses.get(url,
                              headers=headers,
                              proxies=proxies,
                              allow_redirects=True,
                              verify=False)

                print(f'[#] Suggestion HTML: {res.text}')
                print(f'[#] Suggestion status code: {res.status_code}')
                print(f'[#] Suggestion url: {res.url}')
                print(f'[#] Suggestion history: {res.history}')

                if res.status_code == 200:
                    parsed_res = json.loads(res.text)[1]
                    results[keyword] = parsed_res
                    write_results(results)
                else:
                    print('[!] Unsuccesful response')
                    return
                # res = requests.get(url,
                #                    headers=headers,
                #                    proxies=proxies,
                #                    #allow_redirects=False,
                #                    verify=False)
                # print(f'[#] Suggestion HTML: {res.text}')
                # print(f'[#] Suggestion status code: {res.status_code}')
                # print(f'[#] Suggestion url: {res.url}')
                # print(f'[#] Suggestion history: {res.history}')
                # if res.status_code == 200:
                #     parsed_res = json.loads(res.text)[1]
                #     results[keyword] = parsed_res


        except IOError as ioerr:
            print(f'Keyword Expansion IOError: {ioerr}')
            return


def parse_proxy_file(proxies_file):
    proxies = []
    with open(proxies_file, 'r') as file:
        lines = file.readlines()
        proxies = [proxy.strip() for proxy in lines]
    return proxies


class BrowserWrapper():
    firefox_options = FirefoxOptions()
    wire_options = {}
    proxies = []
    invalid_proxies = []
    proxy_string = None

    def __init__(self, proxies):
        self.proxies = proxies
        self.firefox_options.add_argument('--headless')
        self.set_new_proxy()

    def get_valid_proxy(self):
        proxy_works = False

        while proxy_works is False:
            no_proxies = len(self.proxies) < 1
            if no_proxies and len(self.invalid_proxies) > 1:
                print(f'[#] Invalid proxies: {self.invalid_proxies}')
                raise Exception('[!] No valid proxies found.')
            elif no_proxies:
                raise Exception('[!] No proxies given for use.')

            new_proxy = random.choice(self.proxies)
            if self.proxy_string != new_proxy and new_proxy not in self.invalid_proxies:
                self.proxies.remove(new_proxy)
                self.invalid_proxies.append(new_proxy)
                print(f'[#] Trying {new_proxy}')
                try:
                    req_proxy = {
                        'http': f'socks5h://{new_proxy}',
                        'https': f'socks5h://{new_proxy}',
                    }
                    headers = {'User-Agent': user_agent}
                    res = requests.get('http://azenv.net/',
                                       headers=headers,
                                       proxies=req_proxy,
                                       timeout=5,
                                       verify=False)
                    # print(f'[#] IP test response: {res.text}')
                    print(f'[#] IP test status code: {res.status_code}')
                    if res.status_code == 200:
                        proxy_works = True
                        self.proxy_string = new_proxy
                    else:
                        proxy_works = False
                except IOError as error:
                    proxy_works = False
                    print(f'[#] IOError: {error}')

    def set_new_proxy(self):
        print('[+] Selecting valid proxy...')
        try:
            self.get_valid_proxy()
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
    args = parse_args()
    keywords = args.get(keywords_key)
    keywords_file = args.get(keywords_file_key)
    proxies = parse_proxy_file(args.get(proxies_key))
    # proxies = ['13.40.239.130:1080']
    print('[+] Loaded proxies.')
    browser = BrowserWrapper(proxies=proxies)
    print('[+] Initialized browser.')
    expand_keywords(keywords, keywords_file, proxy=browser.proxy_string)
    # browser.get_keywords_results()
