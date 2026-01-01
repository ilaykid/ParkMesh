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

app = FastAPI()

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    video_path = os.path.join(PRESET_DATA_BASE, f"test/camera_videos/{video_id}.mp4")
    thumb_path = os.path.join(RESULTS_DIR, f"thumb_{video_id}.jpg")
    
    if not os.path.exists(video_path):
        return {"error": "Video not found"}
    
    if not os.path.exists(thumb_path):
        # Extract 1st frame
        cmd = ["ffmpeg", "-y", "-i", video_path, "-frames:v", "1", "-vcodec", "mjpeg", thumb_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return FileResponse(thumb_path)

@app.get("/presets/list")
async def list_presets():
    """Lists videos from the local dataset with their GPS data."""
    if not os.path.exists(PRESET_DATA_BASE):
        return []
    
    videos = []
    data_dir = os.path.join(PRESET_DATA_BASE, "test")
    cam_dir = os.path.join(data_dir, "camera_videos")
    gps_dir = os.path.join(data_dir, "gps_jsons")
    
    if os.path.exists(cam_dir):
        for f in os.listdir(cam_dir):
            if f.endswith(".mp4"):
                video_id = os.path.splitext(f)[0]
                json_path = os.path.join(gps_dir, video_id + ".json")
                
                gps_data = None
                display_gps = ""
                if os.path.exists(json_path):
                    with open(json_path, 'r') as jf:
                        gps_raw = json.load(jf)
                        locations = gps_raw.get("locations", [])
                        if locations:
                            lat, lon = locations[0]['latitude'], locations[0]['longitude']
                            display_gps = f"{lat:.4f}, {lon:.4f}"
                            gps_data = {
                                "start": f"{lat},{lon}",
                                "end": f"{locations[-1]['latitude']},{locations[-1]['longitude']}",
                                "points": [{"lat": l["latitude"], "lng": l["longitude"]} for l in locations]
                            }
                
                videos.append({
                    "id": video_id,
                    "filename": f,
                    "url": f"/preset-footage/{f}",
                    "thumbnail": f"/presets/thumbnail/{video_id}",
                    "display_gps": display_gps,
                    "gps": gps_data
                })
    return sorted(videos, key=lambda x: int(x["id"]) if x["id"].isdigit() else x["id"])

tasks = {}

def run_analysis(task_id: str, video_path: str, start_gps: str):
    """
    Runs the Gemini analysis script as a background task.
    """
    tasks[task_id] = {"status": "processing", "progress": 0}
    
    lat, lon = map(float, start_gps.split(','))
    # Move ~400m East for demo purposes (usually staying on land in coastal cities like SF/Tel-Aviv)
    end_gps = f"{lat},{lon + 0.004}"
    
    # Run analysis, output filename is analysis_<basename>.json in the current dir
    # We should probably tell analyze_with_gemini where to put things or move them after
    cmd = [
        "python3", "analyze_with_gemini.py",
        "--video", video_path,
        "--start_gps", start_gps,
        "--end_gps", end_gps,
        "--model", "gemini-3-flash-preview"
    ]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # Files created by script:
        # 1. analysis_<basename>.json
        # 2. processed_<basename>.mp4
        base = os.path.basename(video_path)
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
    start_gps: str = Form(...)
):
    task_id = str(uuid.uuid4())
    video_path = os.path.join(PRESET_DATA_BASE, f"test/camera_videos/{video_id}.mp4")
    
    if not os.path.exists(video_path):
        return {"error": "Video not found"}

    # Start analysis task
    background_tasks.add_task(run_analysis, task_id, video_path, start_gps)
    
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        return {"status": "not_found"}
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
