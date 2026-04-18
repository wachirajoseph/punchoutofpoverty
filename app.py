from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import uuid
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "POPO_SECURE_KEY_2026")

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
FLUTTERWAVE_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "")
FLUTTERWAVE_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY", "")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "punchingoutofpoverty168@gmail.com")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "your_app_password")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")


# -------------------------------------------------
# HOME ROUTE (MESSAGE HANDLER)
# -------------------------------------------------
@app.route('/')
def home():
    msg = request.args.get('msg')

    messages = {
        "sent": "✅ Your message has been sent successfully. We will respond soon.",
        "error": "⚠️ Something went wrong. Please try again later.",
        "donated": "🎉 Thank you for your generous donation to POPO!",
        "failed": "❌ Payment was not successful. Please try again."
    }

    return render_template(
        'index.html',
        success_message=messages.get(msg)
    )


# -------------------------------------------------
# CONTACT FORM (EMAIL SYSTEM)
# -------------------------------------------------
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")

    # Validation
    if not name or not email or not message:
        return redirect(url_for('home', msg="error"))

    subject = f"✨ New Website Message: {name}"
    body = f"""
New inquiry from POPO website:

Name: {name}
Email: {email}

Message:
{message}

---
POPO Contact System
"""

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        msg['Reply-To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.send_message(msg)

    except Exception as e:
        print(f"EMAIL ERROR: {e}")
        return redirect(url_for('home', msg="error"))

    finally:
        try:
            server.quit()
        except:
            pass

    return redirect(url_for('home', msg="sent"))


# -------------------------------------------------
# DONATION CREATION (FLUTTERWAVE)
# -------------------------------------------------
@app.route('/create-donation', methods=['POST'])
def create_donation():
    data = request.get_json()
    amount_raw = data.get("amount")

    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid donation amount"}), 400

    tx_ref = str(uuid.uuid4())
    session["tx_ref"] = tx_ref

    payment_url = (
        "https://checkout.flutterwave.com/v3/hosted/pay"
        f"?public_key={FLUTTERWAVE_PUBLIC_KEY}"
        f"&tx_ref={tx_ref}"
        f"&amount={amount}"
        f"&currency=USD"
        f"&redirect_url={BASE_URL}/verify-payment"
    )

    return jsonify({"payment_url": payment_url})


# -------------------------------------------------
# PAYMENT VERIFICATION
# -------------------------------------------------
@app.route('/verify-payment')
def verify_payment():
    tx_ref = session.get("tx_ref")

    if not tx_ref:
        return redirect(url_for('home', msg="error"))

    headers = {
        "Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"
    }

    url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}"

    try:
        response = requests.get(url, headers=headers)
        result = response.json()

        if (
            result.get("status") == "success"
            and result.get("data", {}).get("status") == "successful"
        ):
            return redirect(url_for('home', msg="donated"))

        return redirect(url_for('home', msg="failed"))

    except Exception as e:
        print(f"PAYMENT ERROR: {e}")
        return redirect(url_for('home', msg="error"))


# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)