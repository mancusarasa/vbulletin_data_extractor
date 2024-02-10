#!/usr/bin/env python3
import hashlib

import requests
from urllib3.util.retry import Retry
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
        'vb_login_password': '',
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
