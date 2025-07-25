import cv2
import os
import numpy as np

# NOTE: For now, all frames are resized to 224x224. Mobile video orientation/aspect ratio handling to be revisited later.

def extract_frames(video_path, output_dir, interval_sec=1, size=(224, 224)):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps else 0
    frame_interval = int(fps * interval_sec) if fps else 1
    frame_idx = 0
    saved_frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            # Resize frame to target size
            resized = cv2.resize(frame, size)
            frame_filename = os.path.join(output_dir, f"frame_{frame_idx}.jpg")
            cv2.imwrite(frame_filename, resized)
            saved_frames.append(frame_filename)
        frame_idx += 1
    cap.release()
    return saved_frames

def mock_ai_match(frame_path, reference_image_path):
    # Placeholder: always returns False (no match)
    # Replace with real AI call later
    return False 