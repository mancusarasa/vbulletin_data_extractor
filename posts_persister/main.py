#!/usr/bin/env python3
from os import getenv
from sys import exit

import pika
from pika.adapters.asyncio_connection import AsyncioConnection

# This is based on the tutorial included in
# https://github.com/pika/pika/blob/main/examples/asyncio_consumer_example.py
# but omiting the steps of declaring the exchange/
# binding the queue, since we're using the default exchange.


class AmqpConsumer:
    '''
    This is a messages consumer which will handle (some)
    unexpected interactions with RabbitMQ, such as channel/connection
    closures.
    '''
    def __init__(self):
        credentials = pika.PlainCredentials(
            getenv('RABBIT_MQ_USER'),
            getenv('RABBIT_MQ_PASS')
        )
        self._parameters = pika.ConnectionParameters(
            host=getenv('RABBIT_MQ_HOST'),
            port=getenv('RABBIT_MQ_PORT'),
            virtual_host='/',
            credentials=credentials
        )
        self._connection = None
        self._channel = None
        self._consumer_tag = None

    def run(self) -> None:
        '''
        Starts the messages consumer. Internally connects to RabbitMQ
        and starts the ioloop of the connection.
        '''
        self._connection = self.connect()
        self._connection.ioloop.run_forever()

    def connect(self) -> pika.adapters.asyncio_connection.AsyncioConnection:
        '''
        This method connects to RabbitMQ, returning the
        connection handle. The way this is configured will
        make pika invoke self.on_connection_open when the
        connection is open.

        :return pika.adapters.asyncio_connection.AsyncioConnection
        '''
        return AsyncioConnection(
            parameters=self._parameters,
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed
        )

    def on_connection_open(self, connection) -> None:
        '''
        Pika will invoke this method when the connection
        to RabbitMQ is established. It will (unnecessarily) pass
        the connection handle as a parameter.

        :param pika.adapters.asyncio_connection.AsyncioConnection connection:
           The connection
        '''
        self.open_channel()

    def on_connection_open_error(self, connection, error) -> None:
        '''
        This method is invoked by pika if the connection to RabbitMQ
        couldn't be established. I'm leaving it blank for now.

        :param pika.adapters.asyncio_connection.AsyncioConnection connection:
           The connection
        :param Exception err: The error
        '''
        print(f'Unable to open connection. Reason: {str(error)}')
        exit(1)

    def on_connection_closed(self, connection, reason) -> None:
        '''
        This method is invoked by pika when the connection is closed
        unexpectedly. I'm leaving it blank for now.

        :param pika.connection.Connection connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of
            connection.
        '''
        print(f'Connection closed unexpectedly. Reason: {reason}')
        exit(1)

    def open_channel(self) -> None:
        '''
        Opens a new channel with RabbitMQ. Once RabbitMQ responds that
        the channel is open, Pika will invoke self.on_channel_open,
        passing the open channel as a parameter.
        '''
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel) -> None:
        '''
        Pika will invoke this method when the channel has actually
        been opened, passing the channel object along.

        Once the channel has been opened, we will directly declare
        the queue (since we're using the default exchange here, we
        don't need to declare it or bind the queue to it).
        '''
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)
        self._channel.queue_declare(
            queue='my_queue',
            callback=self.on_queue_declare_ok
        )

    def on_queue_declare_ok(self, frame) -> None:
        '''
        This method is called by Pika when the queue was
        declared correctly (after a sucessfull call to queue_declare).
        When using a non-default exchange. we should bind the queue
        to the exchange. Since in this case we're using the default
        exchange, we're skipping this step and directly setting the
        QoS.

        We will setup the QoS to only receive
        one message at a time, which we need to ACK before RabbitMQ is
        allowed to send another one. Note that the prefetch_count is
        configurable and thus open to experimentation.

        :param pika.frame.Method _unused_frame: The Queue.DeclareOk frame
        '''
        self._channel.basic_qos(
            prefetch_count=1,
            callback=self.on_basic_qos_ok
        )

    def on_basic_qos_ok(self, frame) -> None:
        '''
        Pika will invoke this method once the call to basic_qos
        has been invoked succesfully. At this point we're ready
        to start consuming messages, which we'll do by setting
        the self.on_message callback for this purpose.
        '''
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)
        self._consumer_tag = self._channel.basic_consume(
            'my_queue',
            self.on_message
        )

    def on_consumer_cancelled(self, frame) -> None:
        '''
        This method will be invoked by Pika when RabbitMQ sends
        a Basic.Cancel for a consumer receiving messages. In
        our case, we'll close the channel.
        '''
        if self._channel:
            self._channel.close()

    def on_channel_closed(self, channel, reason) -> None:
        # FIXME: check out the boolean handling of situations
        # where the connection is attempted to close multiple times
        self._connection.close()

    def on_message(self, channel, basic_deliver, properties, body):
        '''
        This is the actual method that processes an individual
        message received from the queue. This method needs to
        perform an ACK to RabbitMQ, in order to indicate it has
        been received.
        '''
        print(body)
        self._channel.basic_ack(basic_deliver.delivery_tag)


if __name__ == '__main__':
    consumer = AmqpConsumer()
    consumer.run()
