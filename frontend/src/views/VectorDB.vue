<template>
  <div class="vdb-page">

    <!-- ── 页头 ── -->
    <div class="vdb-header">
      <div class="vdb-header__left">
        <el-icon :size="22" color="var(--color-primary)"><Coin /></el-icon>
        <span class="vdb-title">知识库管理</span>
      </div>

      <!-- 上传按钮 -->
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :show-file-list="false"
        :accept="ACCEPT_TYPES"
        :on-change="handleFileChange"
        :disabled="uploading"
      >
        <el-button type="primary" :loading="uploading" :icon="Upload">
          上传文件
        </el-button>
      </el-upload>
    </div>

    <!-- ── 支持格式提示 ── -->
    <div class="vdb-hint">
      <el-icon><InfoFilled /></el-icon>
      支持格式：PDF、Word（docx）、TXT &nbsp;|&nbsp; 单文件最大 50 MB
    </div>

    <!-- ── 上传进度条（上传中显示） ── -->
    <div v-if="uploading" class="vdb-progress">
      <div class="vdb-progress__name">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>{{ uploadingName }} 正在上传并索引...</span>
      </div>
      <el-progress
        :percentage="uploadPercent"
        :stroke-width="6"
        :status="uploadPercent === 100 ? 'success' : ''"
        striped
        :indeterminate="uploading && uploadPercent < 100"
        :duration="5"
      />
    </div>

    <!-- ── 统计栏 ── -->
    <div class="vdb-stats">
      <div class="stat-card">
        <span class="stat-num">{{ documents.length }}</span>
        <span class="stat-label">文档总数</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ pdfCount }}</span>
        <span class="stat-label">PDF</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ docxCount }}</span>
        <span class="stat-label">Word</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">{{ txtCount }}</span>
        <span class="stat-label">TXT</span>
      </div>
    </div>

    <!-- ── 文档列表 ── -->
    <div class="vdb-body">

      <!-- 加载中 -->
      <div v-if="loading" class="vdb-status">
        <el-icon :size="32" class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="documents.length === 0" class="vdb-status">
        <el-icon :size="56" color="#c0c4cc"><FolderOpened /></el-icon>
        <p>知识库为空，点击右上角上传文件</p>
      </div>

      <!-- 文件卡片列表 -->
      <transition-group
        v-else
        name="list"
        tag="div"
        class="doc-grid"
      >
        <div
          v-for="filename in documents"
          :key="filename"
          class="doc-card"
        >
          <!-- 文件图标 -->
          <div class="doc-card__icon" :class="getFileType(filename)">
            <el-icon :size="28"><Document /></el-icon>
            <span class="doc-type-badge">{{ getExt(filename) }}</span>
          </div>

          <!-- 文件信息 -->
          <div class="doc-card__info">
            <p class="doc-name" :title="filename">{{ filename }}</p>
            <p class="doc-meta">{{ getFileType(filename).toUpperCase() }} 文档</p>
          </div>

          <!-- 操作 -->
          <div class="doc-card__actions">
            <el-popconfirm
              :title="`确定删除「${filename}」吗？`"
              confirm-button-text="删除"
              cancel-button-text="取消"
              confirm-button-type="danger"
              :icon="WarningFilled"
              icon-color="#f56c6c"
              width="240"
              @confirm="handleDelete(filename)"
            >
              <template #reference>
                <el-button
                  type="danger"
                  plain
                  size="small"
                  :icon="Delete"
                  :loading="deletingFiles.has(filename)"
                  circle
                />
              </template>
            </el-popconfirm>
          </div>
        </div>
      </transition-group>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Coin, Upload, Delete, Document,
  FolderOpened, Loading, InfoFilled,
  WarningFilled
} from '@element-plus/icons-vue'
import {
  getDocumentsAPI,
  uploadDocumentAPI,
  deleteDocumentAPI
} from '@/api/documents.js'

// ── 常量 ─────────────────────────────────────────────────
const ACCEPT_TYPES = '.pdf,.doc,.docx,.txt'
const MAX_SIZE_MB  = 50

// ── 状态 ─────────────────────────────────────────────────
const documents    = ref([])          // string[]
const loading      = ref(false)
const uploading    = ref(false)
const uploadPercent = ref(0)
const uploadingName = ref('')
const deletingFiles = ref(new Set())  // 正在删除的文件名集合

// ── 统计 ─────────────────────────────────────────────────
const pdfCount  = computed(() => documents.value.filter(f => getExt(f) === 'pdf').length)
const docxCount = computed(() => documents.value.filter(f => ['doc','docx'].includes(getExt(f))).length)
const txtCount  = computed(() => documents.value.filter(f => getExt(f) === 'txt').length)

// ── 工具函数 ──────────────────────────────────────────────

/** 获取小写扩展名，如 "pdf" */
function getExt(filename) {
  return filename.split('.').pop()?.toLowerCase() ?? ''
}

/** 根据扩展名返回类型 class */
function getFileType(filename) {
  const ext = getExt(filename)
  if (ext === 'pdf')              return 'pdf'
  if (['doc','docx'].includes(ext)) return 'word'
  if (ext === 'txt')              return 'txt'
  return 'other'
}

// ── 获取文档列表 ──────────────────────────────────────────
async function fetchDocuments() {
  loading.value = true
  try {
    const res = await getDocumentsAPI()
    documents.value = res.documents ?? []
  } catch (e) {
    ElMessage.error('获取文档列表失败：' + (e.message ?? '未知错误'))
  } finally {
    loading.value = false
  }
}

// ── 上传文件 ──────────────────────────────────────────────
async function handleFileChange(uploadFile) {
  const file = uploadFile.raw

  // 类型校验
  const ext = getExt(file.name)
  if (!['pdf', 'doc', 'docx', 'txt'].includes(ext)) {
    ElMessage.warning(`不支持的文件类型：.${ext}`)
    return
  }

  // 大小校验
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    ElMessage.warning(`文件大小超过 ${MAX_SIZE_MB} MB 限制`)
    return
  }

  // 重复校验
  if (documents.value.includes(file.name)) {
    ElMessage.warning(`「${file.name}」已存在，请先删除再上传`)
    return
  }

  uploading.value     = true
  uploadPercent.value = 0
  uploadingName.value = file.name

  try {
    const res = await uploadDocumentAPI(file, (percent) => {
      // 上传进度占 0-80%，索引阶段保留 80-100% 给后端处理
      uploadPercent.value = Math.min(percent * 0.8, 80)
    })

    uploadPercent.value = 100


    const filename = res.file || file.name
    const chunksCount = res.chunks || '未知'

     ElMessage.success(
      `「${filename}」上传成功，共切分 ${chunksCount} 个片段`
    )

    // 刷新列表
    await fetchDocuments()
  } catch (e) {
    const msg = e.response?.data?.detail ?? e.message ?? '上传失败'
    ElMessage.error('上传失败：' + msg)
  } finally {
    uploading.value = false
  }
}

// ── 删除文件 ──────────────────────────────────────────────
async function handleDelete(filename) {
  deletingFiles.value = new Set([...deletingFiles.value, filename])
  try {
    await deleteDocumentAPI(filename)
    ElMessage.success(`「${filename}」已删除`)
    // 本地直接移除，无需重新请求
    documents.value = documents.value.filter(f => f !== filename)
  } catch (e) {
    const msg = e.response?.data?.detail ?? e.message ?? '删除失败'
    ElMessage.error('删除失败：' + msg)
  } finally {
    const next = new Set(deletingFiles.value)
    next.delete(filename)
    deletingFiles.value = next
  }
}

// ── 初始化 ────────────────────────────────────────────────
onMounted(fetchDocuments)
</script>

<style scoped>
/* ── 整体布局 ─────────────────────────────────────────────── */
.vdb-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── 页头 ───────────────────────────────────────────────── */
.vdb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.vdb-header__left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.vdb-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* ── 提示栏 ─────────────────────────────────────────────── */
.vdb-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: #ecf5ff;
  border: 1px solid #b3d8ff;
  border-radius: 8px;
  font-size: 13px;
  color: #409eff;
}

/* ── 上传进度 ────────────────────────────────────────────── */
.vdb-progress {
  padding: 14px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.vdb-progress__name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* ── 统计栏 ─────────────────────────────────────────────── */
.vdb-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}
.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* ── 文档区域 ────────────────────────────────────────────── */
.vdb-body {
  min-height: 200px;
}
.vdb-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* ── 文档卡片网格 ─────────────────────────────────────────── */
.doc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.doc-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  transition: box-shadow 0.2s, transform 0.2s;
}
.doc-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  transform: translateY(-1px);
}

/* ── 文件图标 ────────────────────────────────────────────── */
.doc-card__icon {
  position: relative;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.doc-card__icon.pdf  { background: #fff2f0; color: #ff4d4f; }
.doc-card__icon.word { background: #f0f5ff; color: #2f54eb; }
.doc-card__icon.txt  { background: #f6ffed; color: #52c41a; }
.doc-card__icon.other{ background: #f5f5f5; color: #8c8c8c; }

.doc-type-badge {
  position: absolute;
  bottom: -4px;
  right: -4px;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 4px;
  border-radius: 4px;
  background: currentColor;
  color: #fff;
  line-height: 1.6;
}
/* badge 颜色跟随父级 color */
.pdf  .doc-type-badge { background: #ff4d4f; }
.word .doc-type-badge { background: #2f54eb; }
.txt  .doc-type-badge { background: #52c41a; }
.other .doc-type-badge { background: #8c8c8c; }

/* ── 文件信息 ────────────────────────────────────────────── */
.doc-card__info {
  flex: 1;
  min-width: 0;
}
.doc-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0 0 4px;
}
.doc-meta {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* ── 操作区 ──────────────────────────────────────────────── */
.doc-card__actions { flex-shrink: 0; }

/* ── 列表动画 ────────────────────────────────────────────── */
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
.list-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
