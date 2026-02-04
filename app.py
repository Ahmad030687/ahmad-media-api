from flask import Flask, request, jsonify, Response
import requests
import os

app = Flask(__name__)

# ---------------------------------------------------------
# 📧 TEMP MAIL ENGINE (1SecMail API)
# ---------------------------------------------------------
# Ye wo service hai jo humein free emails degi
ONESEC_API = "https://www.1secmail.com/api/v1/"

@app.route('/')
def home():
    return "🦅 AHMAD RDX - MAIL SERVER LIVE"

# 1. Email Generate Karne Ka Route
@app.route('/gen-mail')
def gen_mail():
    try:
        # 1secmail se naya email mangna
        url = f"{ONESEC_API}?action=genRandomMailbox&count=1"
        res = requests.get(url).json()
        
        if res:
            return jsonify({
                "status": True,
                "email": res[0] # Pehla email utha lo
            })
        else:
            return jsonify({"status": False, "msg": "Server busy hai."})
    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

# 2. Inbox/OTP Check Karne Ka Route
@app.route('/check-mail')
def check_mail():
    email = request.args.get('email')
    
    if not email or "@" not in email:
        return jsonify({"status": False, "msg": "Email kon dega bhai?"})

    try:
        # Email ko user aur domain mein torna (ahmad@1sec -> ahmad, 1sec)
        login, domain = email.split("@")
        
        # Step A: Messages ki list mangna
        inbox_url = f"{ONESEC_API}?action=getMessages&login={login}&domain={domain}"
        msgs = requests.get(inbox_url).json()
        
        # Agar inbox khali hai
        if not msgs:
            return jsonify({
                "status": True,
                "new_mail": False,
                "msg": "Abhi koi mail nahi aaya. Thora wait karein."
            })
        
        # Step B: Agar mail hai, to latest wali parho
        latest_msg = msgs[0] # Sab se upar wali mail
        msg_id = latest_msg['id']
        
        # Full content download karna
        read_url = f"{ONESEC_API}?action=readMessage&login={login}&domain={domain}&id={msg_id}"
        full_msg = requests.get(read_url).json()
        
        return jsonify({
            "status": True,
            "new_mail": True,
            "from": full_msg.get('from'),
            "subject": full_msg.get('subject'),
            "date": full_msg.get('date'),
            "body": full_msg.get('textBody', 'No text content')
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
