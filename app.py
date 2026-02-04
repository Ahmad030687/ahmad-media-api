from flask import Flask, request, jsonify, Response
import requests
import string
import random
import os

app = Flask(__name__)

# ---------------------------------------------------------
# 🛡️ MAIL.TM ENGINE (High Aura / Anti-Block)
# ---------------------------------------------------------
API_BASE = "https://api.mail.tm"

def get_domain():
    # Mail.tm se available domains nikalna
    try:
        res = requests.get(f"{API_BASE}/domains").json()
        return res['hydra:member'][0]['domain']
    except:
        return "vjuum.com" # Fallback domain

@app.route('/')
def home():
    return "🦅 AHMAD RDX - PREMIUM MAIL ENGINE LIVE"

# 1. NEW EMAIL GENERATOR
@app.route('/gen-mail')
def gen_mail():
    try:
        # Step 1: Random ID aur Password banana
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        password = "AhmadRdxPassword123"
        domain = get_domain()
        email = f"{random_id}@{domain}"

        # Step 2: Account register karna Mail.tm par
        payload = {
            "address": email,
            "password": password
        }
        res = requests.post(f"{API_BASE}/accounts", json=payload)
        
        if res.status_code == 201:
            return jsonify({
                "status": True,
                "email": email,
                "password": password,
                "msg": "Account created! OTP check karne ke liye /check-mail use karein."
            })
        else:
            return jsonify({"status": False, "msg": "Koyeb IP is restricted. Trying alternative..."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

# 2. INBOX CHECKER (Token Based)
@app.route('/check-mail')
def check_mail():
    email = request.args.get('email')
    password = "AhmadRdxPassword123" # Jo humne gen-mail mein rakha tha

    if not email: return jsonify({"status": False, "msg": "Email missing!"})

    try:
        # Step 1: Login karke Token lena
        login_res = requests.post(f"{API_BASE}/token", json={"address": email, "password": password}).json()
        token = login_res.get('token')
        
        if not token:
            return jsonify({"status": False, "msg": "Login fail! Email expire ho gayi ya password ghalat hai."})

        # Step 2: Messages fetch karna
        headers = {"Authorization": f"Bearer {token}"}
        msgs = requests.get(f"{API_BASE}/messages", headers=headers).json()
        
        if not msgs['hydra:member']:
            return jsonify({"status": True, "new_mail": False, "msg": "Inbox khali hai."})

        # Step 3: Latest message parhna
        msg_id = msgs['hydra:member'][0]['id']
        full_msg = requests.get(f"{API_BASE}/messages/{msg_id}", headers=headers).json()

        return jsonify({
            "status": True,
            "new_mail": True,
            "from": full_msg['from']['address'],
            "subject": full_msg['subject'],
            "body": full_msg.get('text', 'No text content'),
            "date": full_msg['createdAt']
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
