from flask import Flask, request, jsonify, render_template, redirect, url_for
# from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from datetime import datetime
import json
import pika
import os
import requests

import csv

import paypalrestsdk as paypal
from paypalrestsdk import *

import stripe

from os import environ

app = Flask(__name__)
# Paypal configuration

file = open ("paypal.txt")
line = file.read().split(",")
client_id = line[0]
client_secret = line[1]

paypal.configure({
    "mode": "sandbox",  # sandbox or live
    "client_id": client_id,
    "client_secret": client_secret})

# dbName = "transaction"

app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# mysql = MySQL(app)

db = SQLAlchemy(app)
CORS(app)

#Stripe configuration
file = open("stripe.txt")
line2 = file.readline().split(",")
pub_key = line2[0]
secret_key = line2[1]

stripe.api_key = secret_key


class Payment(db.Model):
    __tablename__ = 'payment'

    payment_id = db.Column(db.Integer, primary_key=True)
    discount = db.Column(db.Float(), nullable=False)
    percentage = db.Column(db.Float(), nullable=True)
    net_amount = db.Column(db.Float(), nullable=False)
    executed = db.Column(db.Boolean, default=False, nullable=False)

    def json(self):
        return {'payment_id': self.payment_id, 'discount': self.discount, 'net_amount': self.net_amount}

class PaymentUser(db.Model):
    __tablename__ = 'userPayment'

    user_id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, nullable=False)

    def json(self):
        return {'user_id': self.user_id, 'payment_id': self.payment_id}

def to_json(func):
    def wrapper(*args, **kwargs):
        get_fun = func(*args, **kwargs)
        return json.dumps(get_fun)

    return wrapper


@app.route('/paypal_history')
def index():
    history = paypal.Payment.all({"count": 50})
    history_dic = {}
    history_list = []
    for payment in history.payments:
        history_dic['payment_id'] = payment.id
        history_dic['sale_id'] = payment.transactions[0].related_resources[0].sale.id
        history_dic['amount'] = payment.transactions[0].amount.total + " " + history.payments[0].transactions[
            0].amount.currency
        history_dic['type'] = "Paypal"
        history_list.append(history_dic)
        history_dic = {}
        #TODO: Send the payment history in json format to mary
    return jsonify(history_list)


@app.route('/paypal_Return', methods=['GET'])
def paypal_Return():
    # ID of the payment. This ID is provided when creating payment.
    paymentId = request.args['paymentId']
    payer_id = request.args['PayerID']
    payment = paypal.Payment.find(paymentId)
    net_amount = payment.transactions[0].amount['total']

    # PayerID is required to approve the payment.
    if payment.execute({"payer_id": payer_id}):  # return True or False
        paymentRecord = Payment.query.filter_by(payment_id = payment.id).first()
        paymentRecord.executed = 1
        db.session.commit()

        PaymentUserRecord = PaymentUser.query.filter_by(payment_id = payment.id).first()
        db.session.commit()

        user_id = PaymentUserRecord.user_id
        send_amount(net_amount, user_id)
        print("Payment[%s] execute successfully" % (payment.id))
        #mysql statement
        return 'Payment execute successfully!' + payment.id

    else:
        PaymentUser.query.filter_by(payment_id = payment.id).delete()
        print(payment.error)
        return 'Payment execute ERROR!'

@app.route('/paypal_payment', methods=['POST'])
def paypal_payment():
    # Payment
    # A Payment Resource; create one using
    # the above types and intent as 'sale'
    data = request.get_json()

    user_id = data['userid']
    amount = data['amount']

    if 'discount' in data:
        discount = data['discount']
    else:
        discount = 0
    if 'percentage' in data:
        percentage = data['percentage']
    else:
        percentage = 0

    net_amount = round((float(amount)-float(discount))*(100-int(percentage))/100,2)

    paypal_payment = paypal.Payment({
        "intent": "sale",

        # Payer
        # A resource representing a Payer that funds a payment
        # Payment Method as 'paypal'
        "payer": {
            "payment_method": "paypal"},

        # Redirect URLs
        "redirect_urls": {
            "return_url": "http://127.0.0.1:5400/paypal_Return?success=true",
            "cancel_url": "http://127.0.0.1:5400/paypal_Return?cancel=true"},

        # Transaction
        # A transaction defines the contract of a
        # payment - what is the payment for and who
        # is fulfilling it.
        "transactions": [{

            # ItemList
            "item_list": {
                "items": [{
                    "name": "item",
                    "sku": "item",
                    "price": net_amount,
                    "currency": "SGD",
                    "quantity": 1}]},

            # Amount
            # Let's you specify a payment amount.
            "amount": {
                "total": net_amount,
                "currency": "SGD"},
            "description": "Payment made for petrol"}]})
    # Create Payment and return status
    if paypal_payment.create():
        # print(paypal_payment)
        print("Payment[%s] created successfully" % (paypal_payment.id))

        #adds record into transaction table
        # cur = mysql.connection.cursor()
        # cur.execute('''SELECT MAX(id) FROM transaction''')
        # maxid = cur.fetchone()
        # # cur.execute(''' INSERT INTO transaction (payment_id, discount, net_amount, executed) VALUES (%s, %s, %s, %s)''', (maxid[0] +1, discount, amount-discount, False))
        # mysql.connection.commit()

        # user_voucher = UserVoucher(user_id = int(user_id),voucher_id = int(voucher_id))
        payment = Payment(payment_id = paypal_payment.id, discount = float(discount), percentage = percentage, net_amount = net_amount)
        paymentUser = PaymentUser(user_id = user_id, payment_id = paypal_payment.id)
        db.session.add(payment)
        db.session.add(paymentUser)
        db.session.commit()

        # Redirect the user to given approval url
        for link in paypal_payment.links:
            if link.method == "REDIRECT":
                # Convert to str to avoid google appengine unicode issue
                # https://github.com/paypal/rest-api-sdk-python/pull/58
                redirect_url = str(link.href)
                print("Redirect for approval: %s" % (redirect_url))
                # return redirect(redirect_url)
                return jsonify(redirect_url)
    else:
        print("Error while creating payment:")
        print(paypal_payment.error)
        return "Error while creating payment"

@app.route('/send_amount', methods=['GET'])
def send_amount(net_amount, user_id):
    payload = {"userID": user_id,"amt": net_amount}
    r = requests.put("http://g6t3esd.team:5300/updatePoints", json = payload)


@app.route('/stripe')
def stripeIndex():
    return jsonify({"pubkey": pub_key})
    # return render_template('stripe.html', pub_key=pub_key)

@app.route('/thanks')
def thanks():
    userid = request.args['userid']
    amount = request.args['amount']
    send_amount(amount, userid)
    return render_template('thanks.html')

@app.route('/pay', methods=['POST'])
def pay():
    userid = request.form['userid']
    amount = request.form['amount']
    try:
        discount = request.form['discount']
    except:
        discount = 0

    try:
        percentage = request.form['percentage']
    except:
        percentage = 0

    # print(userid)
    # print(amount)
    # print(discount)
    # print(percentage)

    # amount = data['amount']

    net_amount = int((float(amount)-float(discount))*(100-int(percentage))/100*100)

    customer = stripe.Customer.create(email=request.form['stripeEmail'], source=request.form['stripeToken'])

    charge = stripe.Charge.create(
        customer=customer.id,
        amount=net_amount,
        currency='usd',
        description='The Product'
    )

    payment = Payment(payment_id = charge.id, discount = float(discount), percentage = percentage, net_amount = float(net_amount/100), executed = 1)
    paymentUser = PaymentUser(user_id = userid, payment_id = charge.id)
    db.session.add(payment)
    db.session.add(paymentUser)
    db.session.commit()

    return redirect(url_for('thanks', userid=userid, amount=net_amount))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5400, debug=True)
