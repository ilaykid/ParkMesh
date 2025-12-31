<template>
  <div class="app-container">
    <header class="main-header">
      <div class="logo">
        <span class="gemini-gradient">ParkLens</span>
        <span class="version-tag">powered by Gemini</span>
      </div>
    </header>

    <main class="content">
      <Transition name="fade" mode="out-in">
        <!-- Initial State: Upload and Map -->
        <div v-if="state === 'idle'" class="initial-layout" key="idle">
          <div class="hero-section">
            <h1 class="hero-title">Predictive <span class="gemini-gradient">Parking</span> Intelligence</h1>
            <p class="hero-subtitle">Upload your Dashcam footage and let Gemini 2.0 Flash analyze the curbside for vacant spots.</p>
          </div>

          <div class="setup-grid">
            <div class="setup-card glass-panel">
              <div class="card-header">
                <MapIcon />
                <h3>Route Origin</h3>
              </div>
              <p class="card-desc">Identify where your journey began on the map.</p>
              <div class="map-wrapper">
                <MapPicker @select="onCoordsSelect" />
              </div>
              <div v-if="coords" class="coords-display">
                <NavigationIcon size="16" />
                {{ coords.lat.toFixed(6) }}, {{ coords.lng.toFixed(6) }}
              </div>
            </div>

            <div class="setup-card glass-panel">
              <div class="card-header">
                <VideoIcon />
                <h3>Footage</h3>
              </div>
              <p class="card-desc">Drag & drop your dashcam MP4/MOV file.</p>
              <VideoUpload @file-selected="onFileSelected" />
              
              <button 
                class="btn-primary analyze-btn" 
                :disabled="!canStart"
                @click="startAnalysis"
              >
                Start Analysis
                <SparklesIcon v-if="canStart" class="sparkle" />
              </button>
            </div>
          </div>
        </div>

        <!-- Processing State -->
        <div v-else-if="state === 'processing'" class="processing-layout" key="processing">
          <div class="processing-content glass-panel">
            <div class="loader-visual">
              <div class="circle-outer"></div>
              <div class="circle-inner"></div>
              <div class="ai-orb"></div>
            </div>
            <h2>Gemini is analyzing the path...</h2>
            <p>Processing pixels, detecting vehicles, and identifying compliance rules.</p>
            <div class="progress-bar-container">
              <div class="progress-bar-fill" :style="{ width: progress + '%' }"></div>
            </div>
            <p class="status-msg text-muted">{{ statusMsg }}</p>
          </div>
        </div>

        <!-- Results Dashboard -->
        <div v-else-if="state === 'results'" class="results-layout" key="results">
          <AnalysisDashboard :result="analysisResult" :videoUrl="videoUrl" @reset="reset" />
        </div>
      </Transition>
    </main>

    <footer class="main-footer">
      Created for Google Gemini Hackathon 2025
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { 
  MapPin as MapIcon, 
  Video as VideoIcon, 
  Navigation as NavigationIcon,
  Sparkles as SparklesIcon
} from 'lucide-vue-next'
import MapPicker from './components/MapPicker.vue'
import VideoUpload from './components/VideoUpload.vue'
import AnalysisDashboard from './components/AnalysisDashboard.vue'

const state = ref('idle') // idle, processing, results
const coords = ref(null)
const selectedFile = ref(null)
const progress = ref(0)
const statusMsg = ref('Initializing...')
const taskId = ref(null)
const analysisResult = ref(null)
const videoUrl = ref('')

const canStart = computed(() => coords.value && selectedFile.value)

const onCoordsSelect = (c) => {
  coords.value = c
}

const onFileSelected = (file) => {
  selectedFile.value = file
}

const startAnalysis = async () => {
  if (!canStart.value) return
  
  state.value = 'processing'
  progress.value = 10
  statusMsg.value = 'Uploading video to secure processing node...'
  
  const formData = new FormData()
  formData.append('video', selectedFile.value)
  formData.append('start_gps', `${coords.value.lat},${coords.value.lng}`)
  
  try {
    const response = await axios.post('http://localhost:8000/upload', formData)
    taskId.value = response.data.task_id
    pollStatus()
  } catch (err) {
    alert('Upload failed: ' + err.message)
    state.value = 'idle'
  }
}

const pollStatus = async () => {
  if (!taskId.value) return
  
  try {
    const response = await axios.get(`http://localhost:8000/status/${taskId.value}`)
    const data = response.data
    
    if (data.status === 'processing') {
      progress.value = Math.min(progress.value + 5, 95)
      statusMsg.value = 'Gemini 3 is thinking... (Analyzing spatial geometry)'
      setTimeout(pollStatus, 3000)
    } else if (data.status === 'completed') {
      progress.value = 100
      statusMsg.value = 'Success!'
      analysisResult.value = data.result
      videoUrl.value = 'http://localhost:8000' + data.video_url
      setTimeout(() => {
        state.value = 'results'
      }, 1000)
    } else if (data.status === 'failed') {
      alert('Analysis failed: ' + data.error)
      state.value = 'idle'
    }
  } catch (err) {
    console.error('Polling error', err)
    setTimeout(pollStatus, 3000)
  }
}

const reset = () => {
  state.value = 'idle'
  coords.value = null
  selectedFile.value = null
  progress.value = 0
  taskId.value = null
  analysisResult.value = null
}
</script>

<style scoped>
.app-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
}

.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4rem;
}

.logo {
  font-size: 2rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.version-tag {
  font-size: 0.8rem;
  color: var(--text-muted);
  background: var(--panel-bg);
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 400;
}

.hero-section {
  text-align: center;
  margin-bottom: 4rem;
}

.hero-title {
  font-size: 4rem;
  font-weight: 800;
  margin-bottom: 1rem;
  letter-spacing: -1px;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--text-muted);
  max-width: 600px;
  margin: 0 auto;
}

.setup-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.setup-card {
  padding: 2rem;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.card-header h3 {
  font-size: 1.5rem;
  font-weight: 600;
}

.card-desc {
  color: var(--text-muted);
  margin-bottom: 2rem;
}

.map-wrapper {
  height: 400px;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 1rem;
  border: 1px solid var(--panel-border);
}

.coords-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--panel-bg);
  padding: 8px 16px;
  border-radius: 30px;
  width: fit-content;
  font-family: monospace;
  color: var(--primary);
}

.analyze-btn {
  margin-top: 2rem;
  padding: 1.5rem;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.analyze-btn:disabled {
  opacity: 0.3;
  filter: grayscale(1);
  cursor: not-allowed;
}

.sparkle {
  animation: rotate 3s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Processing Layout */
.processing-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem 0;
}

.processing-content {
  max-width: 600px;
  width: 100%;
  padding: 4rem;
  text-align: center;
}

.loader-visual {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 3rem;
}

.circle-outer {
  position: absolute;
  inset: 0;
  border: 4px solid var(--primary);
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 2s linear infinite;
}

.circle-inner {
  position: absolute;
  inset: 20px;
  border: 4px solid var(--accent);
  border-radius: 50%;
  border-bottom-color: transparent;
  animation: spin 1.5s linear reverse infinite;
}

.ai-orb {
  position: absolute;
  inset: 40px;
  background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

.progress-bar-container {
  height: 8px;
  background: var(--panel-bg);
  border-radius: 4px;
  margin: 2rem 0 1rem;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--primary);
  transition: width 0.5s ease;
  box-shadow: 0 0 15px var(--primary-glow);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.main-footer {
  text-align: center;
  padding: 4rem 0;
  color: var(--text-muted);
  font-size: 0.9rem;
  border-top: 1px solid var(--panel-border);
  margin-top: auto;
}
</style>
