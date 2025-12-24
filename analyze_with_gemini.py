import os
import json
import time
import argparse
import requests
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables (expecting GEMINI_API_KEY)
load_dotenv()

import subprocess

def preprocess_video(input_path, target_fps=3):
    """
    Downsamples the video to a lower FPS using FFmpeg to reduce file size and token count.
    Returns the path to the processed video.
    """
    output_path = f"processed_{os.path.splitext(os.path.basename(input_path))[0]}.mp4"
    print(f"Optimizing video to {target_fps} FPS: {input_path} -> {output_path}")
    
    # ffmpeg -i input -r 1 -c:v libx264 -crf 23 -preset fast -c:a copy output
    # We re-encode to ensure the keyframes match the new frame rate for easier analysis
    cmd = [
        "ffmpeg", "-y", # Overwrite output
        "-i", input_path,
        "-r", str(target_fps),
        "-c:v", "libx264",
        "-crf", "24", # Better quality (lower CRF = higher quality)
        "-preset", "fast",
        "-an", # Remove audio
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Video optimized successfully.")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error optimizing video: {e}")
        return input_path # Fallback to original

def get_video_duration(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
             "-of", "default=noprint_wrappers=1:nokey=1", video_path], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return float(result.stdout)
    except Exception as e:
        print(f"Could not determine video duration: {e}")
        return 60.0

def generate_telemetry(duration_sec, start_gps, end_gps):
    """Generates a simple linear interpolation of GPS coordinates."""
    if not start_gps or not end_gps:
        return ""
    
    try:
        lat1, lon1 = map(float, start_gps.split(','))
        lat2, lon2 = map(float, end_gps.split(','))
    except ValueError:
        print("Error parsing GPS coordinates. Use format 'lat,lon'")
        return ""
        
    telemetry = "Timestamp (sec), Latitude, Longitude\n"
    # Generate point every second
    steps = int(duration_sec) + 1
    
    for i in range(steps):
        t = i / max(1, duration_sec)
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t
        telemetry += f"{i}, {lat:.6f}, {lon:.6f}\n"
        
    return telemetry

def analyze_video(video_path, prompt_file='gemini_prompt.md', model_name='gemini-3-flash-preview', optimize=True, start_gps=None, end_gps=None):
    """
    Analyzes video using Gemini API via direct REST calls with inline Base64 data.
    This method is preferred for Gemini 3 Preview which has issues with File API for videos.
    The video is first optimized (downsampled) to ensure it fits within inline payload limits.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return

    # 1. Optimize Video
    # Justification: Inline data has size limits (~20MB). Optimization ensures we fit.
    if optimize:
        video_to_upload = preprocess_video(video_path)
    else:
        video_to_upload = video_path

    # 2. Encode Video to Base64
    print(f"Reading and encoding video: {video_to_upload}...")
    try:
        with open(video_to_upload, "rb") as video_file:
            video_data = video_file.read()
            b64_data = base64.b64encode(video_data).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: File not found: {video_to_upload}")
        return

    file_size_mb = len(video_data) / 1024 / 1024
    print(f"Payload size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 190.0: # ~200MB limit for some, but safer to be lower for inline
        print("Warning: Video size is large for inline data. Consider checking limits.")

    # 3. Read Prompt
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_text = f.read()

    # Inject Telemetry if GPS provided
    if start_gps and end_gps:
        duration = get_video_duration(video_to_upload)
        print(f"Generating telemetry for {duration:.1f}s video ({start_gps} -> {end_gps})...")
        telemetry = generate_telemetry(duration, start_gps, end_gps)
        prompt_text += f"\n\n## TELEMETRY LOG (GPS)\n{telemetry}"

    # 4. Construct Request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    generation_config = {
        "temperature": 0.0,
        "response_mime_type": "application/json"
    }

    # Add thinking config for Gemini 3 (User Request)
    if "gemini-3" in model_name:
        generation_config["thinkingConfig"] = {"thinkingLevel": "minimal"}

    # Mime type check based on extension
    mime_type = "video/mp4"
    if video_to_upload.endswith(".mov"):
        mime_type = "video/quicktime"

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_data
                    }
                },
                {"text": prompt_text}
            ]
        }],
        "generation_config": generation_config
    }

    print(f"Sending inline request to {model_name}...")
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            resp_json = response.json()
            try:
                # Handle possible thinking content or regular content
                candidate = resp_json["candidates"][0]
                text_resp = candidate["content"]["parts"][0]["text"]
                
                # Clean markdown
                text_resp = text_resp.replace("```json", "").replace("```", "").strip()
                
                result = json.loads(text_resp)
                print("\n--- Analysis Result ---")
                print(json.dumps(result, indent=2))

                # Save to file
                output_filename = f"analysis_{os.path.basename(video_path)}.json"
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
                print(f"\nSaved analysis to {output_filename}")

            except (KeyError, IndexError, json.JSONDecodeError) as e:
                print(f"\nError parsing response: {e}")
                print(json.dumps(resp_json, indent=2))
        else:
            print(f"Failed with status {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ParkLens Gemini Analyzer (Hybrid SDK/API)")
    parser.add_argument("--video", type=str, required=True, help="Path to the video file")
    parser.add_argument("--model", type=str, default="gemini-3-flash-preview", help="Model version")
    
    parser.add_argument("--no-optimize", action="store_true", help="Skip video optimization (FPS reduction)")
    
    parser.add_argument("--start_gps", type=str, help="Start GPS coords 'lat,lon'")
    parser.add_argument("--end_gps", type=str, help="End GPS coords 'lat,lon'")
    
    args = parser.parse_args()
    analyze_video(args.video, model_name=args.model, optimize=not args.no_optimize, start_gps=args.start_gps, end_gps=args.end_gps)
