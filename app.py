from flask import Flask, request, jsonify, Response
import requests
import os

app = Flask(__name__)

# ---------------------------------------------------------
# 📧 TEMP MAIL ENGINE (Headers Fixed)
# ---------------------------------------------------------
ONESEC_API = "https://www.1secmail.com/api/v1/"

# 🛡️ Ye Header lagana zaroori hai taake 1secmail block na kare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

@app.route('/')
def home():
    return "🦅 AHMAD RDX - MAIL SERVER FIXED"

@app.route('/gen-mail')
def gen_mail():
    try:
        url = f"{ONESEC_API}?action=genRandomMailbox&count=1"
        # Headers add kiye hain yahan
        res = requests.get(url, headers=HEADERS)
        
        # Check karein ke response sahi aaya hai ya nahi
        if res.status_code != 200:
            return jsonify({"status": False, "msg": f"API Error: {res.status_code}"})

        data = res.json()
        if data:
            return jsonify({
                "status": True,
                "email": data[0]
            })
        else:
            return jsonify({"status": False, "msg": "Email generate nahi hui."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

@app.route('/check-mail')
def check_mail():
    email = request.args.get('email')
    
    if not email or "@" not in email:
        return jsonify({"status": False, "msg": "Invalid email!"})

    try:
        login, domain = email.split("@")
        
        # Step A: Get Message List
        inbox_url = f"{ONESEC_API}?action=getMessages&login={login}&domain={domain}"
        res = requests.get(inbox_url, headers=HEADERS)
        
        # JSON Decode error se bachne ke liye check
        try:
            msgs = res.json()
        except:
            return jsonify({"status": False, "msg": "Server ne ghalat data diya."})
        
        if not msgs:
            return jsonify({
                "status": True,
                "new_mail": False,
                "msg": "Inbox khali hai."
            })
        
        # Step B: Read Latest Message
        latest_msg = msgs[0]
        msg_id = latest_msg['id']
        
        read_url = f"{ONESEC_API}?action=readMessage&login={login}&domain={domain}&id={msg_id}"
        full_msg = requests.get(read_url, headers=HEADERS).json()
        
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
    
