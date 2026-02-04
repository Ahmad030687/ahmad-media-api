from flask import Flask, request, jsonify, Response
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# ⚙️ CONFIGURATION: Stable Piped Instances
# Agar aik server down ho, to hum doosra use kar sakte hain
# ---------------------------------------------------------
PIPED_API_URL = "https://pipedapi.kavin.rocks" 

@app.route('/')
def home():
    return "🦅 AHMAD RDX - PIPED ENGINE (100% WORKING)"

# ---------------------------------------------------------
# 🎵 SEARCH & EXTRACT (No yt-dlp, No Cookies)
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    media_type = request.args.get('type', default='audio') # 'audio' or 'video'
    
    if not query: return jsonify({"status": False, "msg": "Query missing"})

    try:
        # 1. Search Request (Piped API)
        search_url = f"{PIPED_API_URL}/search?q={query}&filter=all"
        search_res = requests.get(search_url).json()
        
        if not search_res.get('items'):
             return jsonify({"status": False, "msg": "No results found."})

        # Pehla result uthana (Video/Music)
        first_result = search_res['items'][0]
        video_path = first_result['url'] # e.g. /watch?v=VIDEO_ID
        video_id = video_path.replace("/watch?v=", "")
        title = first_result['title']
        
        # 2. Stream Link Nikalna
        stream_url = f"{PIPED_API_URL}/streams/{video_id}"
        stream_data = requests.get(stream_url).json()
        
        final_url = ""
        
        if media_type == "audio":
            # Best Audio dhundna
            if stream_data.get('audioStreams'):
                # Sabse high quality audio
                final_url = stream_data['audioStreams'][0]['url']
        else:
            # Best Video dhundna (mp4)
            if stream_data.get('videoStreams'):
                for vid in stream_data['videoStreams']:
                    if vid['format'] == 'mp4' and vid['quality'] == '720p': # 720p prefer
                        final_url = vid['url']
                        break
                # Agar 720p na mile to pehli wali utha lo
                if not final_url and len(stream_data['videoStreams']) > 0:
                    final_url = stream_data['videoStreams'][0]['url']

        if not final_url:
            return jsonify({"status": False, "msg": "Stream link nahi mila."})

        # 3. Base64 Token banana (Safe Link)
        token = base64.b64encode(final_url.encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": title,
            "url": f"{request.host_url}proxy-dl?token={token}&type={media_type}",
            "type": media_type
        })

    except Exception as e:
        return jsonify({"status": False, "error": str(e)})

# ---------------------------------------------------------
# 🛡️ PROXY DOWNLOADER
# ---------------------------------------------------------
@app.route('/proxy-dl')
def proxy_dl():
    token = request.args.get('token')
    m_type = request.args.get('type', 'audio')
    
    if not token: return Response("Token missing", status=400)

    try:
        target_url = base64.b64decode(token.encode('ascii')).decode('ascii')
        
        # Piped ke liye User-Agent zaroori nahi, lekin achi practice hai
        headers = {"User-Agent": "Mozilla/5.0"}

        def generate():
            with requests.get(target_url, headers=headers, stream=True, timeout=600) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    yield chunk

        c_type = "video/mp4" if m_type == "video" else "audio/mpeg"
        return Response(generate(), content_type=c_type)

    except Exception as e:
        return Response(f"Proxy Error: {str(e)}", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
