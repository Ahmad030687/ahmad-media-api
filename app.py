from flask import Flask, request, jsonify, Response
from duckduckgo_search import DDGS
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛠️ BYPASS ENGINE: Flexible Format Selection
# ---------------------------------------------------------
def get_stream_data(video_url, m_type):
    # Flexible format logic: Agar best na mile to available uthao
    if m_type == 'audio':
        format_str = 'ba/b' # Best Audio / or any Audio
    else:
        format_str = 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b' # Best MP4 / or any MP4

    ydl_opts = {
        'format': format_str,
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        # 🛡️ Multiple clients combination
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
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
        # 1. 🔎 Search (DDG bypass)
        with DDGS() as ddgs:
            results = list(ddgs.videos(f"{query} site:youtube.com", max_results=1))
            if not results:
                return jsonify({"status": False, "msg": "Result nahi mila!"})
            video_url = results[0]['content']

        # 2. ⚡ Get Stream
        real_stream_url, title, duration = get_stream_data(video_url, m_type)
        
        if not real_stream_url:
            return jsonify({"status": False, "msg": "Format available nahi hai."})

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
# 🛡️ PROXY STREAMER
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
    
