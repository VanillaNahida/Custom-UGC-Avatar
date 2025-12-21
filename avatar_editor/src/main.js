import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import VueCropper from 'vue-cropper'
import 'vue-cropper/dist/index.css'

const app = createApp(App)
app.use(VueCropper)
app.mount('#app')
