from flask import Flask, request, jsonify, Response
from duckduckgo_search import DDGS
import requests
import os
import base64

app = Flask(__name__)

# 🛡️ STABLE INVIDIOUS INSTANCES (Backup list)
INSTANCES = [
    "https://invidious.snopyta.org",
    "https://y.com.sb",
    "https://invidious.nerdvpn.de",
    "https://inv.tux.rs"
]

@app.route('/')
def home():
    return "🦅 AHMAD RDX - ULTIMATE BYPASS ENGINE LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query empty!"})

    try:
        # 1. 🔎 Search via DuckDuckGo (YouTube search block bypass)
        video_id = ""
        title = ""
        with DDGS() as ddgs:
            results = list(ddgs.videos(f"{query} site:youtube.com", max_results=1))
            if results:
                # YouTube URL se Video ID nikalna
                video_url = results[0]['content']
                video_id = video_url.split("v=")[1].split("&")[0] if "v=" in video_url else ""
                title = results[0]['title']

        if not video_id:
            return jsonify({"status": False, "msg": "Gana nahi mila!"})

        # 2. ⚡ Get Stream Link via Invidious (Bypass Sign-in)
        stream_url = ""
        for instance in INSTANCES:
            try:
                api_url = f"{instance}/api/v1/videos/{video_id}"
                data = requests.get(api_url, timeout=10).json()
                
                if m_type == 'audio':
                    # Best Audio Stream dhundna
                    if 'adaptiveFormats' in data:
                        audios = [f for f in data['adaptiveFormats'] if 'audio/' in f['type']]
                        if audios:
                            stream_url = audios[0]['url']
                            break
                else:
                    # Best Video Stream dhundna
                    if 'formatStreams' in data:
                        stream_url = data['formatStreams'][0]['url']
                        break
            except:
                continue # Agar aik instance down ho to dusri try karein

        if not stream_url:
            return jsonify({"status": False, "msg": "Stream link block hai ya busy hai."})

        # 3. 🛡️ Safe Token (Base64)
        token = base64.b64encode(stream_url.encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": title,
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
