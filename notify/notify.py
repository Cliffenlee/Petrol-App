from flask import Flask, request, jsonify
import json
import requests
from flask_cors import CORS
import smtplib, ssl

app = Flask(__name__)
CORS(app)
port = 5200

class Telegram:

    def __init__(self):

        with open ('api_token.txt', 'rt') as file:
            api_token = file.read()

        self.base_url = 'https://api.telegram.org/bot{}/'.format(api_token)
        self.send_url = self.base_url + 'sendMessage'

    def send_msg(self, chat_id, message):

        params =  {'chat_id':chat_id, 'text':message}
        r = requests.post(url=self.send_url, params=params)

        return r.status_code

@app.route("/sendNotification", methods = ['POST'])
def send_notif():
    '''take in json request with following fields:
    {
        "channels":  [channel 1, channel 2 ...],
        "promo": {all promo details},
        "message": "promotion message to be sent"
    }
    '''
    data = request.get_json()
    channels = data['channels']
    promo = data['promo']
    tiers = promo['tiers']
    tiers_str = ''.join([str(tier) for tier in tiers])

    query = {"query": "query { getCustomers (tier:" + tiers_str + ") { userID, name, email, teleID } }" }
    r = requests.post("http://g6t3esd.team:8000/customer", json = query, headers = {"apikey": "B6NyqU2uDUwWGGnEi5u2y4zVn7yVXwoW"})
    to_send = r.json()["data"]["getCustomers"]

    details = "promo code: {} \ndiscount: {} \nvalid period: {} - {} \nnumber of redemptions: {}".format(promo['code'], promo['discount'], promo['start'], promo['end'], promo['redemptions'])

    message = promo['name'] + '\n' + data['message'] + '\n' + details

    fail = {}

    if "telegram" in channels:
        tele = Telegram()
        tele_fail = []

        for customer in to_send:
            r = tele.send_msg(customer['teleID'], message)
            print(r)
            if r != 200:
                tele_fail.append(customer["userID"])

        fail["telegram"] = tele_fail


    if "email" in channels:
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = "oiladders@gmail.com"  # Enter your address
        with open ('password.txt', 'rt') as file:
            password = file.read()
        email_fail = []

        context = ssl.create_default_context()
        for customer in to_send:

            if customer["email"]:
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                    server.login(sender_email, password)
                    server.sendmail(sender_email, customer["email"], "Subject:" + message)
            else:
                email_fail.append(customer["email"])

        fail["email"] = email_fail

    return jsonify(fail), 200


if __name__ == "__main__":
    app.run(port=port, debug=True)