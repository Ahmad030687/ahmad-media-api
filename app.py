from flask import Flask, request, jsonify, Response
from duckduckgo_search import DDGS
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛠️ BYPASS ENGINE: Android VR & Embedded Clients
# ---------------------------------------------------------
def get_stream_data(video_url, m_type):
    # Ye settings YouTube ki bot detection ko dhoka deti hain
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0',
        # 🛡️ Sabse important bypass settings
        'extractor_args': {
            'youtube': {
                'player_client': ['android_vr', 'web_embedded', 'tvhtml5'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Quest 2) AppleWebKit/537.36 (KHTML, like Gecko) OculusBrowser/15.0.0.0.0 SamsungBrowser/4.0 Chrome/89.0.4389.90 Mobile Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/'
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info.get('url'), info.get('title', 'Ahmad RDX Media'), info.get('duration_string', '0:00')

# ---------------------------------------------------------
# 🎵 MAIN API ENDPOINT
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query empty!"})

    try:
        # 1. 🔎 Search via DuckDuckGo (YouTube search block bypass)
        with DDGS() as ddgs:
            # Hum sirf YouTube ke videos dhoond rahe hain
            results = list(ddgs.videos(f"{query} site:youtube.com", max_results=1))
            
            if not results:
                return jsonify({"status": False, "msg": "Nahi mila! Thora sa naam badlein."})
            
            video_url = results[0]['content']

        # 2. ⚡ Get Stream via Bypass Engine
        real_stream_url, title, duration = get_stream_data(video_url, m_type)
        
        # 3. 🛡️ Safe Token
        token = base64.b64encode(real_stream_url.encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": title,
            "duration": duration,
            "url": f"{request.host_url}proxy-dl?token={token}&type={m_type}"
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

# ---------------------------------------------------------
# 🛡️ PROXY STREAMER (Actual Downloader)
# ---------------------------------------------------------
@app.route('/proxy-dl')
def proxy_dl():
    token = request.args.get('token')
    m_type = request.args.get('type', 'audio')
    if not token: return Response("No token", status=400)

    try:
        target_url = base64.b64decode(token.encode('ascii')).decode('ascii')
        headers = {"User-Agent": "Mozilla/5.0"}

        def generate():
            # 1MB chunks mein data stream karna
            with requests.get(target_url, headers=headers, stream=True, timeout=600) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    yield chunk

        content_type = "video/mp4" if m_type == "video" else "audio/mpeg"
        return Response(generate(), content_type=content_type)
    except Exception as e:
        return Response(str(e), status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
