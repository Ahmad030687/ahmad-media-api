from flask import Flask, request, jsonify, Response
from youtubesearchpython import VideosSearch
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🕵️ SPECIALIST SEARCH ENGINE (No Blocks)
# ---------------------------------------------------------
def search_video(query):
    try:
        # Agar user ne direct link diya hai
        if query.startswith("http"):
            return query, "YouTube Link"

        # Dedicated Library se Search (Ye yt-dlp nahi hai)
        print(f"Searching via Specialist: {query}")
        videos_search = VideosSearch(query, limit=1)
        results = videos_search.result()

        if results and 'result' in results and len(results['result']) > 0:
            top_result = results['result'][0]
            video_link = top_result['link']
            title = top_result['title']
            print(f"Found: {title}")
            return video_link, title
        
        return None, None
    except Exception as e:
        print(f"Search Error: {e}")
        return None, None

# ---------------------------------------------------------
# 🛠️ DOWNLOAD ENGINE (Android Mode)
# ---------------------------------------------------------
def get_stream_data(video_url, m_type):
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        # 🛡️ Sirf Download ke liye Android banenge
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'player_skip': ['webpage', 'configs']
            }
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return {
            "url": info.get('url'),
            "title": info.get('title', 'Media File'),
            "duration": info.get('duration_string', '0:00')
        }

# ---------------------------------------------------------
# 🚀 API ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - SPECIALIST SEARCH API LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    try:
        # STEP 1: Search (Via youtube-search-python)
        real_link, title = search_video(query)
        
        if not real_link:
            return jsonify({
                "status": False, 
                "msg": "Search fail. Koi result nahi mila."
            })

        # STEP 2: Extraction (Via yt-dlp)
        # Agar title pehle nahi mila to yahan update ho jayega
        data = get_stream_data(real_link, m_type)
        if title == "YouTube Link":
            title = data['title']

        # Proxy Token
        token = base64.b64encode(data['url'].encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": title,
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
                
