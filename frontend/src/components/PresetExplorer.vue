<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="presets-modal glass-panel">
      <div class="modal-header">
        <h2>Demo Scenarios</h2>
        <button class="close-btn" @click="$emit('close')"><XIcon /></button>
      </div>
      
      <div class="search-bar">
        <SearchIcon size="18" />
        <input v-model="searchQuery" placeholder="Search by video ID..." />
      </div>

      <div class="video-grid">
        <div 
          v-for="video in filteredVideos" 
          :key="video.id" 
          class="video-card"
          @click="selectVideo(video)"
        >
          <div class="video-preview">
            <img :src="'http://localhost:8000' + video.thumbnail" alt="Video Preview" />
            <div class="video-id-badge">#{{ video.id }}</div>
          </div>
          <div class="video-info">
            <div class="video-filename">{{ video.filename }}</div>
            <div class="gps-info" v-if="video.display_gps">
              <MapPinIcon size="12" /> {{ video.display_gps }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading dataset...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { X as XIcon, Search as SearchIcon, MapPin as MapPinIcon } from 'lucide-vue-next'

const emit = defineEmits(['close', 'select'])

const videos = ref([])
const loading = ref(true)
const searchQuery = ref('')

const filteredVideos = computed(() => {
  return videos.value.filter(v => v.id.includes(searchQuery.value))
})

onMounted(async () => {
  try {
    const res = await axios.get('http://localhost:8000/presets/list')
    videos.value = res.data
  } catch (err) {
    console.error('Failed to fetch presets list', err)
  } finally {
    loading.value = false
  }
})

const selectVideo = (video) => {
  emit('select', video)
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.presets-modal {
  width: 95%;
  max-width: 1000px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  padding: 2.5rem;
  border-radius: 28px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.6);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.modal-header h2 {
  font-size: 1.8rem;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.close-btn {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.close-btn:hover {
  background: rgba(255,255,255,0.1);
  transform: rotate(90deg);
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(255,255,255,0.05);
  padding: 1rem 1.5rem;
  border-radius: 16px;
  margin-bottom: 2rem;
  border: 1px solid rgba(255,255,255,0.1);
}

.search-bar input {
  background: transparent;
  border: none;
  color: white;
  width: 100%;
  outline: none;
  font-size: 1rem;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(200px, 1fr));
  gap: 1.25rem;
  overflow-y: auto;
  padding: 0.5rem;
  flex: 1;
}

.video-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 200px;
}

.video-card:hover {
  background: rgba(66, 133, 244, 0.08);
  border-color: var(--primary);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}

.video-preview {
  position: relative;
  height: 140px;
  background: #1a1a1a;
  overflow: hidden;
}

.video-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.3s, transform 0.3s;
}

.video-card:hover .video-preview img {
  transform: scale(1.05);
}

.video-id-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: var(--primary);
  color: white;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.video-info {
  padding: 1rem;
}

.video-filename {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gps-info {
  font-size: 0.75rem;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 4px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255,255,255,0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
