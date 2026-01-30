# ParkMesh 🚗🔍

**AI-Powered Curbside Intelligence Platform**

ParkMesh is an advanced parking spot detection system built for the Google Gemini Hackathon 2026. It leverages Google's Gemini 3.0 Flash model to analyze dashcam footage and identify available parking spots along city streets in real-time.

## 🌟 Features

### Core Capabilities
- **🤖 AI-Powered Detection**: Uses Gemini 3.0's advanced spatial reasoning to analyze video footage and distinguish between:
  - Valid parking spots
  - Occupied spaces
  - Bus lanes and no-parking zones
  - Illegal parking areas
  
- **🌍 Geospatial Integration**: Automatically interpolates GPS coordinates for every detected parking spot based on route telemetry

- **🎨 Interactive Dashboard**: Premium Vue 3 web interface featuring:
  - Synchronized video playback
  - Google Maps visualization
  - Real-time spot detection overlay
  - Modern, responsive design

### How It Works

ParkMesh uses **Gemini 3.0 Flash** for comprehensive video analysis:
- Video optimization and preprocessing (FFmpeg downsampling to 3 FPS)
- GPS telemetry interpolation across the entire route
- Frame extraction at detected spot timestamps
- Structured JSON output with GPS coordinates, confidence scores, and metadata


## 🏗️ Project Structure

```
ParkMesh/
├── analyze_with_gemini.py      # Gemini AI analysis script
├── server.py                   # FastAPI backend server
├── gemini_prompt.md            # Structured prompt for Gemini
├── requirements.txt            # Python dependencies
├── .env                        # API keys (DO NOT commit)
├── frontend/                   # Vue 3 web application
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── uploads/                    # Uploaded video files
└── results/                    # Analysis results and frames
```

## 🚀 Getting Started

### Prerequisites

Before running ParkMesh, ensure you have the following installed:

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **FFmpeg** (for video processing)
- **Conda** (recommended for environment management)
- **Google Gemini API Key** ([Get one here](https://ai.google.dev/))
- **Google Maps API Key** ([Get one here](https://console.cloud.google.com/))

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd ParkMesh
```

#### 2. Set Up Python Environment

**Using Conda (Recommended):**
```bash
# Create and activate conda environment
conda create -n parkmesh python=3.10
conda activate parkmesh

# Install Python dependencies
pip install -r requirements.txt
pip install fastapi uvicorn
```

#### 3. Configure Environment Variables

Create or update the `.env` file in the project root:

```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

#### 4. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create frontend .env file
echo "VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here" > .env
```

## 🎯 Usage

### Full Web Application

This runs the complete stack with the premium web interface.

**Terminal 1 - Start Backend Server:**
```bash
conda activate parkmesh
python server.py
```
The server will start at `http://localhost:8000`

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```
The frontend will start at `http://localhost:5173`

**Using the Application:**
1. Open `http://localhost:5173` in your browser
2. Click on the map to select your starting location
3. Upload a dashcam video (MP4/MOV format)
4. Click "Start Analysis" and wait for Gemini to process
5. View detected parking spots on the interactive map
6. Click on spots to see exact frames and details

### Command-Line Analysis

Analyze a video directly using Gemini AI (without the web interface):

```bash
conda activate parkmesh

python analyze_with_gemini.py \
  --video path/to/your/video.mp4 \
  --start_gps "40.7128,-74.0060" \
  --end_gps "40.7138,-74.0050" \
  --model gemini-3-flash-preview \
  --fps 3
```

**Parameters:**
- `--video`: Path to dashcam video file
- `--start_gps`: Starting GPS coordinates (lat,lon)
- `--end_gps`: Ending GPS coordinates (lat,lon)
- `--model`: Gemini model to use (default: gemini-3-flash-preview)
- `--fps`: Target FPS for optimization (default: 3)
- `--no-optimize`: Skip video optimization (faster but uses more tokens)

**Output:**
- `analysis_<video_name>.json`: Detailed results with spots and GPS
- `processed_<video_name>.mp4`: Optimized video
- `frame_<video_name>_<N>.jpg`: Extracted frames for each spot



## 📊 API Endpoints

When running `server.py`, the following endpoints are available:

### Upload & Process
- `POST /upload` - Upload video for analysis
  - Form data: `video` (file), `start_gps` (string)
  - Returns: `{"task_id": "uuid"}`

### Status & Results
- `GET /status/{task_id}` - Check analysis status
  - Returns: status, progress, or results

### Preset Videos (if available)
- `GET /presets/list` - List available preset videos
- `POST /process-preset` - Process a preset video
- `GET /presets/thumbnail/{video_id}` - Get video thumbnail

### Static Files
- `/uploads/*` - Uploaded videos
- `/results/*` - Analysis results and frames

## 🧠 How It Works

### Gemini Analysis Pipeline

1. **Video Preprocessing**: 
   - FFmpeg downsamples video to 3 FPS
   - Reduces file size and API token usage
   - Maintains quality for detection

2. **GPS Telemetry Generation**:
   - Interpolates GPS coordinates across video duration
   - Creates synchronized location log

3. **Gemini Processing**:
   - Uploads optimized video + telemetry
   - Uses structured prompt from `gemini_prompt.md`
   - Gemini analyzes spatial layout and parking regulations

4. **Post-Processing**:
   - Extracts frames at detected spot timestamps
   - Generates JSON with GPS coordinates, timestamps, and confidence scores



## 🔧 Configuration

### Gemini Model Settings

In `analyze_with_gemini.py`:
- `--model`: Gemini model to use (default: `gemini-3-flash-preview`)
- `--fps`: Target FPS for video optimization (default: 3)
- `--no-optimize`: Skip video optimization to preserve original quality

In `server.py`:
- `UPLOAD_DIR`: Directory for uploaded videos (default: `uploads/`)
- `RESULTS_DIR`: Directory for analysis results (default: `results/`)

## 🐛 Troubleshooting

### Common Issues

**"GEMINI_API_KEY not found"**
- Ensure `.env` file exists in project root
- Check API key is valid

**"Could not open video source"**
- Verify video file path is correct
- Check video codec is supported (H.264 recommended)


**Frontend can't connect to backend**
- Ensure server is running on port 8000
- Check CORS settings in `server.py`

**FFmpeg not found**
- Install FFmpeg: `sudo apt install ffmpeg` (Linux) or `brew install ffmpeg` (Mac)

## 📝 Environment Variables Reference

### Root `.env`
```
GEMINI_API_KEY=<your_gemini_api_key>
GOOGLE_MAPS_API_KEY=<your_maps_api_key>
```

### Frontend `.env`
```
VITE_GOOGLE_MAPS_API_KEY=<your_maps_api_key>
```

## 🎨 Tech Stack

**Backend:**
- Python 3.10+
- FastAPI (Web server)
- Google Gemini 3.0 Flash (AI analysis)
- FFmpeg (Video optimization)

**Frontend:**
- Vue 3 (Framework)
- Vite (Build tool)
- Google Maps JavaScript API
- Modern CSS with animations

## 📄 License

This project was created for the Google Gemini Hackathon 2026.

## What's next for ParkMesh
The "Mesh" in ParkMesh represents our vision for a hyper-connected, live urban grid. Our next milestone is a direct integration with cloud-connected dashcams, allowing us to ingest live video streams in real-time. By leveraging the low-latency inference of **Gemini 3.0 Flash**, we aim to extract and broadcast parking availability **within seconds** of a camera scanning a street. This real-time feedback loop will turn every connected vehicle into a live sensor, creating a self-healing, instant map of city parking that updates as fast as traffic moves.

---

**Built with ❤️ for the Google Gemini Hackathon 2026**
