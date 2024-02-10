# vBulletin Data Extractor

The point of this repository is to create a data extractor for a [vBulletin](https://www.vbulletin.com/) forum.

# How do I run it?

First, you need to set up a couple of configs. By default the `config.py` file will look for a `config.ini` file, that should contain this structure:

```
[general]
base_url = base URL of your forum

[authentication]
username = a username with access to the forum
password = the password of your user
```

Having configured this, you need to set up a virtual environment, install the dependencies, and let the extraction begin:

```shell
mkdir venv
virtualenv --python=python3 venv
. ./venv/bin/activate
pip3 install -r requirements.txt
./main.py
```
