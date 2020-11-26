from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy as alc
import json
import requests
from datetime import datetime
import pika
import sys
from os import environ

hostname = "13.229.116.2" # default hostname
port = 5672 # default port
# connect to the broker and set up a communication channel in the connection
connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
    # Note: various network firewalls, filters, gateways (e.g., SMU VPN on wifi), may hinder the connections;
    # If "pika.exceptions.AMQPConnectionError" happens, may try again after disconnecting the wifi and/or disabling firewalls
channel = connection.channel()
# set up the exchange if the exchange doesn't exist
exchangename="promo"
channel.exchange_declare(exchange=exchangename, exchange_type='direct')

app = Flask(__name__)
dbname = "redemption"
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL') + dbname 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = alc(app)

class Redemption(db.Model):
    __tablename__ = 'redemptions'

    code = db.Column(db.String(12), primary_key = True)
    user_id = db.Column(db.Integer, primary_key = True)

    def __init__(self, user_id, code):
        self.code = code
        self.user_id = user_id

    # represent in dict to prep for jsonify
    def json(self):
        return {"user_id": self.user_id, "code": self.code}


def add(user_id, code):
    redemption = Redemption(user_id, code)
    
    try:
        db.session.add(redemption)
        db.session.commit()
    except:
        return {"message": "Error occured when adding redemption into database"}

def redemption():
    # prepare a queue for receiving messages
    channelqueue = channel.queue_declare(queue="redemption", durable=True) # 'durable' makes the queue survive broker restarts so that the messages in it survive broker restarts too
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='redemption.promo') # bind the queue to the exchange via the key

    # set up a consumer and start to wait for coming messages
    channel.basic_qos(prefetch_count=1) # The "Quality of Service" setting makes the broker distribute only one message to a consumer if the consumer is available (i.e., having finished processing and acknowledged all previous messages that it receives)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming() # an implicit loop waiting to receive messages; it doesn't exit by default. Use Ctrl+C in the command window to terminate it.

def callback(channel, method, properties, body): # required signature for the callback; no return
    print("Received an redemption by " + __file__)
    redemption = json.loads(body)
    result = add(**redemption)
    # print processing result; not really needed
    print(json.dump(result, sys.stdout, default=str)) # convert the JSON object to a string and print out on screen
    
    channel.basic_ack(delivery_tag=method.delivery_tag) # acknowledge to the broker that the processing of the request message is completed


if __name__ == "__main__":  # execute this program only if it is run as a script (not by 'import')
    redemption()



