from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛠️ HELPER: YouTube Bypass Settings
# ---------------------------------------------------------
def get_ydl_opts(media_type):
    # Audio ya Video ke liye format chunn-na
    if media_type == 'audio':
        format_sel = 'bestaudio/best'
    else:
        format_sel = 'bestvideo+bestaudio/best'

    return {
        'format': format_sel,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'geo_bypass': True,
        # 📱 Mobile App Clients (YouTube bypass karne ka raaz)
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['webpage', 'hls']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us',
        }
    }

# ---------------------------------------------------------
# 🏠 Home Route
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX MEDIA ENGINE v2 - BYPASS ACTIVE"

# ---------------------------------------------------------
# 🎵 Search & Link Generator
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    media_type = request.args.get('type', default='audio')
    
    if not query:
        return jsonify({"status": False, "msg": "Search query missing!"})

    try:
        ydl_opts = get_ydl_opts(media_type)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # YouTube se data nikalna
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            real_url = info.get('url')
            title = info.get('title', 'Media File')
            duration = info.get('duration_string', '0:00')
            
            # Link ko safe karne ke liye Base64 use kar rahe hain
            token = base64.b64encode(real_url.encode('ascii')).decode('ascii')
            
            return jsonify({
                "status": True,
                "title": title,
                "duration": duration,
                "url": f"{request.host_url}proxy-dl?token={token}&type={media_type}",
                "type": media_type
            })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

# ---------------------------------------------------------
# 🛡️ Proxy Engine (Actual Download Stream)
# ---------------------------------------------------------
@app.route('/proxy-dl')
def proxy_dl():
    token = request.args.get('token')
    m_type = request.args.get('type', 'audio')
    
    if not token:
        return Response("Token missing!", status=400)

    try:
        # Link ko wapis decode karna
        target_url = base64.b64decode(token.encode('ascii')).decode('ascii')
        
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "Referer": "https://www.youtube.com/"
        }

        # Chunk by chunk data bhejenge taake RAM crash na ho
        def generate():
            with requests.get(target_url, headers=headers, stream=True, timeout=600) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 1024): # 1MB chunks
                    yield chunk

        content_type = "video/mp4" if m_type == "video" else "audio/mpeg"
        return Response(generate(), content_type=content_type)

    except Exception as e:
        return Response(f"Stream Error: {str(e)}", status=500)

if __name__ == "__main__":
    # Render Port settings
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
