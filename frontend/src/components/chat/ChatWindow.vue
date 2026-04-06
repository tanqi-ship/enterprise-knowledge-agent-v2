<template>
  <div class="chat-window">
    <!-- 顶部栏 -->
    <div class="chat-header">
      <button
        v-if="sidebarCollapsed"
        class="icon-btn"
        title="展开侧边栏"
        @click="$emit('expand-sidebar')"
      >
        <el-icon><Expand /></el-icon>
      </button>
      <span class="chat-title">
        {{ chatStore.currentConv?.title || '新对话' }}
      </span>
    </div>

    <!-- 消息区域 -->
    <div ref="msgAreaRef" class="msg-area">
      <!-- 加载中 -->
      <div v-if="chatStore.loadingMsgs" class="msg-status">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <!-- 未选中会话 -->
      <div v-else-if="!chatStore.currentConvId" class="msg-status">
        <el-icon :size="48" color="#c0c4cc"><ChatDotSquare /></el-icon>
        <p>请选择或新建一个对话</p>
      </div>

      <!-- 消息列表 -->
      <template v-else>
        <!-- 空对话提示 -->
        <div v-if="chatStore.messages.length === 0" class="msg-status">
          <el-icon :size="48" color="#c0c4cc"><ChatDotSquare /></el-icon>
          <p>开始你的第一条消息吧</p>
        </div>

        <!-- 消息气泡 -->
        <div
          v-for="msg in chatStore.messages"
          :key="msg.id ?? msg.content"
          class="msg-row"
          :class="msg.role"
        >
          <!-- 头像 -->
          <div class="msg-avatar">
            <el-avatar v-if="msg.role === 'user'" :size="32" :src="userAvatar">
              {{ userInitial }}
            </el-avatar>
            <el-avatar v-else :size="32" class="ai-avatar">AI</el-avatar>
          </div>

          <!-- 气泡内容 -->
          <div class="msg-bubble" :class="{ error: msg.error }">
            <!-- 工具调用标签 -->
            <div
              v-if="msg.toolCalls?.length"
              class="tool-calls"
            >
              <div
                v-for="(tool, i) in msg.toolCalls"
                :key="i"
                class="tool-tag"
                :class="{ pending: tool.pending }"
              >
                <el-icon class="is-loading" v-if="tool.pending"><Loading /></el-icon>
                <el-icon v-else><Tools /></el-icon>
                <span>{{ tool.name }}</span>
              </div>
            </div>

            <!-- 文字内容 -->
            <div class="msg-content">
              <!-- 用户消息：纯文本 -->
              <template v-if="msg.role === 'user'">{{ msg.content }}</template>

              <!-- AI 消息：支持换行，加打字光标 -->
              <template v-else>
                <div
                class="ai-text markdown-body"
                v-html="renderMarkdown(msg.content)"
                />
                <span v-if="msg.loading" class="typing-cursor" />
              </template>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-box">

        <!-- ✅ 新增：文档分析按钮（输入框左侧） -->
        <el-tooltip content="文档分析" placement="top">
          <el-button
            class="doc-analyze-btn"
            :icon="Document"
            circle
            @click="docDialogVisible = true"
          />
        </el-tooltip>

        <!-- 输入框 -->
        <el-input
          v-model="inputText"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 5 }"
          placeholder="输入消息，Enter 发送，Shift+Enter 换行"
          resize="none"
          :disabled="chatStore.streaming"
          @keydown.enter.exact.prevent="handleSend"
          @keydown.enter.shift.exact="() => {}"
        />

        <!-- 发送 / 中断 按钮 -->
        <button
          v-if="!chatStore.streaming"
          class="send-btn"
          :disabled="!inputText.trim() || !chatStore.currentConvId"
          @click="handleSend"
        >
          <el-icon><Promotion /></el-icon>
        </button>
        <button
          v-else
          class="stop-btn"
          title="停止生成"
          @click="chatStore.abortStream()"
        >
          <el-icon><VideoPause /></el-icon>
        </button>
      </div>
      <p class="input-hint">AI 可能会出错，请自行甄别</p>
    </div>
     <!-- ✅ 新增：文档分析弹窗 -->
    <DocAnalyzeDialog v-model="docDialogVisible" />
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import {
  Expand, Loading, ChatDotSquare,
  Promotion, VideoPause, Tools
} from '@element-plus/icons-vue'
import { useChatStore } from '@/store/chat.js'
import { useUserStore } from '@/store/user.js'

import { Document } from '@element-plus/icons-vue'
import DocAnalyzeDialog from '@/components/chat/DocAnalyzeDialog.vue'

import { renderMarkdown } from '@/utils/markdown.js'


defineProps({
  sidebarCollapsed: { type: Boolean, default: false }
})
defineEmits(['expand-sidebar'])

const chatStore = useChatStore()
const userStore = useUserStore()

const inputText  = ref('')
const msgAreaRef = ref(null)

const docDialogVisible = ref(false)

// 用户头像 / 首字母
const userAvatar  = computed(() => userStore.userInfo?.avatar ?? '')
const userInitial = computed(() => userStore.userInfo?.username?.[0]?.toUpperCase() ?? 'U')

// ── 发送消息 ─────────────────────────────────────────────
function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.streaming) return
  inputText.value = ''
  chatStore.sendMessage(text)
}

// ── 自动滚动到底部 ───────────────────────────────────────
function scrollToBottom() {
  nextTick(() => {
    const el = msgAreaRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

// 消息列表变化 或 最后一条消息内容更新时，滚动到底
watch(
  () => [chatStore.messages.length, chatStore.messages.at(-1)?.content],
  scrollToBottom
)
</script>

<style scoped>
/* ── 布局 ───────────────────────────────────────────────── */
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg);
}

/* ── 顶部栏 ─────────────────────────────────────────────── */
.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  height: var(--header-height);
  padding: 0 20px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.chat-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-primary);
}
.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px; height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}
.icon-btn:hover {
  background: var(--color-bg);
  color: var(--color-text-primary);
}

/* ── 消息区域 ────────────────────────────────────────────── */
.msg-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  scroll-behavior: smooth;
}
.msg-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding-top: 80px;
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* ── 消息行 ──────────────────────────────────────────────── */
.msg-row {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  max-width: 800px;
  margin-inline: auto;
}
/* AI 消息：头像在左，气泡靠左 */
.msg-row.assistant {
  flex-direction: row;
}
/* 用户消息：头像在右，气泡靠右 */
.msg-row.user {
  flex-direction: row-reverse;
}

/* ── 头像 ────────────────────────────────────────────────── */
.msg-avatar { flex-shrink: 0; padding-top: 2px; }
.ai-avatar  { background: var(--color-primary) !important; font-size: 12px; }

/* ── 气泡 ────────────────────────────────────────────────── */
.msg-bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
  background: var(--color-surface);
  color: var(--color-text-primary);
}
.msg-row.user .msg-bubble {
  background: var(--color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.msg-row.assistant .msg-bubble {
  border-bottom-left-radius: 4px;
}
.msg-bubble.error {
  background: #fff2f0;
  color: #cf1322;
  border: 1px solid #ffccc7;
}

/* ── 工具调用标签 ─────────────────────────────────────────── */
.tool-calls { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.tool-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}
.tool-tag.pending { color: var(--color-primary); border-color: var(--color-primary); }

/* ── AI 文字 + 打字光标 ───────────────────────────────────── */
.ai-text { white-space: pre-wrap; }

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--color-text-primary);
  margin-left: 2px;
  vertical-align: text-bottom;
  border-radius: 1px;
  animation: blink 0.8s step-end infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

/* ── 输入区域 ────────────────────────────────────────────── */
.input-area {
  padding: 12px 20px 16px;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}
.input-box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 6px 8px 6px 12px;
  transition: border-color 0.2s;
}
.input-box:focus-within { border-color: var(--color-primary); }

/* 覆盖 el-input 样式 */
.input-box :deep(.el-textarea__inner) {
  border: none !important;
  box-shadow: none !important;
  background: transparent !important;
  padding: 4px 0 !important;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  color: var(--color-text-primary);
}

.send-btn, .stop-btn {
  flex-shrink: 0;
  width: 34px; height: 34px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: 16px;
}
.send-btn {
  background: var(--color-primary);
  color: #fff;
}
.send-btn:disabled {
  background: var(--color-border);
  color: var(--color-text-secondary);
  cursor: not-allowed;
}
.send-btn:not(:disabled):hover { filter: brightness(1.1); }

.stop-btn {
  background: #ff4d4f;
  color: #fff;
}
.stop-btn:hover { filter: brightness(1.1); }

.input-hint {
  margin: 6px 0 0;
  text-align: center;
  font-size: 11px;
  color: var(--color-text-secondary);
}

.doc-analyze-btn {
  flex-shrink: 0;
  margin-right: 6px;
  color: var(--el-text-color-regular);

  &:hover {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    border-color: var(--el-color-primary-light-5);
  }
}

/* Markdown 内容样式 */
.markdown-body {
  line-height: 1.7;
  word-break: break-word;
}

.markdown-body :deep(p) {
  margin: 4px 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.markdown-body :deep(li) {
  margin: 3px 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-weight: bold;
  margin: 10px 0 6px;
}

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'Courier New', monospace;
}

.markdown-body :deep(pre) {
  background: #f6f8fa;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: 13px;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #ddd;
  padding-left: 12px;
  color: #666;
  margin: 6px 0;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 14px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #ddd;
  padding: 6px 12px;
}

.markdown-body :deep(th) {
  background: #f6f8fa;
  font-weight: 600;
}

.markdown-body :deep(a) {
  color: #4080ff;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

</style>
