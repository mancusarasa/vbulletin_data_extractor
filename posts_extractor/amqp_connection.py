#!/usr/bin/env python3
from os import getenv

import pika


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
        self.channel.queue_declare(queue='my_queue')

    def send_message(self, message: str):
        self.channel.basic_publish(
            exchange='',
            routing_key='my_queue',
            body=message
        )
