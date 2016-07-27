import pika
import ConfigParser


class Py_Rabbitmq(object):
    def __init__(self):
        self.user = 'nova'
        self.port = 5673
        self.msg_list = []

    def rbt_connection(self):
        cf = ConfigParser.ConfigParser()
        cf.read("/etc/nova/nova.conf")
        pwd = cf.get("DEFAULT", "rabbit_password")
        hosts = cf.get("DEFAULT", "rabbit_hosts")
        hosts_list = hosts.split(',')
        for host_list in hosts_list:
            host = host_list.split(':')
            credential = pika.PlainCredentials(self.user, pwd)
            try:
                pid = pika.ConnectionParameters(
                        host[0], self.port, '/', credential)
                connection = pika.BlockingConnection(pid)
                channel = connection.channel()
                return channel
            except Exception:
                print 'error'

    def callback(self, ch, method, properties, body):
        self.msg_list.append(body)

    def publish(self, msg_list):
        channel = self.rbt_connection()
        channel.exchange_declare(exchange='first', type='fanout')
        channel.queue_declare(queue='fence_nodes')
        channel.queue_bind(exchange='first', queue='fence_nodes')
        for msg in msg_list:
            channel.basic_publish(
                    exchange='first', routing_key='', body=msg)

    def consume(self):
        channel = self.rbt_connection1()
        channel.queue_declare(queue='fence_nodes')
        channel.basic_consume(
                self.callback, queue='fence_nodes', no_ack=True)
        return self.msg_list
