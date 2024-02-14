#!/usr/bin/env python3
import sqlite3


class Database:
    def __init__(self):
        self._create_table()

    def _create_table(self):
        connection = sqlite3.connect("posts.db")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS posts(username, content);")
        connection.close()

    def insert_post(self, username: str, post_content: str) -> None:
        '''
        Inserts a post into the indicated table.

        :param username: Author of the post
        :para post_content: Content of the post
        :return None
        '''
        connection = sqlite3.connect("posts.db")
        cursor = connection.cursor()
        cursor.execute(
            f"INSERT INTO posts VALUES (?, ?)",
            (username, post_content)
        )
        connection.commit()
        connection.close()
