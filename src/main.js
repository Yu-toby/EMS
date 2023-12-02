import { createApp } from 'vue'

import App from './App.vue'
import router from './router'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'

import axios from "axios";
import VueAxios from "vue-axios";
axios.defaults.baseURL = "/api";

import {
    // create naive ui
    create,
    // component
    NButton
} from 'naive-ui'

const naive = create({
    components: [NButton]
})

const app = createApp(App)
app.use(router)
app.use(naive)
app.use(VueAxios, axios)
app.mount('#app')
