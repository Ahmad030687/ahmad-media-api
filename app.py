from flask import Flask, request, jsonify, Response
import requests
import os
import base64
import re

app = Flask(__name__)

# 🛡️ STABLE SERVERS LIST (Failover System)
SERVERS = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.projectsegfau.lt",
    "https://pipedapi.leptons.xyz",
    "https://invidious.snopyta.org/api/v1"
]

@app.route('/')
def home():
    return "🦅 AHMAD RDX - UNIVERSAL MEDIA ENGINE LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', 'audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    # 1. SEARCH PHASE (YouTube Search via Piped/Invidious)
    video_id = None
    title = "Media File"

    for server in SERVERS:
        try:
            search_url = f"{server}/search?q={query}&filter=all"
            res = requests.get(search_url, timeout=10).json()
            
            # Piped Format
            if 'items' in res and len(res['items']) > 0:
                video_id = res['items'][0]['url'].split("=")[-1]
                title = res['items'][0]['title']
                break
            # Invidious Format
            elif isinstance(res, list) and len(res) > 0:
                video_id = res[0]['videoId']
                title = res[0]['title']
                break
        except:
            continue

    if not video_id:
        return jsonify({"status": False, "msg": "Saare servers busy hain. Thori dair baad try karein."})

    # 2. STREAM PHASE (Extracting the real link)
    final_url = ""
    for server in SERVERS:
        try:
            stream_url = f"{server}/streams/{video_id}"
            s_res = requests.get(stream_url, timeout=10).json()
            
            if m_type == "audio":
                if 'audioStreams' in s_res:
                    final_url = s_res['audioStreams'][0]['url']
                    break
            else:
                if 'videoStreams' in s_res:
                    # Best mp4 dhundna
                    for v in s_res['videoStreams']:
                        if v['format'] == 'mp4':
                            final_url = v['url']
                            break
                    if not final_url: final_url = s_res['videoStreams'][0]['url']
                    break
        except:
            continue

    if not final_url:
        return jsonify({"status": False, "msg": "Download link generate nahi ho saka."})

    # 3. PROXY TOKEN
    token = base64.b64encode(final_url.encode('ascii')).decode('ascii')
    
    return jsonify({
        "status": True,
        "title": title,
        "url": f"{request.host_url}proxy-dl?token={token}&type={m_type}"
    })

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
