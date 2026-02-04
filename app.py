from flask import Flask, request, jsonify, Response
import yt_dlp
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🌍 PIPED API SERVERS (Search Bypass)
# ---------------------------------------------------------
# Ye servers YouTube search karke Video ID dete hain.
# Hum Koyeb ki IP se search nahi karenge, in se karwayenge.
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.ot.ax",
    "https://pipedapi.drgns.space",
    "https://pa.il.ax",
    "https://api.piped.projectsegfau.lt"
]

def search_via_piped(query):
    # Agar direct link hai
    if query.startswith("http"):
        return query, "YouTube Link"

    print(f"Searching via Piped: {query}")
    
    # Har server ko bari bari try karo
    for api_url in PIPED_INSTANCES:
        try:
            # Piped Search API Call
            search_url = f"{api_url}/search?q={query}&filter=music_songs"
            res = requests.get(search_url, timeout=5).json()
            
            # Agar items milein
            if 'items' in res and len(res['items']) > 0:
                # Pehla result uthao
                first_video = res['items'][0]
                video_url = f"https://www.youtube.com/watch?v={first_video['url'].split('/watch?v=')[1]}"
                title = first_video['title']
                print(f"Found on {api_url}: {title}")
                return video_url, title
        except Exception as e:
            print(f"Server {api_url} failed: {e}")
            continue # Agla server try karo
            
    return None, None

# ---------------------------------------------------------
# 🛠️ DOWNLOAD ENGINE (Android Mode)
# ---------------------------------------------------------
def get_stream_data(video_url, m_type):
    ydl_opts = {
        'format': 'bestaudio/best' if m_type == 'audio' else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        # 📱 Android Client (Download ke liye best)
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
            "title": info.get('title', 'Media File'),
            "duration": info.get('duration_string', '0:00')
        }

# ---------------------------------------------------------
# 🚀 API ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - PIPED BYPASS API LIVE"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    try:
        # STEP 1: Search (Piped Servers se)
        real_link, title = search_via_piped(query)
        
        if not real_link:
            # Agar Piped bhi fail ho jaye, to aakhri koshish normal search
            real_link = f"ytsearch1:{query}"
            title = "Searching..."

        # STEP 2: Extraction (yt-dlp se)
        data = get_stream_data(real_link, m_type)
        
        # Agar Piped se title mila tha to wo use karo, warna yt-dlp wala
        final_title = title if title != "YouTube Link" and title != "Searching..." else data['title']

        # Proxy Token
        token = base64.b64encode(data['url'].encode('ascii')).decode('ascii')
        
        return jsonify({
            "status": True,
            "title": final_title,
            "duration": data['duration'],
            "url": f"{request.host_url}proxy-dl?token={token}&type={m_type}"
        })

    except Exception as e:
        # Agar yt-dlp fail ho jaye
        return jsonify({"status": False, "error": str(e), "msg": "Download failed. Try another song."})

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
    
