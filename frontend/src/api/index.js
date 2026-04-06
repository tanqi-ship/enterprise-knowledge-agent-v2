import axios from 'axios'

// ── 创建 Axios 实例 ──────────────────────────────────────
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// ── 防止多个请求同时触发刷新（并发锁） ──────────────────
let isRefreshing = false
let waitQueue = [] // 等待刷新完成的请求队列

const processQueue = (error, token = null) => {
  waitQueue.forEach(({ resolve, reject }) => {
    error ? reject(error) : resolve(token)
  })
  waitQueue = []
}

// ── 请求拦截器：自动附加 access_token ────────────────────
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── 响应拦截器：access_token 过期自动刷新 ────────────────
request.interceptors.response.use(
  (response) => response.data, // 直接返回 data 层，调用时无需 .data
  async (error) => {
    const originalRequest = error.config

    // 401 且不是刷新接口本身，且没有重试过
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes('/auth/refresh')
    ) {
      // 如果正在刷新，把当前请求加入等待队列
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          waitQueue.push({ resolve, reject })
        })
          .then((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return request(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('refresh_token')

      // 没有 refresh_token，直接跳登录
      if (!refreshToken) {
        isRefreshing = false
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        // 调用刷新接口
        const res = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        })
        const { access_token, refresh_token: newRefresh } = res.data

        // 更新本地 token
        saveTokens(access_token, newRefresh)

        // 通知等待队列
        processQueue(null, access_token)

        // 重试原请求
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return request(originalRequest)
      } catch (refreshError) {
        // 刷新也失败（refresh_token 过期），清除并跳登录
        processQueue(refreshError, null)
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 其他错误，提取后端错误信息
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '请求失败'

    return Promise.reject(new Error(message))
  }
)

// ── Token 工具函数 ────────────────────────────────────────
export const saveTokens = (accessToken, refreshToken) => {
  localStorage.setItem('access_token', accessToken)
  localStorage.setItem('refresh_token', refreshToken)
}

export const clearTokens = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export default request
