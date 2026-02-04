from flask import Flask, request, jsonify, Response
from pytubefix import YouTube
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🍪 COOKIES CONFIGURATION
# ---------------------------------------------------------
# Pytubefix mein cookies use karne ke liye 'cookies.txt' file 
# usi folder mein honi chahiye jahan app.py hai.
COOKIES_FILE = 'cookies.txt'

def get_yt_instance(url):
    # Agar cookies file mojud hai to use karein, warna bina cookies ke chalein
    if os.path.exists(COOKIES_FILE):
        return YouTube(url, cookies=COOKIES_FILE)
    return YouTube(url)

@app.route('/')
def home():
    return "🦅 AHMAD RDX - PYTUBEFIX ENGINE (RENDER) LIVE"

# ---------------------------------------------------------
# 🎵 MUSIC/VIDEO INFO & LINK GENERATOR
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query_url = request.args.get('q') # Direct YouTube Link ya Search
    m_type = request.args.get('type', default='audio')
    
    if not query_url: return jsonify({"status": False, "msg": "Link missing!"})

    try:
        yt = get_yt_instance(query_url)
        
        if m_type == 'audio':
            stream = yt.streams.get_audio_only()
        else:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        if not stream:
            return jsonify({"status": False, "msg": "Format available nahi hai."})

        # Real stream link nikalna
        real_url = stream.url
        title = yt.title
        
        # Safe Token (Base64)
        token = base64.b64encode(real_url.encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": title,
            "url": f"{request.host_url}proxy-dl?token={token}&type={m_type}"
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

# ---------------------------------------------------------
# 🛡️ PROXY STREAMER (Render IP Bypass)
# ---------------------------------------------------------
@app.route('/proxy-dl')
def proxy_dl():
    token = request.args.get('token')
    if not token: return Response("No token", status=400)

    try:
        target_url = base64.b64decode(token.encode('ascii')).decode('ascii')
        
        # YouTube headers bypass ke liye
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.youtube.com/"
        }

        def generate():
            with requests.get(target_url, headers=headers, stream=True, timeout=600) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    yield chunk

        return Response(generate(), content_type="application/octet-stream")
    except Exception as e:
        return Response(str(e), status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
