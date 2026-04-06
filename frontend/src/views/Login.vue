<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Logo / 标题 -->
      <div class="auth-header">
        <div class="auth-logo">
          <el-icon :size="32" color="var(--color-primary)"><ChatDotRound /></el-icon>
        </div>
        <h1 class="auth-title">企业智能助手</h1>
        <p class="auth-subtitle">{{ isLogin ? '登录您的账号' : '创建新账号' }}</p>
      </div>

      <!-- Tab 切换 -->
      <div class="auth-tabs">
        <button
          class="auth-tab"
          :class="{ active: isLogin }"
          @click="switchMode(true)"
        >登录</button>
        <button
          class="auth-tab"
          :class="{ active: !isLogin }"
          @click="switchMode(false)"
        >注册</button>
      </div>

      <!-- 登录表单 -->
      <el-form
        v-if="isLogin"
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        size="large"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            :prefix-icon="User"
            clearable
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            placeholder="密码"
            type="password"
            :prefix-icon="Lock"
            show-password
            autocomplete="current-password"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="auth-submit-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 注册表单 -->
      <el-form
        v-else
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        size="large"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名（必填）"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            placeholder="密码（必填）"
            type="password"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            placeholder="确认密码"
            type="password"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <!-- 可选信息折叠 -->
        <div class="optional-section">
          <button
            type="button"
            class="optional-toggle"
            @click="showOptional = !showOptional"
          >
            <el-icon><ArrowDown v-if="!showOptional" /><ArrowUp v-else /></el-icon>
            选填信息（手机 / 邮箱 / 性别）
          </button>

          <transition name="slide-down">
            <div v-show="showOptional" class="optional-fields">
              <el-form-item prop="phone">
                <el-input
                  v-model="registerForm.phone"
                  placeholder="手机号（选填）"
                  :prefix-icon="Phone"
                  clearable
                />
              </el-form-item>
              <el-form-item prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="邮箱（选填）"
                  :prefix-icon="Message"
                  clearable
                />
              </el-form-item>
              <el-form-item prop="gender">
                <el-select
                  v-model="registerForm.gender"
                  placeholder="性别（选填）"
                  style="width: 100%"
                  clearable
                >
                  <el-option label="男" value="male" />
                  <el-option label="女" value="female" />
                  <el-option label="保密" value="secret" />
                </el-select>
              </el-form-item>
            </div>
          </transition>
        </div>

        <el-form-item>
          <el-button
            type="primary"
            class="auth-submit-btn"
            :loading="loading"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User, Lock, Phone, Message,
  ChatDotRound, ArrowDown, ArrowUp
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user.js'

const router = useRouter()
const userStore = useUserStore()

// ── 状态 ──────────────────────────────────────────────────
const isLogin = ref(true)
const loading = ref(false)
const showOptional = ref(false)
const loginFormRef = ref(null)
const registerFormRef = ref(null)

// ── 表单数据 ──────────────────────────────────────────────
const loginForm = reactive({ username: '', password: '' })

const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  phone: '',
  email: '',
  gender: ''
})

// ── 校验规则 ──────────────────────────────────────────────
const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const validateConfirmPwd = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度 2-20 位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' }
  ],
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '手机号格式不正确',
      trigger: 'blur'
    }
  ],
  email: [
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

// ── 切换登录/注册 ─────────────────────────────────────────
const switchMode = (toLogin) => {
  isLogin.value = toLogin
  showOptional.value = false
  // 重置表单
  loginFormRef.value?.resetFields()
  registerFormRef.value?.resetFields()
}

// ── 登录 ──────────────────────────────────────────────────
const handleLogin = async () => {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/chat')
  } catch (err) {
    ElMessage.error(err.message || '登录失败')
  } finally {
    loading.value = false
  }
}

// ── 注册 ──────────────────────────────────────────────────
const handleRegister = async () => {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const { confirmPassword, ...formData } = registerForm
    await userStore.register(formData)
    ElMessage.success('注册成功，请登录')
    switchMode(true)
    // 自动填充用户名
    loginForm.username = registerForm.username
  } catch (err) {
    ElMessage.error(err.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f4ff 0%, #f5f5f5 100%);
}

.auth-card {
  width: 420px;
  background: var(--color-surface);
  border-radius: 16px;
  padding: 40px 36px 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

/* 头部 */
.auth-header {
  text-align: center;
  margin-bottom: 28px;
}
.auth-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: var(--color-primary-light);
  border-radius: 16px;
  margin-bottom: 12px;
}
.auth-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}
.auth-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* Tab 切换 */
.auth-tabs {
  display: flex;
  background: var(--color-bg);
  border-radius: var(--radius-base);
  padding: 4px;
  margin-bottom: 24px;
}
.auth-tab {
  flex: 1;
  padding: 8px 0;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.auth-tab.active {
  background: var(--color-surface);
  color: var(--color-primary);
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

/* 提交按钮 */
.auth-submit-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  border-radius: var(--radius-base);
  margin-top: 4px;
}

/* 选填信息 */
.optional-section {
  margin-bottom: 8px;
}
.optional-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 0 10px;
  transition: color 0.2s;
}
.optional-toggle:hover {
  color: var(--color-primary);
}

/* 展开动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  max-height: 0;
}
.slide-down-enter-to,
.slide-down-leave-from {
  opacity: 1;
  max-height: 300px;
}
</style>
