<template>
  <div 
    class="upload-container" 
    :class="{ 'is-dragging': isDragging, 'has-file': !!fileName }"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="onDrop"
    @click="$refs.fileInput.click()"
  >
    <input 
      type="file" 
      ref="fileInput" 
      style="display: none" 
      accept="video/*" 
      @change="onFileChange"
    >
    
    <div v-if="!fileName" class="upload-idle">
      <UploadCloudIcon :size="48" class="upload-icon" />
      <p>Click or drag dashcam video here</p>
      <span class="text-muted">MP4, MOV supported</span>
    </div>
    
    <div v-else class="upload-active">
      <FileVideoIcon :size="48" class="video-icon" />
      <div class="file-info">
        <span class="file-name">{{ fileName }}</span>
        <span class="file-size">{{ fileSize }}</span>
      </div>
      <button class="remove-btn" @click.stop="clearFile">
        <XIcon :size="16" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadCloud as UploadCloudIcon, FileVideo as FileVideoIcon, X as XIcon } from 'lucide-vue-next'

const emit = defineEmits(['file-selected'])

const isDragging = ref(false)
const fileName = ref('')
const fileSize = ref('')

const onFileChange = (e) => {
  const file = e.target.files[0]
  if (file) handleFile(file)
}

const onDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('video/')) {
    handleFile(file)
  }
}

const handleFile = (file) => {
  fileName.value = file.name
  fileSize.value = (file.size / (1024 * 1024)).toFixed(2) + ' MB'
  emit('file-selected', file)
}

const clearFile = () => {
  fileName.value = ''
  fileSize.value = ''
  emit('file-selected', null)
}
</script>

<style scoped>
.upload-container {
  border: 2px dashed var(--panel-border);
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.upload-container:hover, .is-dragging {
  border-color: var(--primary);
  background: rgba(66, 133, 244, 0.05);
}

.has-file {
  border-style: solid;
  border-color: var(--accent);
  background: rgba(52, 168, 83, 0.05);
}

.upload-icon {
  color: var(--primary);
  margin-bottom: 1rem;
}

.video-icon {
  color: var(--accent);
}

.upload-active {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  position: relative;
  width: 100%;
}

.file-info {
  text-align: left;
  display: flex;
  flex-direction: column;
}

.file-name {
  font-weight: 600;
  display: block;
}

.file-size {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.remove-btn {
  position: absolute;
  right: -10px;
  top: -10px;
  background: var(--error);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(234, 67, 53, 0.3);
}
</style>
