from flask import Flask, request, jsonify, Response
from duckduckgo_search import DDGS
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛠️ HELPER: 100% WORKING STREAM EXTRACTOR
# ---------------------------------------------------------
def get_stream_link(video_url, m_type):
    cookie_path = 'cookies.txt'
    
    # 📱 Mobile bypass settings (iOS/Android clients)
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        # Ye settings bot detection ko bypass karti hain
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'web_embedded'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info.get('url'), info.get('title', 'Media File')

# ---------------------------------------------------------
# 🎵 MUSIC/VIDEO ENDPOINT
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    try:
        # 1. 🔎 SEARCH PHASE (DuckDuckGo Search)
        with DDGS() as ddgs:
            search_query = f"{query} site:youtube.com"
            results = list(ddgs.videos(search_query, max_results=1))
            
            if not results:
                return jsonify({"status": False, "msg": "Nahi mila! Name change karein."})
            
            video_url = results[0]['content']

        # 2. ⚡ STREAM PHASE (Using Mobile Clients)
        real_stream_url, official_title = get_stream_link(video_url, m_type)
        
        # 3. 🛡️ PROXY TOKEN (Base64)
        token = base64.b64encode(real_stream_url.encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": official_title,
            "url": f"{request.host_url}proxy-dl?token={token}&type={m_type}"
        })

    except Exception as e:
        error_msg = str(e)
        # Agar block ho jaye to user ko asaan alfaz mein batana
        if "Sign in" in error_msg:
            return jsonify({"status": False, "msg": "YouTube ne IP block kar di hai. Cookies update karein ya 10 min baad try karein."})
        return jsonify({"status": False, "error": error_msg})

# ---------------------------------------------------------
# 🛡️ PROXY STREAMER (Actual Data Transfer)
# ---------------------------------------------------------
@app.route('/proxy-dl')
def proxy_dl():
    token = request.args.get('token')
    m_type = request.args.get('type', 'audio')
    if not token: return Response("Token missing", status=400)

    try:
        target_url = base64.b64decode(token.encode('ascii')).decode('ascii')
        headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"}

        def generate():
            with requests.get(target_url, headers=headers, stream=True, timeout=600) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=512 * 1024): # 512KB chunks
                    yield chunk

        c_type = "video/mp4" if m_type == "video" else "audio/mpeg"
        return Response(generate(), content_type=c_type)
    except Exception as e:
        return Response(str(e), status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
