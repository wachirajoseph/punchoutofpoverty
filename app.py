from flask import Flask, request, jsonify, render_template, session, redirect
import os
import uuid
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION")

FLUTTERWAVE_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "")
FLUTTERWAVE_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "")

# 💰 Allowed donation amounts (IMPORTANT SECURITY FIX)
ALLOWED_AMOUNTS = [10, 25, 50, 100, 200, 500]


@app.route('/')
def home():
    return render_template('index.html')


# ----------------------------
# CREATE DONATION (SECURE)
# ----------------------------
@app.route('/create-donation', methods=['POST'])
def create_donation():
    data = request.get_json()

    amount = data.get("amount")

    # 1. Validate amount strictly
    if amount not in ALLOWED_AMOUNTS:
        return jsonify({"error": "Invalid donation amount"}), 400

    tx_ref = str(uuid.uuid4())

    # Store transaction server-side (important for verification later)
    session["tx_ref"] = tx_ref
    session["amount"] = amount

    payment_url = (
        "https://checkout.flutterwave.com/v3/hosted/pay"
        f"?public_key={FLUTTERWAVE_PUBLIC_KEY}"
        f"&tx_ref={tx_ref}"
        f"&amount={amount}"
        f"&currency=USD"
        f"&redirect_url=http://127.0.0.1:5000/verify-payment"
    )

    return jsonify({"payment_url": payment_url})


# ----------------------------
# PAYMENT VERIFICATION (IMPORTANT)
# ----------------------------
@app.route('/verify-payment')
def verify_payment():
    tx_ref = session.get("tx_ref")

    if not tx_ref:
        return "Invalid session", 400

    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"
    }

    url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}"

    response = requests.get(url, headers=headers)
    result = response.json()

    if result.get("status") == "success":
        status = result["data"]["status"]

        if status == "successful":
            return "🎉 Payment verified successfully. Thank you for supporting POPO!"
        else:
            return "❌ Payment not completed"

    return "Verification failed", 400


if __name__ == '__main__':
    app.run(debug=False)