from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🍪 COOKIES & BYPASS CONFIGURATION
# ---------------------------------------------------------
def get_ydl_opts(media_type):
    cookie_path = 'cookies.txt'
    
    # Audio ya Video quality selection
    if media_type == 'video':
        format_sel = 'bestvideo+bestaudio/best'
    else:
        format_sel = 'bestaudio/best'

    opts = {
        'format': format_sel,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'geo_bypass': True,
        # Cookies file check
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        # Mobile clients bypass ke liye behtareen hain
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['webpage', 'hls']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        }
    }
    return opts

# ---------------------------------------------------------
# 🏠 HOME ROUTE
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 MEDIA ENGINE v3 (COOKIES ACTIVE) - LIVE"

# ---------------------------------------------------------
# 🎵 SEARCH & DATA EXTRACTOR
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
            # YouTube search
            info = ydl.extract_info(query, download=False)
            
            # Agar results na milien toh "List index out of range" se bachne ke liye check
            if not info or 'entries' not in info or len(info['entries']) == 0:
                return jsonify({"status": False, "msg": "Nahi mila! Name thora change kar ke dekhein."})
            
            video_data = info['entries'][0]
            real_url = video_data.get('url')
            title = video_data.get('title', 'Media File')
            duration = video_data.get('duration_string', '0:00')
            
            # Link ko Base64 mein convert karna taake URL break na ho
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
# 🛡️ PROXY STREAMER (Bypass Direct Link Block)
# ---------------------------------------------------------
@app.route('/proxy-dl')
def proxy_dl():
    token = request.args.get('token')
    m_type = request.args.get('type', 'audio')
    
    if not token:
        return Response("Token missing!", status=400)

    try:
        # Link ko wapis asli halat mein lana
        target_url = base64.b64decode(token.encode('ascii')).decode('ascii')
        
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "Referer": "https://www.youtube.com/"
        }

        # Streaming function taake bari files RAM crash na karein
        def generate():
            with requests.get(target_url, headers=headers, stream=True, timeout=600) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 1024): # 1MB segments
                    yield chunk

        content_type = "video/mp4" if m_type == "video" else "audio/mpeg"
        return Response(generate(), content_type=content_type)

    except Exception as e:
        return Response(f"Stream Error: {str(e)}", status=500)

if __name__ == "__main__":
    # Render Port
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
        
