import os
import json
import time
import argparse
import requests
import base64
import subprocess
from dotenv import load_dotenv

# Load environment variables (expecting GEMINI_API_KEY)
load_dotenv()

def preprocess_video(input_path, target_fps=3):
    """
    Downsamples the video to a lower FPS using FFmpeg to reduce file size and token count.
    Returns the path to the processed video.
    """
    output_path = f"processed_{os.path.splitext(os.path.basename(input_path))[0]}.mp4"
    print(f"Optimizing video to {target_fps} FPS: {input_path} -> {output_path}")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-r", str(target_fps),
        "-c:v", "libx264",
        "-crf", "24",
        "-preset", "fast",
        "-an",
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error optimizing video: {e}")
        return input_path

def get_video_duration(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
             "-of", "default=noprint_wrappers=1:nokey=1", video_path], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return float(result.stdout)
    except Exception as e:
        print(f"Could not determine video duration: {e}")
        return 60.0

def generate_telemetry(duration_sec, start_gps, end_gps):
    if not start_gps or not end_gps:
        return ""
    
    try:
        lat1, lon1 = map(float, start_gps.split(','))
        lat2, lon2 = map(float, end_gps.split(','))
    except ValueError:
        return ""
        
    telemetry = "Timestamp (sec), Latitude, Longitude\n"
    steps = int(duration_sec) + 1
    
    for i in range(steps):
        t = i / max(1, duration_sec)
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t
        telemetry += f"{i}, {lat:.6f}, {lon:.6f}\n"
        
    return telemetry

def extract_frame(video_path, timestamp_str, output_path):
    """Extracts a single frame at the given timestamp (MM:SS)."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", timestamp_str,
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
    except Exception as e:
        print(f"Failed to extract frame at {timestamp_str}: {e}")
        return None

def analyze_video(video_path, prompt_file='gemini_prompt.md', model_name='gemini-3-flash-preview', optimize=True, target_fps=3, start_gps=None, end_gps=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    duration = get_video_duration(video_path)
    
    if optimize:
        video_to_upload = preprocess_video(video_path, target_fps=target_fps)
    else:
        video_to_upload = video_path

    print(f"Reading and encoding video: {video_to_upload}...")
    try:
        with open(video_to_upload, "rb") as video_file:
            video_data = video_file.read()
            b64_data = base64.b64encode(video_data).decode('utf-8')
    except Exception as e:
        print(f"Error: {e}")
        return

    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_text = f.read()

    if start_gps and end_gps:
        telemetry = generate_telemetry(duration, start_gps, end_gps)
        prompt_text += f"\n\n## TELEMETRY LOG (GPS)\n{telemetry}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    generation_config = {"temperature": 0.0, "response_mime_type": "application/json"}
    if "gemini-3" in model_name:
        generation_config["thinkingConfig"] = {"thinkingLevel": "minimal"}

    mime_type = "video/mp4" if not video_to_upload.endswith(".mov") else "video/quicktime"
    payload = {
        "contents": [{"role": "user", "parts": [{"inline_data": {"mime_type": mime_type, "data": b64_data}}, {"text": prompt_text}]}],
        "generation_config": generation_config
    }

    print(f"Sending request to {model_name}...")
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            resp_json = response.json()
            candidate = resp_json["candidates"][0]
            text_resp = candidate["content"]["parts"][0]["text"]
            text_resp = text_resp.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(text_resp)
            
            # Post-process: Extract frames for each spot
            print("Extracting frames for detected spots...")
            for i, spot in enumerate(result.get("spots", [])):
                t = spot.get("timestamp_start", "00:00")
                frame_filename = f"frame_{os.path.basename(video_path)}_{i}.jpg"
                if extract_frame(video_path, t, frame_filename):
                    spot["frame_url"] = frame_filename
            
            output_filename = f"analysis_{os.path.basename(video_path)}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"Saved analysis to {output_filename}")
        else:
            print(f"Failed: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ParkLens Gemini Analyzer")
    parser.add_argument("--video", type=str, required=True)
    parser.add_argument("--model", type=str, default="gemini-3-flash-preview")
    parser.add_argument("--no-optimize", action="store_true")
    parser.add_argument("--fps", type=int, default=3)
    parser.add_argument("--start_gps", type=str)
    parser.add_argument("--end_gps", type=str)
    args = parser.parse_args()
    analyze_video(args.video, model_name=args.model, optimize=not args.no_optimize, target_fps=args.fps, start_gps=args.start_gps, end_gps=args.end_gps)
