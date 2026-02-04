from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛠️ BYPASS ENGINE: Fixed Search & Extraction
# ---------------------------------------------------------
def get_yt_data(query, m_type):
    # Search logic: Link hai ya keyword, dono handle honge
    search_query = f"ytsearch1:{query}" if not query.startswith("http") else query
    
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'extract_flat': False,
        'skip_download': True,
        # 📱 Mobile Identity (YouTube isay block nahi karta)
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
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            
            # 🛡️ INDEX FIX: Check agar search mein koi results aaye hain ya nahi
            if 'entries' in info:
                if not info['entries']:
                    return None # No results found
                video_data = info['entries'][0]
            else:
                video_data = info

            return {
                "url": video_data.get('url'),
                "title": video_data.get('title', 'Ahmad RDX Media'),
                "duration": video_data.get('duration_string', '0:00')
            }
    except Exception as e:
        print(f"Extraction Error: {str(e)}")
        return None

# ---------------------------------------------------------
# 🎵 ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - KOYEB ENGINE FIXED & LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: 
        return jsonify({"status": False, "msg": "Search query missing!"})

    try:
        data = get_yt_data(query, m_type)
        
        # Agar data khali hai (Index Fix)
        if not data:
            return jsonify({
                "status": False, 
                "msg": "Nahi mila! Gane ka sahi naam likhein ya link dein."
            })
        
        # Stream link ko safe banane ke liye Base64
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
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.youtube.com/"}

        def generate():
            # Chunks mein stream karna taake RAM full na ho
            with requests.get(target_url, headers=headers, stream=True, timeout=600) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    yield chunk

        c_type = "video/mp4" if m_type == "video" else "audio/mpeg"
        return Response(generate(), content_type=c_type)
    except Exception as e:
        return Response(str(e), status=500)

if __name__ == "__main__":
    # Koyeb default port 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
