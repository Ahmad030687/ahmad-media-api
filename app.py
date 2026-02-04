from flask import Flask, request, jsonify, Response
from duckduckgo_search import DDGS
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🚀 UNIVERSAL BYPASS ENGINE (Cobalt Logic)
# ---------------------------------------------------------
def get_media_url(video_url, m_type):
    # Ye aik powerful downloader API hai jo block bypass karti hai
    api_url = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Audio ya Video selection
    payload = {
        "url": video_url,
        "videoQuality": "720", # Video ke liye 720p
        "downloadMode": "audio" if m_type == "audio" else "video",
        "isAudioOnly": True if m_type == "audio" else False
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=20)
        data = response.json()
        if data.get("status") == "stream" or data.get("status") == "redirect":
            return data.get("url")
        elif data.get("status") == "picker": # Agar multiple options milien
            return data["picker"][0]["url"]
        return None
    except:
        return None

@app.route('/')
def home():
    return "🦅 AHMAD RDX - UNIVERSAL ENGINE v4 LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query empty!"})

    try:
        # 1. 🔎 Search (YouTube link nikalna DDG se)
        with DDGS() as ddgs:
            results = list(ddgs.videos(f"{query} site:youtube.com", max_results=1))
            if not results:
                return jsonify({"status": False, "msg": "Nahi mila! Name change karein."})
            
            video_url = results[0]['content']
            title = results[0]['title']

        # 2. ⚡ Get Stream via Universal Bypass
        final_stream = get_media_url(video_url, m_type)
        
        if not final_stream:
            return jsonify({"status": False, "msg": "Engine busy hai, dobara try karein."})

        # 3. 🛡️ Proxy Token (Safe Base64)
        token = base64.b64encode(final_stream.encode('ascii')).decode('ascii')
        
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
    
