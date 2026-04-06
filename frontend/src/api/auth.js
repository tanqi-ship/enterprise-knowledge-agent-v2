import request from './index.js'

// ── 认证相关接口 ──────────────────────────────────────────

// 注册
export const registerAPI = (data) => request.post('/auth/register', data)

// 登录
export const loginAPI = (data) => request.post('/auth/login', data)

// 刷新 Token
export const refreshAPI = (data) => request.post('/auth/refresh', data)

// 登出
export const logoutAPI = (data) => request.post('/auth/logout', data)

// 获取当前用户信息
export const getMeAPI = () => request.get('/auth/me')
