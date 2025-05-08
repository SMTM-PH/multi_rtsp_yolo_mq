# coding=utf-8
### 消费者

import pika
import threading


user_info = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', user_info))
channel = connection.channel()

# 如果指定的queue不存在，则会创建一个queue，如果已经存在 则不会做其他动作，生产者和消费者都做这一步的好处是
# 这样生产者和消费者就没有必要的先后启动顺序了
channel.queue_declare(queue='predicate')

# 回调函数
def callback(ch, method, properties, body):
    print('消费者收到:{}'.format(body))

# channel: 包含channel的一切属性和方法
# method: 包含 consumer_tag, delivery_tag, exchange, redelivered, routing_key
# properties: basic_publish 通过 properties 传入的参数
# body: basic_publish发送的消息

def consume_predicate():
    channel.basic_consume(queue='predicate',  # 接收指定queue的消息
                          auto_ack=True,  # 指定为True，表示消息接收到后自动给消息发送方回复确认，已收到消息
                          on_message_callback=callback  # 设置收到消息的回调函数
                          )
    print('Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

def consume_heartbeat():
    connection_heartbeat = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel_heartbeat = connection_heartbeat.channel()
    channel_heartbeat.queue_declare(queue='heartbeat')
    channel_heartbeat.basic_consume(queue='heartbeat', on_message_callback=callback, auto_ack=True)
    print('Waiting for heartbeats. To exit press CTRL+C')
    channel_heartbeat.start_consuming()

# 创建并启动两个线程
threading.Thread(target=consume_predicate).start()
threading.Thread(target=consume_heartbeat).start()
