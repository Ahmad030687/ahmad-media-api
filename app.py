from flask import Flask, request, jsonify, send_file
from pytubefix import YouTube
import re
import os
import shutil

app = Flask(__name__)

# Downloads directory setup
DOWNLOAD_PATH = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

def is_valid_youtube_url(url):
    # Flexible regex for all types of YT links
    pattern = r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$"
    return re.match(pattern, url) is not None

@app.route('/video_info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')
    if not url or not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid or missing YouTube URL."}), 400
    
    try:
        yt = YouTube(url)
        info = {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "views": yt.views
        }
        return jsonify(info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<resolution>', methods=['POST'])
def download_by_resolution(resolution):
    data = request.get_json()
    url = data.get('url')
    
    if not url or not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400
    
    try:
        yt = YouTube(url)
        # Filter progressive mp4 streams
        stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=resolution).first()
        
        if not stream:
            return jsonify({"error": f"Resolution {resolution} available nahi hai."}), 404

        # Download file
        file_name = f"video_{resolution}.mp4"
        video_path = stream.download(output_path=DOWNLOAD_PATH, filename=file_name)
        
        # 🚀 CRUCIAL: File user/bot ko bhejna
        return send_file(video_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/available_resolutions', methods=['POST'])
def available_resolutions():
    data = request.get_json()
    url = data.get('url')
    if not url or not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid URL"}), 400
    
    try:
        yt = YouTube(url)
        res = sorted(list(set([s.resolution for s in yt.streams.filter(progressive=True) if s.resolution])))
        return jsonify({"progressive": res}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render ke liye host aur port settings
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
