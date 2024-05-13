import os
import sys
import json
import random
import requests
import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
# from selenium.webdriver.common.by import By

prog = 'Google Topical Auth'
description = 'Given target keywords, this program will generate a topic authority map'
key_help = 'A list of space separated target keywords to use'
key_file_help = 'A text file of comma separated target keywords to use'
out_file_help = 'A json file to store the results (default is ./data/output.json)'
data_path = os.path.join(os.getcwd(), 'data')
default_output_file = os.path.join(data_path, 'output.json')
suggestions_url = 'https://www.google.com/complete/search?client=chrome&q='
user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/81.0'
parser = argparse.ArgumentParser(prog=prog, description=description)
parser.add_argument('-k',
                    '--keywords',
                    required=False,
                    nargs='*',
                    help=key_help)

parser.add_argument('-f',
                    '--filename',
                    required=False,
                    nargs=1,
                    help=key_file_help)

parser.add_argument('-o',
                    '--output',
                    required=False,
                    nargs=1,
                    help=out_file_help)


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
    output_file_arg = args.output[0] if args.output else default_output_file

    if len(keyword_args) < 1 and keyword_file_arg == '':
        parser.print_help()
        sys.exit(1)

    return {
        'keywords': keyword_args,
        'keywords_file': keyword_file_arg,
        'output_file': os.path.join(os.getcwd(), f'{output_file_arg}'),
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


class ChromeWrapper():
    options = webdriver.ChromeOptions()
    current_proxy = None

    def __init__(self):
        self.set_webdriver_options()

    def set_webdriver_options(self):
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-dev-shm-usage')
        # proxy = self.get_proxy()
        # self.options.add_argument(f'--proxy-server={proxy}')

    def get_proxy(self):
        all_proxies = []
        proxy_works = False
        user_agent_tag = 'HTTP_USER_AGENT'
        ip_tag = 'REMOTE_ADDR'
        proxy_test_url = 'http://azenv.net/'
        proxies_path = os.path.join(data_path, 'proxies.json')

        with open(proxies_path, 'r') as proxy_file:
            all_proxies = json.loads(proxy_file.read())

        while proxy_works is False:
            new_proxy = random.choice(all_proxies)
            if self.current_proxy != new_proxy:
                try:
                    protocol = new_proxy.split('//')[0][:-1]
                    req_proxy = {protocol: new_proxy}
                    headers = {'User-Agent': user_agent}
                    print(f'-------------\nproxy protocol: {protocol}')
                    print(f'proxy: {new_proxy}')
                    response = requests.get(proxy_test_url,
                                            headers=headers,
                                            proxies=req_proxy,
                                            timeout=10)
                    content = BeautifulSoup(response.content, 'lxml')
                    title = content.find('title').string
                    connect_details = content.find('pre').string.split('\n')
                    details_user_agent = ''
                    details_ip = ''

                    for detail in connect_details:
                        if user_agent_tag in detail:
                            details_user_agent = detail.split(' = ')[-1]
                        if ip_tag in detail:
                            details_ip = detail.split(' = ')[-1]

                    print(f'response code: {response.status_code}')
                    print(f'content title: {title}')
                    print(f'connection details: {connect_details}')
                    print(f'connection IP: {details_ip}')
                    print(f'connection User-Agent: {details_user_agent}')
                    proxy_works = True
                    print('good proxy\n-------------')
                except IOError:
                    print('Connection Error')
        return

    def scrape_top_results(self):
        with webdriver.Chrome(options=self.options) as browser:
            browser.get('https://www.google.com')
            # soup = BeautifulSoup(browser.page_source, 'lxml')
            # ip_item = browser.find_element(By.CSS_SELECTOR, 'li#ip-string')
            print(f'page: {browser.page_source}')


if __name__ == '__main__':
    args = parse_args()
    keywords = args.get('keywords')
    keywords_file = args.get('keywords_file')
    output_file = args.get('output_file')
    # expand_keywords(keywords, keywords_file, output_file)
    browser = ChromeWrapper()
    browser.get_proxy()
