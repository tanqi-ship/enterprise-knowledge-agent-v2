import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPersistedstate from 'pinia-plugin-persistedstate'
import router from './router/index.js'
import App from './App.vue'
import { useUserStore } from './store/user.js'

import 'element-plus/dist/index.css'
import './styles/main.css'

const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPersistedstate)

app.use(pinia)
app.use(router)

// 应用启动时尝试恢复登录状态
const userStore = useUserStore()
userStore.restoreSession().finally(() => {
  app.mount('#app')
})
