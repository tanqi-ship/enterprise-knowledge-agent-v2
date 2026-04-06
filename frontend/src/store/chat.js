import { defineStore } from 'pinia'
import {
  getConversationsAPI,
  createConversationAPI,
  deleteConversationAPI,
  renameConversationAPI,
  getMessagesAPI,
  sendMessageStream        // ← 新增
} from '@/api/chat.js'

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversations:  [],
    currentConvId:  null,
    messages:       [],
    loadingConvs:   false,
    loadingMsgs:    false,
    streaming:      false,
    _abortStream:   null    // 内部：中断函数
  }),

  getters: {
    currentConv: (state) =>
      state.conversations.find((c) => c.thread_id === state.currentConvId) ?? null,

    sortedConversations: (state) =>
      [...state.conversations].sort(
        (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
      )
  },

  actions: {
    // ── 加载会话列表 ───────────────────────────────────────
    async fetchConversations() {
      this.loadingConvs = true
      try {
        const res = await getConversationsAPI()
        this.conversations = Array.isArray(res) ? res : []
      } finally {
        this.loadingConvs = false
      }
    },

    // ── 选择会话 ───────────────────────────────────────────
    async selectConversation(threadId) {
      if (this.currentConvId === threadId) return
      if (this.streaming) return

      this.currentConvId = threadId
      this.messages = []
      await this.fetchMessages(threadId)
    },

    // ── 加载消息 ───────────────────────────────────────────
    async fetchMessages(threadId) {
      this.loadingMsgs = true
      try {
        const res = await getMessagesAPI(threadId)
        // 后端返回 { messages: [...] }
        this.messages = Array.isArray(res?.messages) ? res.messages : []
      } finally {
        this.loadingMsgs = false
      }
    },

    // ── 新建会话 ───────────────────────────────────────────
    async createConversation() {
      if (this.streaming) return
      const res = await createConversationAPI()
      this.conversations.unshift(res)
      await this.selectConversation(res.thread_id)
      return res
    },

    // ── 删除会话 ───────────────────────────────────────────
    async deleteConversation(threadId) {
      await deleteConversationAPI(threadId)
      this.conversations = this.conversations.filter(
        (c) => c.thread_id !== threadId
      )
      if (this.currentConvId === threadId) {
        this.currentConvId = null
        this.messages = []
        if (this.conversations.length > 0) {
          const next = [...this.conversations].sort(
            (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
          )[0]
          await this.selectConversation(next.thread_id)
        }
      }
    },

    // ── 重命名会话 ─────────────────────────────────────────
    async renameConversation(threadId, title) {
      await renameConversationAPI(threadId, title)
      const conv = this.conversations.find((c) => c.thread_id === threadId)
      if (conv) conv.title = title
    },

    // ── 流式发送消息 ───────────────────────────────────────
    sendMessage(content) {
      if (this.streaming || !this.currentConvId) return
      if (!content?.trim()) return

      const threadId = this.currentConvId

      // 1. 追加用户消息
      this.messages.push({
        id:         `user-${Date.now()}`,
        role:       'user',
        content:    content.trim(),
        created_at: new Date().toISOString()
      })

      // 2. 追加 AI 占位消息
      this.messages.push({
        id:       `assistant-${Date.now()}`,
        role:     'assistant',
        content:  '',
        toolCalls: [],   // 工具调用记录
        loading:  true,  // 显示打字光标
        error:    false
      })

      this.streaming = true

      // 3. 发起流式请求
      this._abortStream = sendMessageStream(threadId, content.trim(), {

        onText: (chunk) => {
          const last = this.messages.at(-1)
          if (last?.role === 'assistant') {
            last.content += chunk
            last.loading  = false
          }
        },

        onTool: (name) => {
          const last = this.messages.at(-1)
          if (last?.role === 'assistant') {
            last.toolCalls.push({ name, result: null, pending: true })
          }
        },

        onToolResult: (content) => {
          const last = this.messages.at(-1)
          if (last?.role === 'assistant') {
            // 找到最后一个 pending 的工具调用，填入结果
            const tool = [...last.toolCalls].reverse().find((t) => t.pending)
            if (tool) {
              tool.result  = content
              tool.pending = false
            }
          }
        },

        onDone: () => {
          const last = this.messages.at(-1)
          if (last?.role === 'assistant') {
            last.loading = false
          }
          this.streaming    = false
          this._abortStream = null
          // 更新会话时间（本地）
          const conv = this.conversations.find((c) => c.thread_id === threadId)
          if (conv) conv.updated_at = new Date().toISOString()
        },

        onError: (err) => {
          const last = this.messages.at(-1)
          if (last?.role === 'assistant') {
            last.content = '请求出错，请重试'
            last.loading = false
            last.error   = true
          }
          this.streaming    = false
          this._abortStream = null
          console.error('[stream error]', err)
        }
      })
    },

    // ── 中断流式输出 ───────────────────────────────────────
    abortStream() {
      this._abortStream?.()
      const last = this.messages.at(-1)
      if (last?.role === 'assistant' && last.loading) {
        last.loading = false
      }
      this.streaming    = false
      this._abortStream = null
    },

    // ── 工具方法 ───────────────────────────────────────────
    appendMessage(msg)      { this.messages.push(msg) },
    updateLastMessage(patch) {
      const last = this.messages.at(-1)
      if (last) Object.assign(last, patch)
    },
    updateConvTitle(threadId, title) {
      const conv = this.conversations.find((c) => c.thread_id === threadId)
      if (conv) conv.title = title
    }
  },

  persist: {
    key:     'chat-store',
    storage: localStorage,
    paths:   ['currentConvId']
  }
})
