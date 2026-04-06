<template>
  <el-dialog
    v-model="visible"
    title="文档分析"
    width="680px"
    :close-on-click-modal="false"
    destroy-on-close
    class="doc-analyze-dialog"
    @closed="handleClosed"
  >
    <!-- ── 上传区域 ── -->
    <div v-if="!result" class="upload-section">
      <!-- 拖拽上传区 -->
      <el-upload
        ref="uploadRef"
        class="doc-uploader"
        drag
        :auto-upload="false"
        :multiple="false"
        :limit="1"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        :accept="acceptTypes"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          拖拽文件到此处，或 <em>点击选择文件</em>
        </div>
        <div class="upload-hint">
          支持 PDF、TXT、DOCX、MD，最大处理 6000 字符
        </div>
      </el-upload>

      <!-- 已选文件提示 -->
      <div v-if="selectedFile" class="selected-file">
        <el-icon><Document /></el-icon>
        <span class="file-name">{{ selectedFile.name }}</span>
        <span class="file-size">{{ formatSize(selectedFile.size) }}</span>
        <el-icon class="remove-icon" @click="removeFile"><CircleClose /></el-icon>
      </div>

      <!-- 问题输入 -->
      <div class="question-section">
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          placeholder="输入你的问题（可选），例如：总结文档要点、提取关键信息..."
          maxlength="200"
          show-word-limit
          resize="none"
        />
      </div>
    </div>

    <!-- ── 分析结果区域 ── -->
    <div v-else class="result-section">
      <!-- 截断警告 -->
      <el-alert
        v-if="result.truncated"
        type="warning"
        :closable="false"
        show-icon
        class="truncate-alert"
      >
        <template #title>
          文档内容较长，已截取前 6000 字符进行分析，结果可能不完整
        </template>
      </el-alert>

      <!-- 文件信息栏 -->
      <div class="result-meta">
        <span class="meta-item">
          <el-icon><Document /></el-icon>
          {{ result.filename }}
        </span>
        <span class="meta-item">
          <el-icon><Reading /></el-icon>
          已分析 {{ result.char_count.toLocaleString() }} 字符
        </span>
      </div>

      <!-- Markdown 渲染结果 -->
      <div class="result-content markdown-body" v-html="renderedAnswer" />
    </div>

    <!-- ── 底部操作栏 ── -->
    <template #footer>
      <!-- 未出结果时 -->
      <div v-if="!result" class="footer-actions">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!selectedFile"
          @click="handleAnalyze"
        >
          {{ loading ? '分析中...' : '开始分析' }}
        </el-button>
      </div>

      <!-- 出结果后 -->
      <div v-else class="footer-actions">
        <el-button @click="handleReset">重新分析</el-button>
        <el-button @click="handleCopy" :icon="CopyDocument">
          {{ copied ? '已复制' : '复制结果' }}
        </el-button>
        <el-button type="primary" @click="handleClose">完成</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  UploadFilled,
  Document,
  CircleClose,
  Reading,
  CopyDocument
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { analyzeDocumentAPI } from '@/api/documents'
import { useChatStore } from '@/store/chat' // 取 threadId

// ── Props & Emits ───────────────────────────────────────
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})
const emit = defineEmits(['update:modelValue'])

// ── Store ───────────────────────────────────────────────
const chatStore = useChatStore()

// ── 响应式状态 ──────────────────────────────────────────
const uploadRef = ref(null)
const selectedFile = ref(null)   // File 对象
const question = ref('')
const loading = ref(false)
const result = ref(null)         // 接口返回数据
const copied = ref(false)

// ── 弹窗双向绑定 ────────────────────────────────────────
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// ── 支持的文件类型 ──────────────────────────────────────
const acceptTypes = '.pdf,.txt,.docx,.doc,.md'

// ── Markdown 渲染 ────────────────────────────────────────
const renderedAnswer = computed(() => {
  if (!result.value?.answer) return ''
  // marked 转换 + DOMPurify 防 XSS
  return DOMPurify.sanitize(marked.parse(result.value.answer))
})

// ── 文件处理 ─────────────────────────────────────────────
function handleFileChange(uploadFile) {
  selectedFile.value = uploadFile.raw // 取原始 File 对象
}

function handleExceed() {
  ElMessage.warning('每次只能上传一个文件，请先移除当前文件')
}

function removeFile() {
  selectedFile.value = null
  uploadRef.value?.clearFiles()
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ── 核心：发起分析 ───────────────────────────────────────
async function handleAnalyze() {
  if (!selectedFile.value) return

  loading.value = true
  try {
    const threadId = chatStore.currentConvId ?? ''
    const res = await analyzeDocumentAPI(
      selectedFile.value,
      question.value.trim(),
      threadId
    )

    result.value = res


  } catch (err) {
    const msg = err.response?.data?.detail || '分析失败，请重试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

// ── 复制结果 ─────────────────────────────────────────────
async function handleCopy() {
  if (!result.value?.answer) return
  try {
    await navigator.clipboard.writeText(result.value.answer)
    copied.value = true
    ElMessage.success('已复制到剪贴板')
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    ElMessage.error('复制失败，请手动选择文本')
  }
}

// ── 重置回初始状态 ───────────────────────────────────────
function handleReset() {
  result.value = null
  selectedFile.value = null
  question.value = ''
  uploadRef.value?.clearFiles()
}

// ── 关闭弹窗 ─────────────────────────────────────────────
function handleClose() {
  visible.value = false
}

// 弹窗完全关闭后重置（destroy-on-close 已处理 DOM，这里重置数据）
function handleClosed() {
  handleReset()
}
</script>

<style scoped lang="scss">
// ── 上传区 ───────────────────────────────────────────────
.upload-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.doc-uploader {
  width: 100%;

  :deep(.el-upload-dragger) {
    padding: 30px 20px;
    border-radius: 8px;
    transition: border-color 0.2s;

    &:hover {
      border-color: var(--el-color-primary);
    }
  }
}

.upload-icon {
  font-size: 48px;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.upload-text {
  font-size: 15px;
  color: var(--el-text-color-regular);

  em {
    color: var(--el-color-primary);
    font-style: normal;
    cursor: pointer;
  }
}

.upload-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

// ── 已选文件 ─────────────────────────────────────────────
.selected-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  font-size: 13px;

  .file-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--el-text-color-primary);
  }

  .file-size {
    color: var(--el-text-color-secondary);
    flex-shrink: 0;
  }

  .remove-icon {
    cursor: pointer;
    color: var(--el-text-color-placeholder);
    flex-shrink: 0;
    transition: color 0.2s;

    &:hover {
      color: var(--el-color-danger);
    }
  }
}

// ── 结果区 ───────────────────────────────────────────────
.result-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.truncate-alert {
  border-radius: 6px;
}

.result-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  padding: 0 2px;

  .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.result-content {
  max-height: 380px;
  overflow-y: auto;
  padding: 16px;
  background: var(--el-fill-color-extra-light);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  font-size: 14px;
  line-height: 1.7;

  // Markdown 基础样式
  :deep(h1), :deep(h2), :deep(h3) {
    margin: 12px 0 6px;
    font-weight: 600;
  }
  :deep(h1) { font-size: 18px; }
  :deep(h2) { font-size: 16px; }
  :deep(h3) { font-size: 14px; }

  :deep(p) { margin: 6px 0; }

  :deep(ul), :deep(ol) {
    padding-left: 20px;
    margin: 6px 0;
  }

  :deep(li) { margin: 4px 0; }

  :deep(code) {
    background: var(--el-fill-color);
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 13px;
    font-family: 'Fira Code', monospace;
  }

  :deep(pre) {
    background: var(--el-fill-color);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;

    code { background: none; padding: 0; }
  }

  :deep(blockquote) {
    border-left: 3px solid var(--el-color-primary-light-5);
    padding-left: 12px;
    color: var(--el-text-color-secondary);
    margin: 8px 0;
  }

  :deep(strong) { font-weight: 600; }

  :deep(hr) {
    border: none;
    border-top: 1px solid var(--el-border-color);
    margin: 12px 0;
  }
}

// ── 底部按钮 ─────────────────────────────────────────────
.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
