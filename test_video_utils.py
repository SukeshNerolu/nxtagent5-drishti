import os
import pytest
import cv2
from video_utils import extract_frames, mock_ai_match

def test_extract_frames_and_mock_match():
    video_path = "sample_video_clip.mp4"  # Placeholder, replace with real test video if available
    output_dir = "test_frames"
    reference_image = "image-5.png"
    if not os.path.exists(video_path):
        pytest.skip("Test video not available")
    frames = extract_frames(video_path, output_dir, interval_sec=1, size=(224, 224))
    assert len(frames) > 0
    for frame_path in frames:
        img = cv2.imread(frame_path)
        assert img.shape[0] == 224 and img.shape[1] == 224
        # Test mock match always returns False
        assert mock_ai_match(frame_path, reference_image) is False
    # Cleanup
    for f in frames:
        os.remove(f)
    os.rmdir(output_dir) 