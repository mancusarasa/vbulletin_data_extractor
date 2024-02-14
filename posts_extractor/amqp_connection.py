#!/usr/bin/env python3
from os import getenv

import pika
from pika.exchange_type import ExchangeType


class AmqpConnection:
    def __init__(self):
        credentials = pika.PlainCredentials(
            getenv('RABBIT_MQ_USER'),
            getenv('RABBIT_MQ_PASS')
        )
        parameters = pika.ConnectionParameters(
            host=getenv('RABBIT_MQ_HOST'),
            port=getenv('RABBIT_MQ_PORT'),
            virtual_host='/',
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange='posts.exchange',
            exchange_type=ExchangeType.direct
        )
        self.channel.queue_declare(queue='posts_queue')
        self.channel.queue_bind(
            exchange='posts.exchange',
            queue='posts_queue',
            routing_key='posts_routing_key'
        )

    def send_message(self, message: str):
        self.channel.basic_publish(
            exchange='posts.exchange',
            routing_key='posts_routing_key',
            body=message
        )
