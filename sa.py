from flask import Flask, request, jsonify
from shazamio import Shazam
import asyncio
import os
import requests
import tempfile

app = Flask(__name__)
shazam = Shazam()

@app.route('/identify', methods=['GET'])
def identify_song_sync():
    return asyncio.run(identify_song())

async def identify_song():
    try:
        # Get the audio file URL from the query parameters
        audio_url = request.args.get('audio_url')
        if not audio_url:
            return jsonify({"status": "fail", "message": "No audio URL provided!"})

        # Download the audio file from the provided URL
        response = requests.get(audio_url, stream=True)
        if response.status_code != 200:
            return jsonify({"status": "fail", "message": f"Unable to fetch file from URL: {audio_url}"})

        # Save the audio file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        # Identify the song using Shazam
        result = await shazam.recognize_song(temp_file_path)

        # Delete the temporary file after processing
        os.unlink(temp_file_path)

        # Extract relevant details
        if result and "track" in result:
            track = result["track"]
            response = {
                "title": track.get("title"),
                "subtitle": track.get("subtitle"),
                "artist": track.get("share", {}).get("subject"),
                "url": track.get("share", {}).get("href"),
                "image": track.get("images", {}).get("coverart"),
            }
            return jsonify({"status": "success", "data": response})
        else:
            return jsonify({"status": "fail", "message": "No song identified!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
