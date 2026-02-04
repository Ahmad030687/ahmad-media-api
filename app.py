from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛠️ BYPASS ENGINE: Mobile Identity Logic
# ---------------------------------------------------------
def get_yt_data(query, m_type):
    # Search command: Agar link nahi hai to search karo
    # ytsearch1 means pehla result uthao
    search_query = f"ytsearch1:{query}" if not query.startswith("http") else query
    
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        # 📱 Android VR aur iOS clients sabse stable bypass hain
        'extractor_args': {
            'youtube': {
                'player_client': ['android_vr', 'ios', 'mweb'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        
        return {
            "url": info.get('url'),
            "title": info.get('title', 'Media File'),
            "duration": info.get('duration_string', '0:00')
        }

@app.route('/')
def home():
    return "🦅 AHMAD RDX - KOYEB SUPER ENGINE LIVE"

# ---------------------------------------------------------
# 🎵 API ENDPOINT
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    try:
        data = get_yt_data(query, m_type)
        
        # Stream link ko safe banane ke liye Base64 use kar rahe hain
        token = base64.b64encode(data['url'].encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": data['title'],
            "duration": data['duration'],
            "url": f"{request.host_url}proxy-dl?token={token}&type={m_type}"
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

# ---------------------------------------------------------
# 🛡️ PROXY STREAMER (Bypass Social Media Blocks)
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
    # Koyeb 8080 use karta hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
