#!/usr/bin/env python3

from typing import Optional

import requests
from bs4 import BeautifulSoup

from login import perform_login


def get_content(url: str, session: Optional[requests.Session] = None) -> BeautifulSoup:
    '''
    Retrieves the content of the given website.

    :param url URL of the website whose content we need
    '''
    session = session if session is not None else perform_login()
    try:
        page = session.get(url)
        return BeautifulSoup(page.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f'Error fetching content of {url}')
        raise e
