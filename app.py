from flask import Flask, request, jsonify, Response
import requests
import os
import base64

app = Flask(__name__)

# ---------------------------------------------------------
# 🌍 PUBLIC PIPED INSTANCES (High Speed & No Block)
# ---------------------------------------------------------
# Hum bari bari in servers se data mangenge
INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.ot.ax",
    "https://pipedapi.drgns.space",
    "https://pa.il.ax",
    "https://api.piped.projectsegfau.lt"
]

def get_piped_data(query, m_type):
    # 1. SEARCH PHASE
    video_id = ""
    title = ""
    used_instance = ""

    # Agar direct link hai
    if "youtube.com" in query or "youtu.be" in query:
        if "v=" in query:
            video_id = query.split("v=")[1].split("&")[0]
        else:
            video_id = query.split("/")[-1]
        title = "YouTube Link"
    
    # Agar search karna hai
    else:
        for instance in INSTANCES:
            try:
                print(f"Searching on: {instance}")
                search_url = f"{instance}/search?q={query}&filter=music_songs"
                res = requests.get(search_url, timeout=4).json()
                if 'items' in res and res['items']:
                    video_id = res['items'][0]['url'].split("/watch?v=")[1]
                    title = res['items'][0]['title']
                    used_instance = instance # Jo server chala, usi se download bhi karenge
                    break
            except:
                continue
    
    if not video_id:
        return None, "Search failed on all servers."

    # 2. STREAM EXTRACTION PHASE (Without yt-dlp)
    # Hum usi instance se stream link mangenge
    target_instances = [used_instance] if used_instance else INSTANCES
    
    for instance in target_instances:
        try:
            stream_url = f"{instance}/streams/{video_id}"
            data = requests.get(stream_url, timeout=4).json()
            
            # Title update agar pehle nahi mila
            if title == "YouTube Link":
                title = data.get('title', 'Unknown Media')

            # Audio ya Video link nikaalna
            final_url = ""
            if m_type == 'audio':
                # Sabse best audio stream dhoondo
                audio_streams = data.get('audioStreams', [])
                if audio_streams:
                    final_url = audio_streams[0]['url'] # Best quality usually first
            else:
                # Video stream
                video_streams = data.get('videoStreams', [])
                if video_streams:
                    # Video with sound dhoondna
                    for v in video_streams:
                        if v.get('videoOnly') == False:
                            final_url = v['url']
                            break
            
            if final_url:
                duration = data.get('duration', 0)
                # Seconds to Min:Sec conversion
                mins, secs = divmod(duration, 60)
                duration_str = f"{int(mins)}:{int(secs):02d}"
                
                return {
                    "title": title,
                    "url": final_url,
                    "duration": duration_str
                }, None
                
        except Exception as e:
            print(f"Stream error on {instance}: {e}")
            continue

    return None, "Stream link nahi mila (All mirrors busy)."

# ---------------------------------------------------------
# 🚀 API ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    return "🦅 AHMAD RDX - PIPED PROXY ENGINE (NO YT-DLP)"

@app.route('/music-dl')
def music_dl():
    query = request.args.get('q')
    m_type = request.args.get('type', default='audio')
    
    if not query: return jsonify({"status": False, "msg": "Query missing!"})

    # Data fetch via Piped API
    data, error = get_piped_data(query, m_type)
    
    if not data:
        return jsonify({"status": False, "msg": error})

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
        # Piped ke liye headers simple rakhne hote hain
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
                                  
