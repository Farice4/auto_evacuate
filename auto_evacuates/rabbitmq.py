import pika


class Py_Rabbitmq(object):
    def __init__(self):
        self.user = 'nova'
        self.pwd = 'irxscf28'
        self.localhost = '127.0.0.1'
        self.port = 5673
        self.credential = pika.PlainCredentials(self.user, self.pwd)
        self.pid = pika.ConnectionParameters(
                self.localhost, self.port, '/', self.credential)
        self.connection = pika.BlockingConnection(self.pid)
        self.channel = self.connection.channel()
        self.msg_list = []

    def callback(self, ch, method, properties, body):
                self.msg_list.append(body)

    def publish(self, msg_list):
        self.channel.exchange_declare(exchange='first', type='fanout')
        self.channel.queue_declare(queue='fence_nodes')
        self.channel.queue_bind(exchange='first', queue='fence_nodes')
        for msg in msg_list:
            self.channel.basic_publish(
                    exchange='first', routing_key='', body=msg)

    def consume(self):
        self.channel.queue_declare(queue='fence_nodes')
        self.channel.basic_consume(
                self.callback, queue='fence_nodes', no_ack=True)
        return self.msg_list
