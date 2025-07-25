import pytest
from fastapi.testclient import TestClient
from main import app, UPLOAD_DIR, REPORTS_FILE
import os
import json

client = TestClient(app)

def cleanup():
    # Remove uploaded files and metadata after tests
    if os.path.exists(REPORTS_FILE):
        os.remove(REPORTS_FILE)
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            os.remove(os.path.join(UPLOAD_DIR, f))

def test_submit_lost_report_with_description():
    cleanup()
    response = client.post(
        "/lost-report",
        data={"description": "Lost black backpack"}
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Lost black backpack"
    assert response.json()["frames_checked"] == 0
    assert response.json()["match_found"] is False
    # Check metadata file
    with open(REPORTS_FILE) as f:
        data = json.load(f)
    assert data[-1]["description"] == "Lost black backpack"
    assert data[-1]["photo_filename"] is None
    assert data[-1]["frames_checked"] == 0
    assert data[-1]["match_found"] is False
    cleanup()

def test_submit_lost_report_with_photo_and_description():
    cleanup()
    with open("image-5.png", "rb") as img:
        response = client.post(
            "/lost-report",
            data={"description": "Lost person with red shirt"},
            files={"photo": ("image-5.png", img, "image/png")}
        )
    assert response.status_code == 200
    assert response.json()["received_photo"] is True
    assert response.json()["description"] == "Lost person with red shirt"
    assert response.json()["frames_checked"] > 0
    assert response.json()["match_found"] is False
    # Check file saved
    filename = response.json()["photo_filename"]
    assert filename is not None
    assert os.path.exists(os.path.join(UPLOAD_DIR, filename))
    # Check metadata file
    with open(REPORTS_FILE) as f:
        data = json.load(f)
    assert data[-1]["description"] == "Lost person with red shirt"
    assert data[-1]["photo_filename"] == filename
    assert data[-1]["frames_checked"] > 0
    assert data[-1]["match_found"] is False
    cleanup() 