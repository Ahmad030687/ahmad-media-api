from flask import Flask, request, jsonify, Response
from ytmusicapi import YTMusic
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)
ytmusic = YTMusic()

# ---------------------------------------------------------
# 🛠️ MEDIA EXTRACTOR: YouTube Music Logic
# ---------------------------------------------------------
def get_stream_data(video_id, m_type):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'player_skip': ['webpage', 'configs']
            }
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info.get('url'), info.get('title', 'Media File')

# ---------------------------------------------------------
# 🎵 MAIN API ENDPOINT
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query:
        return jsonify({"status": False, "msg": "Search query missing!"})

    try:
        # 1. 🔎 Search directly on YouTube Music (Bypasses DuckDuckGo)
        search_results = ytmusic.search(query, filter="songs")
        
        if not search_results:
            return jsonify({"status": False, "msg": "No results found on YouTube Music."})
        
        # Extract the first result
        video_id = search_results[0]['videoId']
        title = search_results[0]['title']
        artist = search_results[0]['artists'][0]['name'] if 'artists' in search_results[0] else "Unknown Artist"

        # 2. ⚡ Get Stream Link
        real_stream_url, official_title = get_stream_data(video_id, m_type)
        
        # 3. 🛡️ Proxy Token (Safe Base64)
        token = base64.b64encode(real_stream_url.encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": f"{title} - {artist}",
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
    
