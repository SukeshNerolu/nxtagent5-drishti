import cv2
import numpy as np
import base64

# Initialize background subtractor for motion detection
backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)

def detect_anomalies(frame):
    # 1. Fire detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    fire_mask = cv2.inRange(hsv, (0, 120, 70), (20, 255, 255))
    fire_area = np.count_nonzero(fire_mask) / (frame.shape[0] * frame.shape[1])
    fire_detected = fire_area > 0.01  # 1% of frame area
    
    # 2. Stampede detection using motion analysis
    fg_mask = backSub.apply(frame)
    
    # Noise reduction
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)
    
    # Find contours of moving objects
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Calculate total motion area
    motion_area = 0
    for contour in contours:
        if cv2.contourArea(contour) > 500:  # Filter small contours
            motion_area += cv2.contourArea(contour)
    
    motion_ratio = motion_area / (frame.shape[0] * frame.shape[1])
    stampede_detected = motion_ratio > 0.3  # 30% of frame has motion
    
    # Determine anomaly type
    if stampede_detected:
        anomaly_type = "stampede"
        confidence = motion_ratio
    elif fire_detected:
        anomaly_type = "fire"
        confidence = fire_area
    else:
        return None

    # Encode frame for response
    _, buffer = cv2.imencode('.jpg', frame)
    image_b64 = base64.b64encode(buffer).decode('utf-8')
    
    return {
        "image_b64": image_b64,
        "type": anomaly_type,
        "confidence": confidence
    }
