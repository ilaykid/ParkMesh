from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid
import json
import subprocess
from typing import Optional
import shutil
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "videos")
SHOW_LOCAL_PRESETS = os.getenv("SHOW_LOCAL_PRESETS", "false").lower() == "true"

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"Supabase initialized for URL: {SUPABASE_URL}")
    except Exception as e:
        print(f"Failed to initialize Supabase: {e}")
else:
    print("Supabase URL or Key missing in .env")

UPLOAD_DIR = "uploads"
RESULTS_DIR = "results"
PRESET_DATA_BASE = "/mnt/c/Users/ilayk/Downloads/BDDA/BDDA"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Mount both dirs to serve files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

# Optional: Mount preset data if available
if os.path.exists(PRESET_DATA_BASE):
    # We'll serve the test footage for demo purposes
    footage_dir = os.path.join(PRESET_DATA_BASE, "test/camera_videos")
    if os.path.exists(footage_dir):
        app.mount("/preset-footage", StaticFiles(directory=footage_dir), name="presets")

@app.get("/presets/thumbnail/{video_id}")
async def get_preset_thumbnail(video_id: str):
    """Generates and returns a thumbnail for a preset video."""
    thumb_path = os.path.join(RESULTS_DIR, f"thumb_{video_id}.jpg")
    
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path)
        
    # Find the video source (local or cloud)
    video_path = None
    
    # 1. Check local fallback
    local_path = os.path.join(PRESET_DATA_BASE, f"test/camera_videos/{video_id}.mp4")
    if os.path.exists(local_path):
        video_path = local_path
    
    # 2. Check Supabase if local not found
    elif supabase:
        try:
            # We assume the filename matches video_id + .mp4 or .mov
            for ext in ['.mp4', '.mov']:
                filename = f"{video_id}{ext}"
                url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
                # Verify if exists by trying to get headers
                print(f"Checking cloud video for thumbnail: {url}")
                head = requests.head(url)
                if head.status_code == 200:
                    print(f"Found cloud video: {filename}, using for thumbnail extraction")
                    video_path = url
                    break
        except Exception as e:
            print(f"Thumb generation cloud check error: {e}")

    if not video_path:
        return {"error": "Video source not found"}
    
    # Extract 1st frame
    # ffmpeg can take a URL as input!
    print(f"Running FFmpeg to extract thumbnail from: {video_path}")
    cmd = ["ffmpeg", "-y", "-i", video_path, "-frames:v", "1", "-vcodec", "mjpeg", thumb_path]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg error: {res.stderr}")
    
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path)
    return {"error": "Failed to generate thumbnail"}

@app.get("/presets/list")
async def list_presets():
    """Lists videos from Supabase storage or local fallback."""
    videos = []
    
    # Try fetching from Supabase first
    if supabase:
        try:
            res = supabase.storage.from_(SUPABASE_BUCKET).list()
            print(f"Raw Supabase list result: {res}")
            for item in res:
                if item['name'].endswith(('.mp4', '.mov')):
                    video_id = os.path.splitext(item['name'])[0]
                    # Generate public URL
                    video_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(item['name'])
                    videos.append({
                        "id": video_id,
                        "filename": item['name'],
                        "url": video_url,
                        "thumbnail": f"/presets/thumbnail/{video_id}", # Still using local thumb cache
                        "display_gps": "Berkeley, CA (Demo)",
                        "gps": {
                            "start": "37.8715,-122.2730",
                            "display": "Berkeley Area"
                        }
                    })
            if videos:
                print(f"Found {len(videos)} videos in Supabase bucket '{SUPABASE_BUCKET}'")
                return sorted(videos, key=lambda x: x["id"])
            else:
                print(f"No videos found in Supabase bucket '{SUPABASE_BUCKET}'")
        except Exception as e:
            print(f"Supabase list error: {e}")

    # Fallback to local directory (if flag enabled or Supabase failed)
    if SHOW_LOCAL_PRESETS and os.path.exists(PRESET_DATA_BASE):
        print("Checking local presets (SHOW_LOCAL_PRESETS is True)")
        data_dir = os.path.join(PRESET_DATA_BASE, "test")
        cam_dir = os.path.join(data_dir, "camera_videos")
        if os.path.exists(cam_dir):
            for f in os.listdir(cam_dir):
                if f.endswith(".mp4"):
                    video_id = os.path.splitext(f)[0]
                    videos.append({
                        "id": video_id,
                        "filename": f,
                        "url": f"/preset-footage/{f}",
                        "thumbnail": f"/presets/thumbnail/{video_id}",
                        "display_gps": "Local Dataset",
                        "gps": None
                    })
    return sorted(videos, key=lambda x: x["id"])

tasks = {}

def run_analysis(task_id: str, video_path: str, start_gps: str):
    """
    Runs the Gemini analysis script as a background task.
    """
    tasks[task_id] = {"status": "processing", "progress": 0}
    
    # If video_path is a URL, download it first
    actual_video_path = video_path
    if video_path.startswith('http'):
        import requests
        local_filename = f"temp_{task_id}_{os.path.basename(video_path.split('?')[0])}"
        local_path = os.path.join(UPLOAD_DIR, local_filename)
        try:
            with requests.get(video_path, stream=True) as r:
                r.raise_for_status()
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            actual_video_path = local_path
        except Exception as e:
            tasks[task_id] = {"status": "failed", "error": f"Failed to download remote video: {e}"}
            return

    lat, lon = map(float, start_gps.split(','))
    # Move ~400m East for demo purposes
    end_gps = f"{lat},{lon + 0.004}"
    
    cmd = [
        "python3", "analyze_with_gemini.py",
        "--video", actual_video_path,
        "--start_gps", start_gps,
        "--end_gps", end_gps,
        "--model", "gemini-3-flash-preview"
    ]
    
    try:
        print(f"Starting analysis for task {task_id} with video: {actual_video_path}")
        process = subprocess.run(cmd, capture_output=True, text=True)
        print(f"Analysis process finished with return code {process.returncode}")
        if process.stdout: print(f"STDOUT: {process.stdout[:500]}...")
        if process.stderr: print(f"STDERR: {process.stderr}")

        # Files created by script:
        # 1. analysis_<basename>.json
        # 2. processed_<basename>.mp4
        # CRITICAL: base must match what analyze_with_gemini.py uses (os.path.basename(actual_video_path))
        base = os.path.basename(actual_video_path)
        raw_json = f"analysis_{base}.json"
        raw_video = f"processed_{os.path.splitext(base)[0]}.mp4"
        
        final_json_path = os.path.join(RESULTS_DIR, f"{task_id}.json")
        final_video_path = os.path.join(RESULTS_DIR, f"{task_id}.mp4")

        # Move files to results if they exist
        if os.path.exists(raw_json):
            with open(raw_json, 'r') as f:
                res = json.load(f)
            
            # Move frames if they exist
            for spot in res.get("spots", []):
                frame_name = spot.get("frame_url")
                if frame_name and os.path.exists(frame_name):
                    target_frame = f"{task_id}_{frame_name}"
                    shutil.move(frame_name, os.path.join(RESULTS_DIR, target_frame))
                    spot["frame_url"] = f"/results/{target_frame}"
            
            # Save final updated JSON
            with open(final_json_path, 'w') as f:
                json.dump(res, f)
            os.remove(raw_json)

        if os.path.exists(raw_video):
            shutil.move(raw_video, final_video_path)
            video_url = f"/results/{task_id}.mp4"
        else:
            video_url = f"/uploads/{base}"
        
        if os.path.exists(final_json_path):
            with open(final_json_path, 'r') as f:
                result_data = json.load(f)
            
            # Use the path provided by Gemini directly
            path_points = []
            if "travel_path" in result_data:
                path_points = result_data["travel_path"]
                # Normalize lon to lng for Google Maps
                for p in path_points:
                    if "lon" in p: p["lng"] = p.pop("lon")
            elif "path" in result_data:
                path_points = result_data["path"]
                for p in path_points:
                    if "lon" in p: p["lng"] = p.pop("lon")
            
            result_data["path"] = path_points
                
            tasks[task_id] = {
                "status": "completed",
                "result": result_data,
                "video_url": video_url
            }
        else:
            tasks[task_id] = {
                "status": "failed",
                "error": "Analysis failed to produce results.",
                "details": process.stderr
            }
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}

@app.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    start_gps: str = Form(...)
):
    task_id = str(uuid.uuid4())
    file_extension = os.path.splitext(video.filename)[1]
    video_filename = f"{task_id}{file_extension}"
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    
    # Start background analysis
    background_tasks.add_task(run_analysis, task_id, video_path, start_gps)
    
    return {"task_id": task_id}

@app.post("/process-preset")
async def process_preset(
    background_tasks: BackgroundTasks,
    video_id: str = Form(...),
    start_gps: str = Form(...),
    video_url: Optional[str] = Form(None)
):
    task_id = str(uuid.uuid4())
    
    # Use the provided URL if available (from Supabase), otherwise look locally
    target_path = video_url
    if not target_path:
        target_path = os.path.join(PRESET_DATA_BASE, f"test/camera_videos/{video_id}.mp4")
        if not os.path.exists(target_path):
            return {"error": "Video not found"}

    # Start analysis task
    background_tasks.add_task(run_analysis, task_id, target_path, start_gps)
    
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        return {"status": "not_found"}
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
