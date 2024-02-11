# vBulletin Data Extractor

The point of this repository is to create a data extractor for a [vBulletin](https://www.vbulletin.com/) forum.

# How do I run it?

First, you'll need valid credentials for the forum whose posts you're trying to extract. This must be configured through the `posts_extractor/config.ini` file, which should contain this structure:

```
[general]
base_url = base URL of your forum

[authentication]
username = a username with access to the forum
password = the password of your user
```

After configuring this, you also need to install the latest [docker](https://docs.docker.com/desktop/) release, which includes `docker compose`.

After installing this, you should be good to go: 

```shell
docker compose down && docker compose build && docker compose up
```

This will perform these actions:

- Start the RabbitMQ server, necessary for both `posts_extractor` (which will act as producer in this schema) and `posts_persister` (which will act as the consumer in this schema)
- Start the `posts_extractor` and `posts_persister` services

## Posts extractor

This service is basically a scraper, written in Python3 using the [requests](https://pypi.org/project/requests/) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) packages. It's in charge of obtaining the URLs of all the subforums (including subforums that multiple pages), obtain the URLs of all the threads from every subforum, and finally go through every page of every thread and obtain a list of `(username: str, post_content: str)` tuples. Then, these lists will be sent through RabbitMQ queue (the [pika](https://pika.readthedocs.io/en/stable/) package is also installed for this exact purpose). The actual processing of posts will be performed by Posts persister.

## Posts persister

This service will receive the posts obtained in the extraction phase from RabbitMQ, and perform two actions over them:

- Sanitize the posts (remove HTML tags and quoted posts, which was a vBulletin feature that basically embedded someone else's posts in our own, so we need to get rid of them).
- Store the sanitized posts in a destination database

All of this is pending work, the only part that actually works is obtaining the posts from the RabbitMQ queue.
