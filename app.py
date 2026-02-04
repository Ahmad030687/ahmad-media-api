from flask import Flask, request, jsonify, Response
from duckduckgo_search import DDGS # Is se YouTube search block bypass hoga
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛠️ HELPER: Mobile Stream Extractor
# ---------------------------------------------------------
def get_stream_link(video_url, m_type):
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}}, # 📱 Mobile Bypass
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info.get('url'), info.get('title', 'Media File')

# ---------------------------------------------------------
# 🎵 MUSIC/VIDEO DOWNLOADER
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    try:
        # 1. 🔎 SEARCH PHASE (Using DuckDuckGo to find YouTube Link)
        with DDGS() as ddgs:
            # Hum sirf YouTube ke results mangwa rahe hain
            search_query = f"{query} site:youtube.com"
            results = list(ddgs.videos(search_query, max_results=1))
            
            if not results:
                return jsonify({"status": False, "msg": "Nahi mila! Name change karein."})
            
            video_url = results[0]['content'] # YouTube URL
            title = results[0]['title']

        # 2. ⚡ STREAM PHASE
        real_stream_url, official_title = get_stream_link(video_url, m_type)
        
        # 3. 🛡️ PROXY TOKEN (Safe Base64)
        token = base64.b64encode(real_stream_url.encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": official_title,
            "url": f"{request.host_url}proxy-dl?token={token}&type={m_type}"
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

# ---------------------------------------------------------
# 🛡️ PROXY STREAMER
# ---------------------------------------------------------
@app.route('/proxy-dl')
def proxy_dl():
    token = request.args.get('token')
    m_type = request.args.get('type', 'audio')
    if not token: return Response("No token", status=400)

    try:
        target_url = base64.b64decode(token.encode('ascii')).decode('ascii')
        headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"}

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
    
