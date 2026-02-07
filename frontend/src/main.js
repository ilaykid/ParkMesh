import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { setOptions } from '@googlemaps/js-api-loader'

const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ""
console.log("System: Google Maps Key loaded:", apiKey ? "YES (starts with " + apiKey.substring(0, 6) + ")" : "NO (EMPTY)")

setOptions({
    apiKey,
    version: "weekly"
})

createApp(App).mount('#app')
