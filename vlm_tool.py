import base64
import google.generativeai as genai

genai.configure(api_key="AIzaSyC7LMqW08PVXjK66a7t3HPWLrXS1bUPa6g")

def describe_frame(image_b64, transcript=None):
    prompt = (
        "You're analyzing CCTV footage. "
        "Describe the scene and identify potential threats (fire, stampede, weapons). "
    )
    if transcript:
        prompt += f"\nTranscript: {transcript}"

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([
        {
            "role": "user",
            "parts": [
                {"text": prompt},
                {"mime_type": "image/jpeg", "data": base64.b64decode(image_b64)}
            ]
        }
    ])
    return response.text