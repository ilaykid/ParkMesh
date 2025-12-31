# ParkLens 🚗🔍

Advanced curbside intelligence platform built for the Google Gemini Hackathon 2025. ParkLens uses Gemini 2.0 Flash to analyze dashcam footage and identify vacant parking spots in real-time.

## features
- **AI-Powered Detection**: Leverages Gemini's spatial reasoning to distinguish between valid parking, bus lanes, and illegal zones.
- **Geospatial Syncing**: Automatically interpolates GPS coordinates for every detected spot based on route telemetry.
- **Interactive Dashboard**: A premium Vue 3 interface with synchronized video playback and Google Maps visualization.

## Project Structure
- `/frontend`: Vue 3 application (Vite).
- `server.py`: FastAPI backend for video processing and Gemini API orchestration.
- `analyze_with_gemini.py`: Core logic for video optimization and Gemini interaction.
- `gemini_prompt.md`: Structured system prompt for precise spatial analysis.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API Key
- Google Maps API Key

### 1. Server Setup
```bash
pip install -r requirements.txt
python server.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
# Add VITE_GOOGLE_MAPS_API_KEY to frontend/.env
npm run dev
```

### 3. Usage
1. Open the frontend in your browser.
2. Select your starting location on the Google Map.
3. Upload a dashcam video clip.
4. Click "Start Analysis" and wait for Gemini to process the path.
5. Explore detected spots on the interactive dashboard.
