from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛠️ YOUTUBE ANDROID ENGINE (Search & Download)
# ---------------------------------------------------------
def get_youtube_data(query, m_type):
    # 1. Search Logic:
    # Agar direct link hai to wahi use karo, warna "ytsearch1:" lagao
    if query.startswith("http"):
        search_query = query
    else:
        # "ytsearch1:" ka matlab hai pehla result uthao
        search_query = f"ytsearch1:{query}"

    # 2. Android Client Settings (Block Proof)
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        # 🛡️ Ye setting bot ko "Samsung Android Phone" bana deti hai
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36 YouTube/17.31.35'
        }
    }
    
    # 3. Execution
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Data extract karna
            info = ydl.extract_info(search_query, download=False)
            
            # Agar Search results hon (playlist/search)
            if 'entries' in info:
                # Check agar list khali hai
                if not info['entries']:
                    return None, "Search results khali hain (Empty List)."
                info = info['entries'][0]
            
            return {
                "url": info.get('url'),
                "title": info.get('title', 'Unknown Title'),
                "duration": info.get('duration_string', '0:00')
            }, None

    except Exception as e:
        # Asli error wapis bhejna
        return None, str(e)

# ---------------------------------------------------------
# 🚀 API ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - ANDROID API LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    # Data fetch karna
    data, error_msg = get_youtube_data(query, m_type)
    
    if not data:
        # Agar error aaye to user ko dikhana
        return jsonify({
            "status": False, 
            "msg": f"Error: {error_msg}"
        })

    try:
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
    
