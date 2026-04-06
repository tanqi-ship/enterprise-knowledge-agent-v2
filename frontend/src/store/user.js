import { defineStore } from 'pinia'
import { loginAPI, logoutAPI, getMeAPI, registerAPI } from '@/api/auth.js'
import { saveTokens, clearTokens } from '@/api/index.js'

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,   // { id, username, role, is_active }
    isLoggedIn: false
  }),

  getters: {
    isAdmin: (state) => state.userInfo?.role === 'admin',
    username: (state) => state.userInfo?.username ?? ''
  },

  actions: {
    // 登录
    async login(username, password) {
      const res = await loginAPI({ username, password })
      const { access_token, refresh_token } = res

      // 存 token
      saveTokens(access_token, refresh_token)

      // 拉取用户信息
      await this.fetchUserInfo()
    },

    // 注册
    async register(formData) {
      // 过滤掉空字符串字段（phone/email/gender 非必填）
      const payload = Object.fromEntries(
        Object.entries(formData).filter(([, v]) => v !== '' && v !== null)
      )
      await registerAPI(payload)
    },

    // 获取当前用户信息
    async fetchUserInfo() {
      const res = await getMeAPI()
      this.userInfo = res
      this.isLoggedIn = true
      // 同步到 localStorage 供路由守卫使用
      localStorage.setItem('user_info', JSON.stringify(res))
    },

    // 登出
    async logout() {
      const refreshToken = localStorage.getItem('refresh_token')
      try {
        if (refreshToken) {
          await logoutAPI({ refresh_token: refreshToken })
        }
      } catch {
        // 即使接口失败也要清除本地状态
      } finally {
        this._clear()
      }
    },

    // 清除本地状态
    _clear() {
      this.userInfo = null
      this.isLoggedIn = false
      clearTokens()
      localStorage.removeItem('user_info')
    },

    // 应用启动时恢复登录状态
    async restoreSession() {
      const token = localStorage.getItem('access_token')
      if (!token) return

      try {
        await this.fetchUserInfo()
      } catch {
        this._clear()
      }
    }
  },

  persist: {
    key: 'user-store',
    storage: localStorage,
    paths: ['userInfo', 'isLoggedIn']
  }
})
