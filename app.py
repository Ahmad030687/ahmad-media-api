from flask import Flask, request, jsonify, Response
from ytmusicapi import YTMusic
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)
ytmusic = YTMusic()

# ---------------------------------------------------------
# 🛠️ YOUTUBE SPECIAL ENGINE
# ---------------------------------------------------------
def get_youtube_data(query, m_type):
    video_id = ""
    title = ""
    duration = ""

    # STEP 1: Search via YouTube Music API (Bypasses Block)
    try:
        if query.startswith("http"):
            # Agar direct link hai
            video_id = query.split("v=")[1].split("&")[0] if "v=" in query else query.split("/")[-1]
            title = "YouTube Link"
        else:
            # Agar naam likha hai to Search karo
            results = ytmusic.search(query, filter="songs")
            if not results:
                # Agar songs mein na mile to video search karo
                results = ytmusic.search(query, filter="videos")
            
            if not results:
                return None
            
            first_result = results[0]
            video_id = first_result['videoId']
            title = first_result['title']
            # Artist ka naam bhi saath jornay ke liye
            if 'artists' in first_result:
                artist = first_result['artists'][0]['name']
                title = f"{title} - {artist}"
                
    except Exception as e:
        print(f"Search Error: {e}")
        return None

    # STEP 2: Extract Link via yt-dlp (Mobile Client)
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'player_skip': ['webpage', 'configs']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return {
                "url": info.get('url'),
                "title": info.get('title', title),
                "duration": info.get('duration_string', '0:00')
            }
    except Exception as e:
        print(f"Extraction Error: {e}")
        return None

# ---------------------------------------------------------
# 🚀 API ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - YOUTUBE MUSIC API LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    try:
        data = get_youtube_data(query, m_type)
        
        if not data:
            return jsonify({"status": False, "msg": "Gana nahi mila. Spelling check karein."})

        # Proxy Token
        token = base64.b64encode(data['url'].encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": data['title'],
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
            
