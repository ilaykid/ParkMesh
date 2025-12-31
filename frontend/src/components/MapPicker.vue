<template>
  <div ref="mapRef" class="google-map"></div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { setOptions, importLibrary } from '@googlemaps/js-api-loader'

const emit = defineEmits(['select'])
const mapRef = ref(null)
const marker = ref(null)

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

onMounted(async () => {
  setOptions({
    apiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "",
    version: "weekly",
  })

  try {
    const { Map } = await importLibrary("maps")
    const { AdvancedMarkerElement, PinElement } = await importLibrary("marker")

    const defaultLocation = { lat: 32.0853, lng: 34.7818 }

    const map = new Map(mapRef.value, {
      center: defaultLocation,
      zoom: 15,
      mapId: "DEMO_MAP_ID", // Required for AdvancedMarkerElement
      disableDefaultUI: false,
      zoomControl: true,
      gestureHandling: "greedy",
      styles: mapStyles,
    })

    map.addListener("click", (e) => {
      const clickedLat = e.latLng.lat()
      const clickedLng = e.latLng.lng()
      const position = { lat: clickedLat, lng: clickedLng }

      if (marker.value) {
        marker.value.map = null
      }

      const pin = new PinElement({
        background: "#4285F4",
        borderColor: "#ffffff",
        glyphColor: "#ffffff",
        scale: 1.2,
      })

      marker.value = new AdvancedMarkerElement({
        position,
        map,
        content: pin.element,
        title: "Selected Origin",
      })

      emit('select', position)
    })
  } catch (err) {
    console.error("Google Maps failed to load:", err)
  }
})
</script>

<style scoped>
.google-map {
  width: 100%;
  height: 100%;
}
</style>
