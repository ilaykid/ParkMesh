from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
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
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Mount static files to serve processed videos or original videos
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

tasks = {}

def run_analysis(task_id: str, video_path: str, start_gps: str):
    """
    Runs the Gemini analysis script as a background task.
    In a real app, you might use a task queue like Celery.
    """
    tasks[task_id] = {"status": "processing", "progress": 0}
    
    # Example end_gps (just a dummy for linear interpolation for now, 
    # or we can ask for end_gps too. For demo, we can just simulate it)
    # Let's say it moves 0.01 degrees North/East
    lat, lon = map(float, start_gps.split(','))
    end_gps = f"{lat + 0.005},{lon + 0.005}"
    
    cmd = [
        "python3", "analyze_with_gemini.py",
        "--video", video_path,
        "--start_gps", start_gps,
        "--end_gps", end_gps,
        "--model", "gemini-3-flash-preview"
    ]
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        # The script saves analysis to analysis_<filename>.json
        output_filename = f"analysis_{os.path.basename(video_path)}.json"
        
        if os.path.exists(output_filename):
            with open(output_filename, 'r') as f:
                result_data = json.load(f)
            
            # Clean up: move analysis to results dir
            final_result_path = os.path.join(RESULTS_DIR, f"{task_id}.json")
            with open(final_result_path, 'w') as f:
                json.dump(result_data, f)
            
            tasks[task_id] = {
                "status": "completed",
                "result": result_data,
                "video_url": f"/static/{os.path.basename(video_path)}"
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

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        return {"status": "not_found"}
    return tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
