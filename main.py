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
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Global Variables
data_path = os.path.join(os.getcwd(), 'data')
default_output_file = os.path.join(data_path, 'results.json')
suggestions_url = 'http://suggestqueries.google.com/complete/search?output=firefox&q='
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
proxy = {}
proxies = []
wire_options = {}
driver_options = FirefoxOptions()
driver_options.add_argument('--headless')

# Argument Parser Variables
prog = 'Google Topical Map'
description = 'Given target keywords, this program will generate a Google topical map'
key_help = 'A list of space separated target keywords to use'
key_file_help = 'A text file of comma separated target keywords to use'
proxy_help = '''A text file path containing newline separated list of proxies.
Proxy format: <IP-ADDRESS>:<PORT>'''
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
    with open(default_output_file, 'w') as result_file:
        result_file.write(json_data)


def read_results():
    results = {}
    with open(default_output_file, 'r') as result_file:
        text_results = result_file.read()
        results = json.loads(text_results)
    return results


def expand_keywords(keywords: [str]):
    driver = webdriver.Firefox(options=driver_options,seleniumwire_options=wire_options)
    try:
        driver.get('https://www.google.com/')
        #input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "APjFqb")))
        print(driver.page_source)
        print('==> input is clickable.')
    except TimeoutError:
        print('[!] Hit timeout limit.')
    finally:
        driver.quit()


def load_proxies(proxies_file: str):
    global proxies
    with open(proxies_file, 'r') as file:
        lines = file.readlines()
        for proxy in lines:
            parsed_proxy = proxy.strip()
            proxies.append({
                'http': parsed_proxy,
                'https': parsed_proxy,
            })


def set_proxy():
    global proxy
    global proxies
    global wire_options
    random_proxy = random.choice(proxies)
    if len(proxy.keys()) < 1:
        proxy = random_proxy
        wire_options = {'proxy': random_proxy}
        return
    while random_proxy['http'] == proxy['http']:
        random_proxy = random.choice(proxies)
    proxy = random_proxy
    wire_options = {'proxy': random_proxy}
    return


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
    urllib3.disable_warnings()
    keywords = []
    args = parse_args()
    keywords_file = args.get(keywords_file_key)
    keywords.extend(args.get(keywords_key))
    keywords.extend(load_keyword_file(keywords_file))
    print('[+] Loaded keywords.')
    load_proxies(args.get(proxies_key))
    print('[+] Loaded proxies.')
    set_proxy()
    print(f'[+] Proxy selected: {proxy}')
    print('[+] Expanding keywords.')
    expand_keywords(keywords)
    # scrape key results page.
