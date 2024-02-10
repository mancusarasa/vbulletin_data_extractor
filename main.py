#!/usr/bin/env python3

from sys import exit
from typing import Set
from urllib.parse import urljoin
import re

from bs4 import BeautifulSoup
import requests

from config import app_config
from login import perform_login


def extract_forums(base_url: str) -> Set[str]:
    '''
    Extracts all the forums. Performs a recursive search to
    analyze subforums of forums.

    :param str base_url: url to begin the recursive search.
    :return Set[str] set of all the subforums' urls.
    '''
    session = perform_login()
    forums = set()
    def recurse(base_url: str, session: requests.Session, forums: Set[str]):
        '''
        Recursively extracts the set of subforums nested below
        base_url

        :param str base_url base url of the vbulleting forum
        :param requests.Session session object to use for requests
        :return Set[str] set of urls of the subforums
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
                    recurse(subforum_url, session, forums)

    recurse(base_url, session, forums)
    return forums


def extract_forum_pages(forum_url: str) -> Set[str]:
    '''
    Extracts a set of urls, representing the list of pages 
    present in the indicated forum_url.

    :param str forum_url url whose pages we need
    :return Set[str] set of urls with the pages of each subforum.
    '''
    session = perform_login()
    try:
        page = session.get(forum_url)
    except requests.exceptions.RequestException as e:
        print(f'Skipping forum {forum_url} from extract_forum_pages')
        return set([forum_url])
    soup = BeautifulSoup(page.text, 'html.parser')
    pages_count = 1
    for td in soup.find_all('td', class_='vbmenu_control'):
        for content in td.contents:
            if match := re.match('^Pagina 1 de ([0-9]+)$', str(content)):
                pages_count = int(match.group(1))
                break
    return set(f'{forum_url}&page={page}' for page in range(1, pages_count+1))


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
        forum_pages = extract_forum_pages(forum)
        for forum_page in forum_pages:
            threads = extract_threads(forum_page)
            print(threads)
