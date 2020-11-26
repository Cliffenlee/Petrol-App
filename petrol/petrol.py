from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy as alc
import json
import requests
from flask_cors import CORS
from flask_graphql import GraphQLView
from graphene import ObjectType, String, Int, Field, List, Schema, Float
from graphene.types.datetime import Date
from flask_cors import CORS
from os import environ

dbname = "petrol"

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL') + dbname
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = alc(app)

host = '52.221.188.29'
port = 5500




######## GRAPHQL settings ##########
class Petrol(ObjectType):
    name = String()
    rating = Int()
    storage = Float()
    cost = Float()

class Message(ObjectType):
    message = String()

class Pump(ObjectType):
    message = String()
    petrol = Field(Petrol)
    price = Float()

class Query(ObjectType):
    petrol = List(Petrol)
    topup = Field(Message, name = String(), amount = Float())
    pump = Field(Pump, name = String(), amount = Float())

    def resolve_petrol(parent, info):
        r = requests.get("http://{}:{}/petrol".format(host, port)).json()
        return r

    def resolve_topup(parent, info, name, amount):
        details = {
            "name" : name,
            "amount" : amount
        }
        r = requests.put("http://{}:{}/topup".format(host, port), json = details).json()
        return r

    def resolve_pump(parent, info, name, amount):
        details = {
            "name" : name,
            "amount" : amount
        }
        r = requests.put("http://{}:{}/pump".format(host, port), json = details).json()
        return r

petrol_schema = Schema(query = Query)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=petrol_schema, graphiql=True))
######## GraphQL END #########




class Petrol(db.Model):
    __tablename__ = 'petrol'

    name = db.Column(db.String(20), primary_key = True)
    rating = db.Column(db.Integer, nullable = False)
    storage = db.Column(db.Float, nullable = False)
    cost = db.Column(db.Float, nullable = False)

    def __init__(self, name, rating, storage):
        self.name = name
        self.rating = rating
        self.storage = storage
        self.cost = cost

    def json(self):
        return {"name": self.name, "rating": self.rating, "storage": self.storage, "cost": self.cost}

@app.route("/petrol")
def get_all():
    return jsonify([petrol.json() for petrol in Petrol.query.all()]), 200

@app.route("/topup", methods = ['PUT'])
def topup():
    data = request.get_json()
    
    petrol = Petrol.query.filter_by(name = data['name']).first()
    petrol.storage += data['amount']

    try:
        db.session.commit()
    except:
        return jsonify({"message": "Error adding into database"})
    
    return jsonify({"message": "Success!"})

@app.route("/pump", methods = ['PUT'])
def pump():
    data = request.get_json()
    petrol = Petrol.query.filter_by(name = data['name']).first()

    if petrol.storage < data['amount']:
        return jsonify({"message": "Sorry, there is not enough petrol available."}), 400

    petrol.storage -= data['amount']

    try:
        db.session.commit()
    except:
        return jsonify({"message": "There was a problem deducting the amount to the database"}), 500
    
    return jsonify({"petrol": petrol.json(), "price": petrol.cost * data['amount'], "message": "Success!"}), 200


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port=5000, debug=True)
