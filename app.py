from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🌍 UNIVERSAL ENGINE (Supports All Platforms)
# ---------------------------------------------------------
def get_universal_data(query, m_type):
    # 1. Logic: Agar Link nahi hai, to YouTube Search samjho
    if not query.startswith("http"):
        query = f"ytsearch1:{query}"

    # 2. Universal Options
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'best', # Universal format
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        # 📱 User Agent (Mobile ban kar request bhejna)
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        },
        # 🛡️ Special Tweaks
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'], # YouTube ke liye
                'player_skip': ['webpage', 'configs']
            },
            'tiktok': {
                'app_version': ['30.0.0'] # TikTok ke liye
            }
        }
    }
    
    # 3. Extraction
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            # Agar Search Results hon (YouTube)
            if 'entries' in info:
                if not info['entries']: return None
                info = info['entries'][0]
            
            # Title aur URL nikalna
            return {
                "url": info.get('url'),
                "title": info.get('title', 'Social Media Video'),
                "duration": info.get('duration_string', '')
            }
    except Exception as e:
        print(f"Error: {e}")
        return None

# ---------------------------------------------------------
# 🚀 API ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - UNIVERSAL MEDIA API LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Link ya naam likhein!"})

    try:
        data = get_universal_data(query, m_type)
        
        if not data:
            return jsonify({"status": False, "msg": "Media nahi mila ya Private hai."})

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
        # Instagram/FB ke liye headers zaroori hote hain
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "Referer": "https://www.tiktok.com/" if "tiktok" in target_url else "https://www.instagram.com/"
        }

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
