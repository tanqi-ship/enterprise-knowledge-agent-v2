import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/Chat.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/vector-db',
    name: 'VectorDB',
    component: () => import('@/views/VectorDB.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    // 默认跳转
    path: '/',
    redirect: '/chat'
  },
  {
    // 404 兜底
    path: '/:pathMatch(.*)*',
    redirect: '/chat'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ── 全局路由守卫 ─────────────────────────────────────────
router.beforeEach((to, from, next) => {
  const accessToken = localStorage.getItem('access_token')
  const isLoggedIn = !!accessToken

  // 需要登录但未登录
  if (to.meta.requiresAuth && !isLoggedIn) {
    return next('/login')
  }

  // 已登录不能访问登录页
  if (to.path === '/login' && isLoggedIn) {
    return next('/chat')
  }

  // 需要管理员权限（从 localStorage 读取角色）
  if (to.meta.requiresAdmin) {
    const userInfo = localStorage.getItem('user_info')
    const role = userInfo ? JSON.parse(userInfo).role : null
    if (role !== 'admin') {
      return next('/chat') // 无权限跳回聊天页
    }
  }

  next()
})

export default router
