#!/usr/bin/env python3

from typing import List
from typing import Set
from urllib.parse import urljoin
import re
import hashlib
from urllib3.util.retry import Retry
from typing import Optional

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter

from config import app_config


def perform_login() -> requests.Session:
    '''
    Performs a login to the main page of the forum.
    Returns a requests.Session object, which we'll use
    later to authenticate our subsequent requests
    when fetching the contents of a given thread
    '''
    base_url = app_config.get('general', 'base_url')
    username = app_config.get('authentication', 'username')
    password = app_config.get('authentication', 'password')
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    # we'll just spoof the user agent in our request
    # for the time being
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Connection': 'keep-alive'
    }
    data = {
        'vb_login_username': username,
        'vb_login_password': password,
        'vb_login_md5password': hashlib.md5(password.encode()).hexdigest(),
        'vb_login_md5password_utf': hashlib.md5(password.encode()).hexdigest(),
        'cookieuser': 1,
        'do': 'login',
        's': '',
        'securitytoken': 'guest'
    }
    session.post(
        f'{base_url}login.php?do=login',
        data=data,
        headers=headers
    )
    return session


def extract_forums(base_url: str) -> Set[str]:
    '''
    Extracts all the forums. Performs a recursive search to
    analyze subforums of forums.

    :param str base_url: url to begin the recursive search.
    :return Set[str] set of all the subforums' urls.
    '''
    session = perform_login()
    forums = set()
    recursively_extract_forums(base_url, session, forums)
    return forums

def recursively_extract_forums(base_url: str, session: requests.Session, forums: Set[str]):
    '''
    Recursively extracts the list of subforums nested below
    base_url

    :param str base_url base url of the vbulleting forum
    :param requests.Session session object to use for requests
    :return List[str] list of urls of the subforums
    '''
    # FIXME: exclude do=markread from here
    try:
        page = session.get(base_url)
    except requests.exceptions.RequestException as e:
        print(f'Skipping {base_url}')
        return
    soup = BeautifulSoup(page.text, 'html.parser')
    for link in soup.find_all('a'):
        href = link.get('href')
        if href is None:
            continue
        if re.match('^forumdisplay\.php\?f=[0-9]+$', href):
            subforum_url = urljoin(base_url, href)
            if subforum_url not in forums:
                forums.add(subforum_url)
                recursively_extract_forums(subforum_url, session, forums)


def extract_threads(forum_url: str) -> Set[str]:
    '''
    Obtains the urls of all the threads present
    in the indicated forum.

    :param str forum_url: full url of the subforum to search.
    :return set of all the urls of the threads in the subforum.
    '''
    threads_urls = set()
    session = perform_login()
    try:
        page = session.get(forum_url)
    except requests.exceptions.RequestException:
        print(f'Skipping subforum {forum_url}')
    soup = BeautifulSoup(page.text, 'html.parser')
    # check for pages

    for link in soup.find_all('a'):
        href = link.get('href')
        if href is None:
            continue
        if re.match('^showthread\.php\?t=[0-9]+$', href):
            thread_url = urljoin(forum_url, href)
            threads_urls.add(thread_url)
    return threads_urls

if __name__ == '__main__':
    base_url = app_config.get('general', 'base_url')
    forums = extract_forums(base_url)
    for forum in forums:
        print(extract_threads(forum))
