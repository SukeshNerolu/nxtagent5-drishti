from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
import json
from datetime import datetime
from video_utils import extract_frames, mock_ai_match

app = FastAPI()
UPLOAD_DIR = "uploads"
REPORTS_FILE = "lost_reports.json"
VIDEO_PATH = "sample_video_clip.mp4"
FRAMES_DIR = "temp_frames"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_report_metadata(description, filename, match_found, checked_frames):
    report = {
        "description": description,
        "photo_filename": filename,
        "timestamp": datetime.utcnow().isoformat(),
        "match_found": match_found,
        "frames_checked": checked_frames
    }
    if os.path.exists(REPORTS_FILE):
        with open(REPORTS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []
    data.append(report)
    with open(REPORTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.post("/lost-report")
async def submit_lost_report(
    photo: Optional[UploadFile] = File(None),
    description: Optional[str] = Form(None)
):
    filename = None
    if photo:
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{photo.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
    # Extract frames from video and run mock AI matching
    match_found = False
    checked_frames = 0
    if filename:
        frames = extract_frames(VIDEO_PATH, FRAMES_DIR, interval_sec=1, size=(224, 224))
        for frame_path in frames:
            checked_frames += 1
            if mock_ai_match(frame_path, os.path.join(UPLOAD_DIR, filename)):
                match_found = True
                break
        # Clean up extracted frames
        for f in frames:
            os.remove(f)
        os.rmdir(FRAMES_DIR)
    save_report_metadata(description, filename, match_found, checked_frames)
    return JSONResponse({
        "received_photo": bool(photo),
        "photo_filename": filename,
        "description": description,
        "frames_checked": checked_frames,
        "match_found": match_found
    }) 