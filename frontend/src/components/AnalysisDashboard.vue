<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div class="header-left">
        <button class="back-btn" @click="$emit('reset')">
          <ArrowLeftIcon />
        </button>
        <div>
          <h1>Analysis Report</h1>
          <p class="text-muted">{{ result.summary }}</p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-card glass-panel">
          <span class="stat-value">{{ result.spots.length }}</span>
          <span class="stat-label">Vacant Spots</span>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- Video Player Section -->
      <div class="video-section glass-panel">
        <div class="panel-tag">Live Feed Analysis</div>
        <video 
          ref="videoPlayer" 
          :src="videoUrl" 
          controls 
          class="main-video"
          @timeupdate="onTimeUpdate"
        ></video>
        
        <div class="timeline-markers">
          <div 
            v-for="(spot, idx) in result.spots" 
            :key="idx"
            class="marker"
            :style="{ left: getPercentage(spot.timestamp_start) + '%' }"
            @click="seekTo(spot.timestamp_start)"
          >
            <div class="marker-popover">{{ spot.reasoning }}</div>
          </div>
        </div>
      </div>

      <!-- Map View Section -->
      <div class="map-section glass-panel">
        <div class="panel-tag">Geospatial Distribution</div>
        <div ref="resultsMapRef" class="results-map"></div>
      </div>

      <!-- Spots List -->
      <div class="spots-list-section glass-panel">
        <div class="panel-tag">Detected Opportunities</div>
        <div class="spots-scroll">
          <div 
            v-for="(spot, idx) in result.spots" 
            :key="idx"
            class="spot-item"
            :class="{ active: currentSpotIdx === idx }"
            @click="seekTo(spot.timestamp_start)"
          >
            <div class="spot-icon">
              <CheckCircleIcon v-if="spot.confidence > 0.8" class="text-accent" />
              <InfoIcon v-else class="text-warning" />
            </div>
            <div class="spot-details">
              <div class="spot-time">{{ spot.timestamp_start }} - {{ spot.timestamp_end }}</div>
              <div class="spot-reason">{{ spot.reasoning }}</div>
              <div class="spot-meta">
                <span class="conf">Confidence: {{ (spot.confidence * 100).toFixed(0) }}%</span>
                <span class="coord">{{ spot.coordinates.lat.toFixed(5) }}, {{ spot.coordinates.lon.toFixed(5) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { 
  ArrowLeft as ArrowLeftIcon, 
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  MapPin as MapPinIcon
} from 'lucide-vue-next'
import { setOptions, importLibrary } from '@googlemaps/js-api-loader'

const props = defineProps({
  result: Object,
  videoUrl: String
})

const emit = defineEmits(['reset'])

const videoPlayer = ref(null)
const resultsMapRef = ref(null)
const currentSpotIdx = ref(-1)
let map = null
let markers = []
let Marker, Animation, SymbolPath

const getPercentage = (timestamp) => {
  if (!videoPlayer.value || !videoPlayer.value.duration) return 0
  const parts = timestamp.split(':')
  const seconds = parseInt(parts[0]) * 60 + parseInt(parts[1])
  return (seconds / videoPlayer.value.duration) * 100
}

const seekTo = (timestamp) => {
  const parts = timestamp.split(':')
  const seconds = parseInt(parts[0]) * 60 + parseInt(parts[1])
  videoPlayer.value.currentTime = seconds
  videoPlayer.value.play()
}

const onTimeUpdate = () => {
  const cur = videoPlayer.value.currentTime
  const idx = props.result.spots.findIndex(s => {
    const start = s.timestamp_start.split(':')
    const startSec = parseInt(start[0]) * 60 + parseInt(start[1])
    const end = s.timestamp_end.split(':')
    const endSec = parseInt(end[0]) * 60 + parseInt(end[1])
    return cur >= startSec && cur <= endSec
  })
  
  if (idx !== currentSpotIdx.value) {
    currentSpotIdx.value = idx
    if (idx !== -1 && map) {
      const spot = props.result.spots[idx]
      map.panTo({ lat: spot.coordinates.lat, lng: spot.coordinates.lon })
      if (markers[idx] && Animation) {
        markers[idx].setAnimation(Animation.BOUNCE)
        setTimeout(() => markers[idx].setAnimation(null), 1500)
      }
    }
  }
}

const mapStyles = [
  { elementType: "geometry", stylers: [{ color: "#212121" }] },
  { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#757575" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#212121" }] },
  { featureType: "road", elementType: "geometry.fill", stylers: [{ color: "#2c2c2c" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#000000" }] },
]

onMounted(async () => {
  setOptions({
    apiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "",
    version: "weekly",
  })

  const { Map } = await importLibrary("maps")
  const markerLib = await importLibrary("marker")
  Marker = markerLib.Marker
  Animation = markerLib.Animation
  SymbolPath = markerLib.SymbolPath
  
  const initialCenter = props.result.spots.length > 0 
    ? { lat: props.result.spots[0].coordinates.lat, lng: props.result.spots[0].coordinates.lon }
    : { lat: 32.0853, lng: 34.7818 }

  map = new Map(resultsMapRef.value, {
    center: initialCenter,
    zoom: 16,
    styles: mapStyles,
    disableDefaultUI: true,
  })

  props.result.spots.forEach((spot, i) => {
    const marker = new Marker({
      position: { lat: spot.coordinates.lat, lng: spot.coordinates.lon },
      map: map,
      title: `Spot ${i+1}`,
      icon: {
        path: SymbolPath.CIRCLE,
        scale: 8,
        fillColor: "#34A853",
        fillOpacity: 1,
        strokeWeight: 2,
        strokeColor: "#ffffff",
      }
    })
    markers.push(marker)
  })
})
</script>

<style scoped>
.dashboard {
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.back-btn {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  color: white;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--panel-border);
}

.stat-card {
  padding: 1rem 2rem;
  text-align: center;
  border-radius: 16px;
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
}

.stat-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  grid-template-rows: auto 400px;
  gap: 1.5rem;
}

.video-section {
  grid-column: 1;
  position: relative;
  padding: 0;
  overflow: hidden;
  border-radius: 24px;
  background: black;
}

.main-video {
  width: 100%;
  aspect-ratio: 16/9;
  display: block;
}

.panel-tag {
  position: absolute;
  top: 1.5rem;
  left: 1.5rem;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  z-index: 10;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.map-section {
  grid-column: 2;
  grid-row: 1 / 3;
  position: relative;
  padding: 0;
  overflow: hidden;
}

.results-map {
  width: 100%;
  height: 100%;
}

.spots-list-section {
  grid-column: 1;
  padding: 1.5rem;
}

.spots-scroll {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: 1rem;
  margin-top: 2rem;
}

.spot-item {
  min-width: 300px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  padding: 1.25rem;
  display: flex;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.spot-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-4px);
}

.spot-item.active {
  border-color: var(--accent);
  background: rgba(52, 168, 83, 0.1);
}

.spot-icon {
  padding-top: 4px;
}

.text-accent { color: var(--accent); }
.text-warning { color: var(--warning); }

.spot-time {
  font-weight: 700;
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
}

.spot-reason {
  font-size: 0.85rem;
  color: var(--text-main);
  margin-bottom: 0.75rem;
  line-height: 1.4;
}

.spot-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.timeline-markers {
  position: absolute;
  bottom: 50px; /* Above video controls */
  left: 0;
  right: 0;
  height: 4px;
  pointer-events: none;
}

.marker {
  position: absolute;
  width: 12px;
  height: 12px;
  background: var(--accent);
  border: 2px solid white;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  pointer-events: auto;
  transition: scale 0.2s;
}

.marker:hover {
  scale: 1.4;
  z-index: 20;
}

.marker-popover {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  color: black;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.7rem;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.marker:hover .marker-popover {
  opacity: 1;
  visibility: visible;
  bottom: 25px;
}
</style>
