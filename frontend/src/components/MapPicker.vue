<template>
  <div class="map-container">
    <div class="search-box glass-panel">
      <input 
        ref="searchInput" 
        type="text" 
        placeholder="Search location or paste lat,lng..."
        @keyup.enter="handleSearch"
      />
      <button @click="handleSearch"><SearchIcon size="18" /></button>
    </div>
    <div ref="mapRef" class="google-map"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { setOptions, importLibrary } from '@googlemaps/js-api-loader'
import { Search as SearchIcon } from 'lucide-vue-next'

const props = defineProps({
  modelValue: Object
})

const emit = defineEmits(['select', 'update:modelValue'])
const mapRef = ref(null)
const searchInput = ref(null)
const marker = ref(null)
let mapInstance = null
let MarkerClass, PinClass

const mapStyles = [
  { elementType: "geometry", stylers: [{ color: "#212121" }] },
  { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#9da5b0" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#212121" }] },
  { featureType: "administrative", elementType: "geometry", stylers: [{ color: "#2f3948" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#2c2c2c" }] },
  { featureType: "road", elementType: "labels.text.fill", stylers: [{ color: "#8a8a8a" }] },
  { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#3c3c3c" }] },
  { featureType: "transit", elementType: "geometry", stylers: [{ color: "#2f3948" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#171717" }] },
]

const handleSearch = () => {
  const val = searchInput.value.value
  if (!val) return
  
  const coordsRegex = /^([-+]?\d+\.\d+)\s*,\s*([-+]?\d+\.\d+)$/
  const match = val.match(coordsRegex)
  if (match) {
    const pos = { lat: parseFloat(match[1]), lng: parseFloat(match[2]) }
    updateMapFromExternal(pos)
    return
  }
  
  const geocoder = new google.maps.Geocoder()
  geocoder.geocode({ address: val }, (results, status) => {
    if (status === "OK") {
      const pos = results[0].geometry.location
      const coords = { lat: pos.lat(), lng: pos.lng() }
      updateMapFromExternal(coords)
    }
  })
}

const placeMarker = (position, silent = false) => {
  if (!mapInstance || !MarkerClass) return

  if (marker.value) {
    marker.value.map = null
  }

  const pin = new PinClass({
    background: "#4285F4",
    borderColor: "#ffffff",
    scale: 1.2,
  })

  marker.value = new MarkerClass({
    position,
    map: mapInstance,
    content: pin.element,
  })

  if (!silent) {
    emit('select', position)
    emit('update:modelValue', position)
  }
}

const updateMapFromExternal = (pos) => {
  if (!mapInstance) return
  mapInstance.setCenter(pos)
  mapInstance.setZoom(17)
  placeMarker(pos, true) // silent update
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && mapInstance) {
    updateMapFromExternal(newVal)
  }
}, { deep: true })

onMounted(async () => {
  setOptions({
    apiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "",
    version: "weekly",
  })

  try {
    const { Map } = await importLibrary("maps")
    const { AdvancedMarkerElement, PinElement } = await importLibrary("marker")
    const { Autocomplete } = await importLibrary("places")
    
    MarkerClass = AdvancedMarkerElement
    PinClass = PinElement

    const initialCenter = props.modelValue || { lat: 32.0853, lng: 34.7818 }

    mapInstance = new Map(mapRef.value, {
      center: initialCenter,
      zoom: 15,
      // mapId: "DEMO_MAP_ID",
      disableDefaultUI: false,
      zoomControl: true,
      gestureHandling: "greedy",
      styles: mapStyles,
    })

    if (props.modelValue) {
      placeMarker(props.modelValue, true)
    }

    mapInstance.addListener("click", (e) => {
      const pos = { lat: e.latLng.lat(), lng: e.latLng.lng() }
      placeMarker(pos)
    })

    const autocomplete = new Autocomplete(searchInput.value, {
      fields: ["geometry", "name"]
    })
    
    autocomplete.addListener("place_changed", () => {
      const place = autocomplete.getPlace()
      if (place.geometry) {
        const pos = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng()
        }
        updateMapFromExternal(pos)
      }
    })
  } catch (err) {
    console.error("Google Maps failed to load:", err)
  }
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.google-map {
  width: 100%;
  height: 100%;
}

.search-box {
  position: absolute;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  z-index: 20;
  display: flex;
  background: rgba(10, 12, 16, 0.9) !important;
  border-radius: 12px !important;
  padding: 4px 8px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

.search-box input {
  flex: 1;
  background: transparent;
  border: none;
  color: white;
  padding: 10px;
  outline: none;
  font-family: inherit;
}

.search-box button {
  background: transparent;
  border: none;
  color: var(--primary);
  cursor: pointer;
  padding: 0 10px;
}
</style>
