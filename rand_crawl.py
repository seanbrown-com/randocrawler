import sys
import random
import threading
from os import path
from urllib.error import URLError

from _socket import gaierror
from random_words import RandomWords
from googlesearch import search
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ErrorInResponseException
from selenium.webdriver.chrome.options import Options

output_filename = 'rand_crawl.csv'
output_file_hdr = 'URL,Desktop Result,Mobile Result'


class LockingUrlTable(object):
    def __init__(self):
        self.search_urls = {}  # dict used as a hashtable
        self.lock = threading.Lock()

    def __repr__(self):
        return '<Urls: {}>'.format(self.search_urls)

    def add(self, web_url):
        self.lock.acquire()
        self.search_urls[web_url] = 1
        self.lock.release()

    def lookup(self, web_url):
        self.lock.acquire()
        found = web_url in self.search_urls
        self.lock.release()
        return found


class LockingFileHandle(object):
    def __init__(self, file_path, header):
        self.file_path = file_path
        self.header = header
        self.lock = threading.Lock()

    def __repr__(self):
        return '<File: {}>'.format(self.file_path)

    def initialize(self):
        self.lock.acquire()
        if path.exists(self.file_path):
            file = open(self.file_path, 'r')
            header = file.readline(1)
            file.close()
            if header is not self.header:
                file = open(self.file_path, 'w')
                file.write(self.header)
                file.write('\n')
                file.close()
        else:
            file = open(self.file_path, 'w')
            file.write(self.header)
            file.write('\n')
            file.close()
        self.lock.release()

    def append(self, crawled_url, desktop_result, mobile_result):
        self.lock.acquire()
        file = open(self.file_path, 'a')
        file.write(crawled_url)
        file.write(',')
        file.write(desktop_result)
        file.write(',')
        file.write(mobile_result)
        file.write('\n')
        file.close()
        self.lock.release()


def get_random_search_string():
    rw = RandomWords()
    num_words = random.randint(1, 4)
    search_str = ''
    for x in range(0, num_words):
        word = rw.random_word()
        search_str = '{} {}'.format(search_str, word)
    return search_str


def crawl(browser, crawl_url, ua_str):
    result = 'OK'
    if crawl_url is not None:
        browser.execute_cdp_cmd('Network.setUserAgentOverride', {'userAgent': ua_str})
        try:
            browser.get(crawl_url)
        except (ErrorInResponseException, TimeoutException, URLError, gaierror) as err:
            result = '{}'.format(err)
            result.replace(',', ' ')
    else:
        result = 'URL was empty'
    return result


def crawl_mobile(browser, crawl_url):
    return crawl(browser, crawl_url, 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 '
                                     '(KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19')


def crawl_desktop(browser, crawl_url):
    return crawl(browser, crawl_url, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/74.0.3729.169 Safari/537.36')


def do_crawl(search_urls, searches, results_per_search, output_file):
    driver = webdriver.Chrome()
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    driver.set_page_load_timeout(30)  # request timeout - 30 seconds

    for i in range(searches):
        rand_str = get_random_search_string()
        google_results = None
        try:
            google_results = search(query=rand_str, stop=results_per_search)
        except (URLError, gaierror) as err:
            print('{}'.format(err))
        if google_results is not None:
            for google_url in google_results:
                print('{}->{}'.format(rand_str, google_url))
                if not search_urls.lookup(google_url):
                    desktop_result = crawl_desktop(driver, google_url)
                    mobile_result = crawl_mobile(driver, google_url)
                    output_file.append(google_url, desktop_result, mobile_result)
                    search_urls.add(google_url)
    driver.close()
    driver.quit()


if __name__ == '__main__':
    num_threads = int(sys.argv[1])
    num_searches = int(sys.argv[2])
    num_results_per_search = int(sys.argv[3])
    print('Initializing output...')
    file_handle = LockingFileHandle(output_filename, output_file_hdr)
    url_bucket = LockingUrlTable()

    print('Launching {} crawler(s)'.format(num_threads))
    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=do_crawl, args=(url_bucket, num_searches, num_results_per_search, file_handle))
        threads.append(thread)
        thread.start()

    for thread in threads:
        # Wait for threads to complete
        thread.join()

    print('Search complete. See output file ({}) for results.'.format(output_filename))
