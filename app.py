from flask import Flask, request, jsonify, render_template
import requests
import base64
from datetime import datetime

app = Flask(__name__)

# HOME ROUTE
@app.route('/')
def home():
    return render_template('index.html')


# CONTACT FORM
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    print(f"New Message from {name} ({email}): {message}")

    return jsonify({"status": "success"})


# MPESA STK PUSH
@app.route('/mpesa/stkpush', methods=['POST'])
def stk_push():
    data = request.get_json()
    phone = data.get('phone')
    amount = data.get('amount')

    # 🔐 YOUR CREDENTIALS (replace)
    consumer_key = "YOUR_KEY"
    consumer_secret = "YOUR_SECRET"
    shortcode = "174379"
    passkey = "YOUR_PASSKEY"

    # STEP 1: ACCESS TOKEN
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret))
    access_token = response.json()['access_token']

    # STEP 2: GENERATE PASSWORD
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode('utf-8')

    # STEP 3: STK PUSH
    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": "https://yourdomain.com/callback",
        "AccountReference": "POPO",
        "TransactionDesc": "Donation"
    }

    res = requests.post(stk_url, json=payload, headers=headers)

    return jsonify(res.json())


if __name__ == '__main__':
    app.run(debug=True)