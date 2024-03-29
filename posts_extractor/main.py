#!/usr/bin/env python3

from sys import exit
from typing import Set, Tuple
from urllib.parse import urljoin
import re
from json import dumps
import logging

from bs4 import BeautifulSoup
import requests

from config import app_config
from login import perform_login
from page import get_content

from amqp_connection import AmqpConnection


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)


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
        soup = get_content(base_url, session)
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
    try:
        soup = get_content(forum_url)
    except requests.exceptions.RequestException as e:
        logger.warning(f'Skipping forum {forum_url} from extract_forum_pages')
        return set([forum_url])
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
    soup = get_content(forum_url)
    for link in soup.find_all('a'):
        href = link.get('href')
        if href is None:
            continue
        if re.match('^showthread\.php\?t=[0-9]+$', href):
            thread_url = urljoin(forum_url, href)
            threads_urls.add(thread_url)
    return threads_urls


def extract_thread_pages(thread_url: str) -> Set[str]:
    '''
    Extracts a set of urls, representing the list of pages 
    present in the indicated thread_url.

    :param str thread_url thread whose pages we need
    :return Set[str] set of urls with the pages of the thread.
    '''
    session = perform_login()
    try:
        soup = get_content(thread_url)
    except requests.exceptions.RequestException as e:
        logger.warning(f'Skipping thread {thread_url} from extract_thread_pages')
        return set([thread_url])
    pages_count = 1
    for td in soup.find_all('td', class_='vbmenu_control'):
        for content in td.contents:
            if match := re.match('^Pagina 1 de ([0-9]+)$', str(content)):
                pages_count = int(match.group(1))
                break
    return set(f'{thread_url}&page={page}' for page in range(1, pages_count+1))


def extract_posts(thread_page_url: str) -> Set[Tuple[str, str]]:
    posts = set()
    try:
        soup = get_content(thread_page_url)
    except requests.exceptions.RequestException as e:
        logger.warning(f'Skipping thread page {thread_page_url} from extract_posts')
        return posts
    for post in soup.find_all('table', id=lambda post_id: post_id and re.match('^post[0-9]+$', post_id)):
        username_tag = post.find(class_='bigusername')
        if username_tag:
            username = str(username_tag.contents[0])
        else:
            # deleted/guest users have their usernames defined differently
            username = str(post.find(id=lambda i: i and re.match('^postmenu_[0-9]+$', i)).contents[0])
        post_content = ' '.join([str(c) for c in post.find(id=lambda i: i and re.match('^post_message_[0-9]+$', i)).contents])
        posts.add((username, post_content))
    return posts


if __name__ == '__main__':
    connection = AmqpConnection()
    base_url = app_config.get('general', 'base_url')
    forums = extract_forums(base_url)
    for forum in forums:
        forum_pages = extract_forum_pages(forum)
        for forum_page in forum_pages:
            threads = extract_threads(forum_page)
            for thread in threads:
                thread_pages = extract_thread_pages(thread)
                for thread_page in thread_pages:
                    posts = extract_posts(thread_page)
                    message = [
                        {
                            'username': username,
                            'content': content
                        } for username, content in posts
                    ]
                    connection.send_message(dumps(message))
