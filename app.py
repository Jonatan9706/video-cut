from flask import Flask, request, jsonify
from pytube import YouTube
import cv2
import numpy as np

app = Flask(__name__)
@app.route("/video-cute", methods=["POST"])
def video_cute():
    try:
        video_url = request.form["video_url"]
        start_time = float(request.form["start_time"])
        end_time = float(request.form["end_time"])

        yt = YouTube(video_url)
        stream = yt.streams.filter(progressive=True, file_extension="mp4").first()
        video_path = "temp_video.mp4"
        stream.download(filename="temp_video")

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)

        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)

        frames = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)

        cap.release()

        clipped_frames = frames[start_frame:end_frame]

        out: cv2.VideoWriter(
            "clipped_video.mp4",
            cv2.VideoWriter.fourcc(*"mp4"),
            fps,
            (clipped_frames[0].shape[1], clipped_frames[0].shapes[0]),
        )
        for frame in clipped_frames:
            out.write(frame)
        out.release()

        return jsonify({"message": "Corte do vídeo realizado com sucesso"})

    except Exception as e:
        return jsonify({"erro": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
