from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🛡️ MIRROR SEARCH ENGINE (To Fix Empty List Error)
# ---------------------------------------------------------
# Ye servers YouTube se search kar ke result la dete hain
# Hum inhein bari bari try karenge taake empty error na aaye.
SEARCH_INSTANCES = [
    "https://inv.tux.rs",
    "https://y.com.sb",
    "https://invidious.nerdvpn.de",
    "https://invidious.flokinet.to",
    "https://invidious.projectsegfau.lt"
]

def search_via_mirrors(query):
    # Agar user ne direct link diya hai
    if query.startswith("http"):
        return query, "YouTube Link"

    # Agar naam diya hai, to Mirrors par search karo
    print(f"Searching for: {query}")
    for instance in SEARCH_INSTANCES:
        try:
            # Invidious API Call
            api_url = f"{instance}/api/v1/search?q={query}&type=video"
            res = requests.get(api_url, timeout=6).json()
            
            # Agar result mil gaya
            if res and len(res) > 0:
                video_id = res[0]['videoId']
                title = res[0]['title']
                print(f"Found on {instance}: {title}")
                return f"https://www.youtube.com/watch?v={video_id}", title
        except:
            continue # Next server try karo
            
    return None, None

# ---------------------------------------------------------
# 🛠️ DOWNLOADER (Android Mode)
# ---------------------------------------------------------
def get_stream_data(video_url, m_type):
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        # 📱 Mobile Client (Download ke liye best)
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'player_skip': ['webpage', 'configs']
            }
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return {
            "url": info.get('url'),
            "duration": info.get('duration_string', '0:00')
        }

# ---------------------------------------------------------
# 🚀 API ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - MIRROR SEARCH ENGINE LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Likha hi kuch nahi!"})

    try:
        # STEP 1: Search (Mirror se)
        real_link, title = search_via_mirrors(query)
        
        if not real_link:
            return jsonify({
                "status": False, 
                "msg": "Search fail ho gayi. Sare servers busy hain."
            })

        # STEP 2: Extraction (yt-dlp se)
        data = get_stream_data(real_link, m_type)
        
        # Proxy Token
        token = base64.b64encode(data['url'].encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": title,
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
    
