#!/usr/bin/env python3
from configparser import ConfigParser
from pathlib import Path


class Config:
    def __init__(self, filename: str):
        self.parser = ConfigParser()
        with open(filename) as f:
            self.parser.read_file(f)

    def get(self, section: str, key: str) -> str:
        return self.parser.get(section, key)


current_directory = Path(__file__).parent.resolve()
app_config = Config(f'{current_directory}/config.ini')
