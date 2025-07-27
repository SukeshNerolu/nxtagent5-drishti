import warnings
warnings.filterwarnings("ignore", message="Your application has authenticated using end user credentials")

import streamlit as st
import tempfile
import asyncio
import json
import os
from runner import run_full_pipeline

# Set environment variables
os.environ["GOOGLE_CLOUD_PROJECT"] = "gen-lang-client-0658872622"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_CLOUD_DISABLE_WARNINGS"] = "1"  # Suppress warnings

st.set_page_config(page_title="Video Anomaly Detection", layout="wide")
st.title("Real-time Video Anomaly Detection")

# Create containers for UI elements
video_container = st.container()
notification_container = st.container()

# File uploader
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    # Save uploaded file to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
        tmp_file.write(uploaded_file.read())
        video_path = tmp_file.name
    
    # Display video
    with video_container:
        st.video(video_path)
    
    # Placeholder for notifications
    notification_placeholder = notification_container.empty()
    notifications = []
    
    # Custom function to capture and display anomalies
    async def process_and_capture():
        # Capture both anomalies and agent responses
        notifications = []
        
        # Define callback for anomaly detection
        def anomaly_callback(frame_number, anomaly):
            nonlocal notifications
            # Extract only the anomaly type
            anomaly_type = anomaly.get("type", "Unknown anomaly")
            notifications.append(f"Frame {frame_number}: {anomaly_type}")
            # Update notifications in real-time
            notification_placeholder.write("\n\n".join(notifications))
        
        # Define callback for agent responses
        def agent_callback(frame_number, response):
            nonlocal notifications
            # Format agent response for display
            if isinstance(response, list):
                response_text = "\n".join(response)
            else:
                response_text = str(response)
                
            notifications.append(f"Frame {frame_number}: Agent Response\n{response_text}")
            # Update notifications in real-time
            notification_placeholder.write("\n\n".join(notifications))
        
        # Run pipeline with both callbacks
        await run_full_pipeline(video_path, 
                               anomaly_callback=anomaly_callback,
                               agent_callback=agent_callback)
        return notifications
    
    # Run processing
    with st.spinner("Processing video for anomalies..."):
        anomalies = asyncio.run(process_and_capture())
        
    # Clean up temp file
    os.unlink(video_path)
    
    st.success("Processing complete!")
