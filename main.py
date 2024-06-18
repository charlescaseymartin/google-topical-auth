import os
import sys
import json
import random
import requests
import argparse
from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
# from selenium.webdriver.common.by import By

prog = 'Google Topical Auth'
description = 'Given target keywords, this program will generate a topic authority map'
key_help = 'A list of space separated target keywords to use'
key_file_help = 'A text file of comma separated target keywords to use'
proxy_help = 'A text file path that contains a newline separated list of proxies.\nProxy format: <USERNAME>:<PASSWORD>@<IP-ADDRESS>:<PORT>'
data_path = os.path.join(os.getcwd(), 'data')
default_output_file = os.path.join(data_path, 'output.json')
suggestions_url = 'https://www.google.com/complete/search?client=chrome&q='
user_agent = 'Mozilla/23.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0'
keywords_key = 'keywords'
keywords_file_key = 'filename'
proxies_key = 'proxies'
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


def expand_keywords(keywords: [str], keyword_file: str, output_file: str):
    results = {}
    all_keywords = get_all_keywords(keywords, keywords_file)

    for keyword in all_keywords:
        url = f'{suggestions_url}{keyword}'
        response = requests.get(url, headers={'User-Agent': user_agent})
        parsed_response = json.loads(response.text)[1]
        results[keyword] = parsed_response

    return results


class BrowserWrapper():
    firefox_options = FirefoxOptions()
    wire_options = {}
    proxies_file = None
    proxy_string = None

    def __init__(self, proxies_file):
        self.proxies_file = proxies_file
        self.configure_browser()

    def configure_browser(self):
        self.firefox_options.add_argument('--headless')
        # self.options.add_argument('--no-sandbox')
        self.get_new_proxy()
        self.wire_options = {
            'proxy': {
                'http': f'http://{self.proxy_string}',
                'https': f'https://{self.proxy_string}',
                'socks': f'socks5h://{self.proxy_string}',
                'no_proxy': 'localhost,127.0.0.1',
            }
        }

    def get_all_proxies(self):
        proxies = []
        with open(self.proxies_file, 'r') as file:
            lines = file.readlines()
            proxies = [proxy.strip() for proxy in lines]
        return proxies

    def get_new_proxy(self):
        all_proxies = self.get_all_proxies()
        proxy_works = False

        while proxy_works is False:
            new_proxy = random.choice(all_proxies)
            if self.proxy_string != new_proxy:
                try:
                    req_proxy = {"http://": new_proxy}
                    headers = {'User-Agent': user_agent}
                    requests.get('http://azenv.net/',
                                 headers=headers,
                                 proxies=req_proxy,
                                 timeout=10)
                    proxy_works = True
                    self.proxy_string = new_proxy
                except IOError:
                    print(f'Proxy Connection Error: {new_proxy}\n{IOError}')

    def scrape_top_results(self):
        with webdriver.Firefox(
                options=self.firefox_options,
                seleniumwire_options=self.wire_options) as browser:
            browser.get('http://azenv.net/')
            # soup = BeautifulSoup(browser.page_source, 'lxml')
            # ip_item = browser.find_element(By.CSS_SELECTOR, 'li#ip-string')
            print(f'page: {browser.page_source}')
            print(f'page url: {browser.current_url}')
            print(f'current proxy: {self.proxy_string}')


if __name__ == '__main__':
    args = parse_args()
    keywords = args.get(keywords_key)
    keywords_file = args.get(keywords_file_key)
    proxies_file = args.get(proxies_key)
    # expand_keywords(keywords, keywords_file, output_file)
    browser = BrowserWrapper(proxies_file=proxies_file)
    browser.scrape_top_results()
