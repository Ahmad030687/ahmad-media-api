from flask import Flask, request, jsonify, Response
import requests
import re
import os
import base64
import random

app = Flask(__name__)

# ---------------------------------------------------------
# 🦆 DUCKDUCKGO SEARCH (Bypass YouTube Block)
# ---------------------------------------------------------
def search_via_ddg(query):
    # Agar direct link hai
    if "youtube.com" in query or "youtu.be" in query:
        return query, "YouTube Link"

    try:
        # DuckDuckGo HTML search (Bohat halka aur fast)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Hum specifically youtube.com site search kar rahe hain
        ddg_url = f"https://html.duckduckgo.com/html/?q={query}+site:youtube.com"
        
        res = requests.get(ddg_url, headers=headers, timeout=10).text
        
        # Regex se pehla YouTube link nikalna
        # Ye pattern dhoondta hai: watch?v=VIDEO_ID
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', res)
        
        if video_ids:
            # Pehla result
            video_id = video_ids[0]
            print(f"DuckDuckGo found ID: {video_id}")
            return f"https://www.youtube.com/watch?v={video_id}", "Media Found"
            
    except Exception as e:
        print(f"DDG Error: {e}")
    
    return None, None

# ---------------------------------------------------------
# ⚙️ COBALT API (The Ultimate Downloader)
# ---------------------------------------------------------
# Cobalt ke multiple instances taake agar aik down ho to doosra chale
COBALT_INSTANCES = [
    "https://api.cobalt.tools",
    "https://cobalt.kn1.us",
    "https://cobalt.q14.pw",
    "https://cobalt.kwiatekmiki.pl"
]

def get_cobalt_stream(url, m_type):
    # Data prepare karna
    payload = {
        "url": url,
        "videoQuality": "720",
        "audioFormat": "mp3",
        "isAudioOnly": (m_type == 'audio')
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Compatible; AhmadBot/1.0)"
    }

    # Servers try karna
    for instance in COBALT_INSTANCES:
        try:
            print(f"Trying Cobalt: {instance}")
            api_url = f"{instance}/api/json"
            res = requests.post(api_url, json=payload, headers=headers, timeout=10).json()
            
            # Agar success ho
            if 'url' in res:
                return {
                    "url": res['url'],
                    "title": "Cobalt Media", # Cobalt aksar title nahi deta, par link pakka deta hai
                    "duration": "0:00"
                }
        except Exception as e:
            print(f"Cobalt {instance} failed: {e}")
            continue

    return None

# ---------------------------------------------------------
# 🚀 API ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - COBALT HYBRID ENGINE LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    try:
        # STEP 1: Search (DuckDuckGo se)
        real_link, title_hint = search_via_ddg(query)
        
        if not real_link:
            return jsonify({
                "status": False, 
                "msg": "Search fail. DuckDuckGo ne result nahi diya."
            })

        # STEP 2: Extraction (Cobalt API se)
        data = get_cobalt_stream(real_link, m_type)
        
        if not data:
            return jsonify({
                "status": False,
                "msg": "Download fail. Cobalt servers busy hain."
            })

        # Proxy Token
        token = base64.b64encode(data['url'].encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": data['title'], # Note: Cobalt shayad title generic de
            "duration": data['duration'],
            "url": f"{request.host_url}proxy-dl?token={token}&type={m_type}"
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

@app.route('/proxy-dl')
def proxy_dl():
    token = request.args.get('token')
    m_type = request.args.get('type', 'audio')
    if not token: return Response("No token", status=400)

    try:
        target_url = base64.b64decode(token.encode('ascii')).decode('ascii')
        headers = {"User-Agent": "Mozilla/5.0"}

        def generate():
            with requests.get(target_url, headers=headers, stream=True, timeout=600) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    yield chunk

        c_type = "video/mp4" if m_type == "video" else "audio/mpeg"
        return Response(generate(), content_type=c_type)
    except Exception as e:
        return Response(str(e), status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
