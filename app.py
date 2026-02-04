from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return "🦅 AHMAD RDX MEDIA ENGINE - LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    media_type = request.args.get('type', default='audio') # audio ya video
    
    if not query: return jsonify({"status": False, "msg": "Query missing"})

    # yt-dlp ki professional settings
    ydl_opts = {
        'format': 'bestaudio/best' if media_type == 'audio' else 'bestvideo+bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'geo_bypass': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            real_url = info.get('url')
            title = info.get('title', 'Media File')
            
            # Link ko safe karne ke liye Base64 use kar rahe hain
            token = base64.b64encode(real_url.encode('ascii')).decode('ascii')
            
            return jsonify({
                "status": True,
                "title": title,
                "url": f"{request.host_url}proxy-dl?token={token}&type={media_type}"
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
        content_type = "video/mp4" if m_type == "video" else "audio/mpeg"
        return Response(generate(), content_type=content_type)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
      
