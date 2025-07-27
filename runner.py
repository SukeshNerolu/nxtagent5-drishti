import cv2
import json
import os
import asyncio
from asyncio import Queue
from cv_agent_tool import detect_anomalies
from vlm_tool import describe_frame
from main_agent import send_to_main_agent

async def permission_prompt(queue: Queue, results, agent_callback):
    while True:
        idx, agent_response = await queue.get()
        print(f"🛑 Agent response for frame {idx}: {agent_response}")
        user_input = input("Agent requests permission to take action. Approve? (yes/no): ").strip().lower()
        followup_payload = json.dumps({
            "frame_index": idx,
            "user_permission": user_input
        }, indent=2)
        followup_response = await send_to_main_agent(followup_payload)
        print(f"🛑 Agent follow-up response: {followup_response}")
        
        # If there's an agent_callback, send the followup response
        if agent_callback:
            agent_callback(idx, followup_response)
        
        # Also update the results to include the followup response
        # We need to find the corresponding result for this frame and add the followup
        for result in results:
            if result["frame_index"] == idx:
                result["followup_response"] = followup_response
                break
        
        queue.task_done()

async def run_full_pipeline(video_path, anomaly_callback=None, agent_callback=None):
    print(f"🔍 Processing: {video_path}")
    cap = cv2.VideoCapture(video_path)
    results = []
    permission_queue = Queue()
    session_id = None

    async def process_frames():
        nonlocal session_id
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % 30 == 0:
                anomaly = detect_anomalies(frame)
                if anomaly:
                    if anomaly_callback:
                        anomaly_callback(idx, anomaly)
                    else:
                        print(f"⚠️ Anomaly detected in frame {idx}: {anomaly}")
                    vlm_desc = describe_frame(anomaly["image_b64"])
                    payload = json.dumps({
                        "frame_index": idx,
                        "anomaly": "anomaly",
                        "vlm_description": vlm_desc
                    }, indent=2)
                    agent_response, session_id = await send_to_main_agent(payload, session_id=session_id)
                    
                    # Send agent response to callback if provided
                    if agent_callback:
                        agent_callback(idx, agent_response)
                        
                    if any(line.strip().lower().startswith("ask_human:") for line in agent_response):
                        # Put the request in the permission queue and wait for the followup
                        await permission_queue.put((idx, agent_response))
                        # We will not add to results here because the permission_prompt task will handle the followup and update the result
                    else:
                        results.append({
                            "frame_index": idx,
                            "anomaly": "anomaly",
                            "vlm_description": vlm_desc,
                            "agent_response": agent_response
                        })
                    
                    # We remove the followup_response handling here because it's not in scope
            idx += 1
        cap.release()

    consumer_task = asyncio.create_task(permission_prompt(permission_queue, results, agent_callback))
    await process_frames()
    await permission_queue.join()
    consumer_task.cancel()

    with open("pipeline_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("✅ Pipeline complete. Results saved to pipeline_results.json.")

if __name__ == "__main__":
    video_file = "sample_stampede.mp4"
    if not os.path.exists(video_file):
        print(f"Video file '{video_file}' not found. Please provide a valid video file.")
    else:
        asyncio.run(run_full_pipeline(video_file))
