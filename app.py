from flask import Flask, request, jsonify, Response
import requests
import os
import base64
import random

app = Flask(__name__)

# ---------------------------------------------------------
# ⚙️ SERVER LIST (Agar aik fail ho to dusra chalega)
# ---------------------------------------------------------
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.privacy.com.de",
    "https://pipedapi.drgns.space",
    "https://api.piped.yt",
    "https://piped-api.lunar.icu"
]

@app.route('/')
def home():
    return "🦅 AHMAD RDX - FAILOVER ENGINE LIVE"

# ---------------------------------------------------------
# 🎵 SMART SEARCH (Multi-Server)
# ---------------------------------------------------------
@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    media_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing"})

    # Servers ko shuffle kar lete hain taake load balance ho jaye
    instances = PIPED_INSTANCES.copy()
    random.shuffle(instances)
    
    selected_instance = None
    video_data = None
    error_log = []

    # 🔄 LOOP: Har server ko check karna
    for instance in instances:
        try:
            # Step 1: Search Request
            search_url = f"{instance}/search?q={query}&filter=all"
            # Timeout kam rakha hai taake agar server slow ho to foran next par jaye
            res = requests.get(search_url, timeout=5) 
            
            if res.status_code != 200: continue # Agar error aye to next try karo
            
            data = res.json()
            if not data.get('items'): continue

            # Result mil gaya!
            first_result = data['items'][0]
            video_path = first_result['url'] # /watch?v=ID
            video_id = video_path.replace("/watch?v=", "")
            title = first_result['title']
            
            # Step 2: Stream Link nikalna
            stream_url = f"{instance}/streams/{video_id}"
            stream_res = requests.get(stream_url, timeout=5)
            
            if stream_res.status_code != 200: continue
            
            stream_data = stream_res.json()
            
            final_url = ""
            if media_type == "audio":
                if stream_data.get('audioStreams'):
                    final_url = stream_data['audioStreams'][0]['url']
            else:
                # Video (720p prefer)
                if stream_data.get('videoStreams'):
                    for vid in stream_data['videoStreams']:
                        if vid['format'] == 'mp4' and vid['quality'] == '720p':
                            final_url = vid['url']
                            break
                    if not final_url and len(stream_data['videoStreams']) > 0:
                        final_url = stream_data['videoStreams'][0]['url']
            
            if final_url:
                selected_instance = instance # Kaam ban gaya
                # Link ko Base64 mein pack karna
                token = base64.b64encode(final_url.encode('ascii')).decode('ascii')
                
                return jsonify({
                    "status": True,
                    "server": instance, # Bata dega kis server ne kaam kiya
                    "title": title,
                    "url": f"{request.host_url}proxy-dl?token={token}&type={media_type}",
                    "type": media_type
                })

        except Exception as e:
            error_log.append(f"{instance}: {str(e)}")
            continue # Next server try karo

    # Agar saare servers fail ho gaye
    return jsonify({
        "status": False, 
        "msg": "All servers are busy. Try again later.",
        "errors": error_log
    })

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
    
