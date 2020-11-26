from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy as alc
import json
import requests
from datetime import datetime
import pika
from flask_graphql import GraphQLView
from graphene import ObjectType, String, Int, Field, List, Schema
from graphene.types.datetime import Date
from flask_cors import CORS
from os import environ



app = Flask(__name__)
dbname = "promotions"
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL') + dbname
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
host = '172.31.30.44'
port = 5000






######## GRAPHQL settings ##########

class Promotion(ObjectType):
    code = String()
    discount = Int()
    name = String()
    redemptions = Int()
    start = String()
    end = String()
    message = String()
    tiers = List(Int)

class EndPromo(ObjectType):
    message = String()

class Redeem(ObjectType):
    discount = Int()
    message = String()

class Create(ObjectType):
    message = String()

class Query(ObjectType):
    promotion = Field(Promotion, code = String())
    promotions = List(Promotion)
    tiers = List(Int, code = String())
    create = Field(Create, code = String(), discount = Int(), name = String(), redemptions = Int(), start = String(), end = String(), message = String(), tiers = List(Int))
    redeem = Field(Redeem, code = String(), userId = Int(), tier = Int())
    endPromo = Field(EndPromo, code = String())

    def resolve_promotion(parent, info, code):
        r = requests.get("http://{}:{}/retrieve/{}".format(host, port, code)).json()
        return r
        
    def resolve_promotions(parent, info):
        r = requests.get("http://{}:{}/retrieve".format(host,port)).json()
        return r

    def resolve_tiers(parent, info, code):
        r = requests.get("http://{}:{}/retrieveTiers/{}".format(host, port, code)).json()
        return r

    def resolve_create(parent, info, code, discount, name, redemptions, start, end, message, tiers):
        details = {"discount" : discount,
                    "name" : name,
                    "redemptions" : redemptions,
                    "start" : start,
                    "end" : end,
                    "message" : message,
                    "tiers" : tiers}
        r = requests.post("http://{}:{}/create/{}".format(host, port, code), json = details)
        if r.status_code != 200:
            return r.json()
        return r.json()

    def resolve_redeem(parent, info, code, userId, tier):
        user = {"user_id": userId,
                "tier": tier}
        r = requests.put("http://{}:{}/redeem/{}".format(host, port, code), json = user)
        return r.json()

    def resolve_endPromo(parent, info, code):
        r = requests.put("http://{}:{}/end/{}".format(host, port, code))
        return r.json()

promotion_schema = Schema(query = Query)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=promotion_schema, graphiql=True))
######## GraphQL END #########







db = alc(app)

class Promotions(db.Model):
    __tablename__ = 'promotions'

    code = db.Column(db.String(12), primary_key = True)
    discount = db.Column(db.Integer, nullable = False)
    name = db.Column(db.String(50), nullable = False)
    redemptions = db.Column(db.Integer, nullable = True)
    start_date = db.Column(db.String(10), nullable = False)
    end_date = db.Column(db.String(10), nullable = False)
    message = db.Column(db.String(300), nullable = False)


    def __init__(self, code, discount, name, redemptions, start, end, message, **kwargs):
        self.code = code
        self.discount = discount
        self.name = name
        self.redemptions = redemptions
        self.start_date = start
        self.end_date = end
        self.message = message

    def json(self):
        return {"code": self.code, "discount": self.discount, "name": self.name, "redemptions": self.redemptions, "start": self.start_date, "end": self.end_date, "message": self.message}


class Applicability(db.Model):
    __tablename__ = 'applicability'

    code = db.Column(db.String(12), primary_key = True)
    tier = db.Column(db.Integer, primary_key = True)

    def __init__(self, code, tier):
        self.code = code
        self.tier = tier

    def json(self):
        return {"code": self.code, "tier": self.tier}
        

@app.route("/retrieve") #graphql done
def retrieve_all():
    promotions = [promotion.json() for promotion in Promotions.query.all()]
    for promotion in promotions:
        promotion["start"] = promotion["start"].strftime("%d-%m-%Y")
        promotion["end"] = promotion["end"].strftime("%d-%m-%Y")
        promotion["tiers"] = [app.tier for app in Applicability.query.filter_by(code = promotion["code"]).all()]
    print(promotion)
    
    return jsonify(promotions), 200

@app.route("/retrieve/<string:code>") #graphql done
def retrieve_by_code(code):
    promotion = Promotions.query.filter_by(code = code).first().json()
    promotion["start"] = promotion["start"].strftime("%d-%m-%Y")
    promotion["end"] = promotion["end"].strftime("%d-%m-%Y")
    promotion["tiers"] = [app.tier for app in Applicability.query.filter_by(code = promotion["code"]).all()]
    
    return jsonify(promotion), 200

@app.route("/retrieveTiers/<string:code>") #graphql done
def retrieve_applicability(code):
    tiers = [app.tier for app in Applicability.query.filter_by(code = code).all()]
    return jsonify(tiers), 200


@app.route("/create/<string:code>", methods = ['POST']) #graphql done
def create_promotion(code):

    if Promotions.query.filter_by(code = code).first():
        return jsonify({"message": "A promotion with promo code '{}' already exists.".format(code)}), 400

    data = request.get_json()
    promo = Promotions(code, **data)
    try:
        db.session.add(promo)
        db.session.commit()
    except Exception as e:
        print(e)
        return jsonify({"message": "An error occurred while creating the promotion"}), 500

    tiers = data["tiers"]
    for tier in tiers:
        app = Applicability(code, tier)

        try:
            db.session.add(app)
            db.session.commit()
        except Exception as e:
            print(e)
            return jsonify({"message": "An error occurred while creating the applicability."}), 500  

    return jsonify({"message": "Success!"}), 200

@app.route("/redeem/<string:code>", methods = ['PUT']) #graphql done
def redeem(code):

    promo = Promotions.query.filter_by(code = code).first()
    data = request.get_json()
    user_id = data['user_id']
    tier = data['tier']

    # check correct code
    if promo == None:
        return jsonify({"message": "No such code exists, please try again."}), 400

    # check expiry
    now = datetime.now().date()

    start = promo.start_date
    end = promo.end_date

    if now > end:
        return jsonify({"message": "The promotion has expired!"}), 400
    
    if now < start:
        return jsonify({"message": "The promotion has not started!"})

    # check applicability
    valid = Applicability.query.filter_by(code = code, tier = tier).first()

    if valid == None:
        return jsonify({"message": "Sorry! You are not eligible for this promotion!"}), 400

    # check redemptions left
    if promo.redemptions == 0:
        return jsonify({"message": "Sorry! This promotion has been fully redeemed."})

    # # check if redeemed before
    # if Redeem.query.filter_by(user_id = user_id, code = code).first():
    #     return jsonify({"message": "You have already redeemed this promotion! Thank you!"}), 400

    promo.redemptions -= 1
    
    try:
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred while redeeming."}), 500

    # add to redemption
    redemption = {"user_id": user_id, "code": code}
    send_redemption(redemption)  

    return jsonify({"discount": promo.discount, "message": "Promotion successfully redeemed!"}), 201

def send_redemption(redemption):
    hostname = "13.229.116.2" # default broker hostname. Web management interface default at http://localhost:15672
    port = 5672 # default messaging port.
    # connect to the broker and set up a communication channel in the connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
        # Note: various network firewalls, filters, gateways (e.g., SMU VPN on wifi), may hinder the connections;
        # If "pika.exceptions.AMQPConnectionError" happens, may try again after disconnecting the wifi and/or disabling firewalls
    channel = connection.channel()

    # set up the exchange if the exchange doesn't exist
    exchangename="promo"
    channel.exchange_declare(exchange=exchangename, exchange_type='direct')

    channelqueue = channel.queue_declare(queue="redemption", durable=True) # 'durable' makes the queue survive broker restarts so that the messages in it survive broker restarts too
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='redemption.promo') # bind the queue to the exchange via the key

    message = json.dumps(redemption, default=str) # convert a JSON object to a string

    # send the message
    # always inform Monitoring for logging no matter if successful or not
    channel.basic_publish(exchange=exchangename, routing_key="redemption.promo", body=message)
        # By default, the message is "transient" within the broker;
        #  i.e., if the monitoring is offline or the broker cannot match the routing key for the message, the message is lost.
        # If need durability of a message, need to declare the queue in the sender (see sample code below).


# force end a promo
@app.route("/end/<string:code>", methods = ['PUT']) #graphql done
def end_promo(code):
    end_date = datetime.now().date()

    promo = Promotions.query.filter_by(code = code).first()

    if promo == None:
        return jsonify({"message": "Wrong code"}), 400
    
    promo.end_date = end_date

    try:
        db.session.commit()
    except:
        return jsonify({"message": "An error occured while updating the end_date"}), 500
    
    return jsonify({"message": "Promotion with code {} has been ended.".format(code)}), 200



if __name__ == "__main__":
    app.run(host = '0.0.0.0', port=port, debug=True)
