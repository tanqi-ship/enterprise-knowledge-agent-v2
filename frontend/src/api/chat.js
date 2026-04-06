import request from './index.js'

// ── 会话管理 ──────────────────────────────────────────────

export const getConversationsAPI = () => request.get('/sessions')
export const createConversationAPI = () => request.post('/sessions')
export const deleteConversationAPI = (threadId) => request.delete(`/sessions/${threadId}`)
export const renameConversationAPI = (threadId, title) =>
  request.put(`/sessions/${threadId}/title`, { title })
export const getMessagesAPI = (threadId) => request.get(`/sessions/${threadId}`)

// ── 流式发送消息 ──────────────────────────────────────────

/**
 * @param {string}   threadId
 * @param {string}   content
 * @param {object}   callbacks
 * @param {(text: string) => void}        callbacks.onText       - 收到文字 token
 * @param {(name: string) => void}        callbacks.onTool       - 工具调用开始
 * @param {(content: string) => void}     callbacks.onToolResult - 工具执行结果
 * @param {() => void}                    callbacks.onDone       - 流结束
 * @param {(err: Error) => void}          callbacks.onError      - 出错
 * @returns {() => void} abort 函数
 */
export const sendMessageStream = (threadId, content, callbacks = {}) => {
  const { onText, onTool, onToolResult, onDone, onError } = callbacks

  // ── 取 token（与 request 拦截器保持一致）──
  const token = localStorage.getItem('access_token')

//  const baseURL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
  const baseURL = (request.defaults.baseURL ?? '').replace(/\/$/, '')
  const ctrl = new AbortController()

  fetch(`${baseURL}/sessions/${threadId}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ message: content }),
    signal: ctrl.signal
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader  = res.body.getReader()
      const decoder = new TextDecoder()
      let   buffer  = ''   // 处理跨 chunk 的不完整行

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 按换行切割，保留最后一段不完整的行
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''  // 最后一段留着等下次拼接

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data:')) continue

          const raw = trimmed.slice(5).trim()
          if (!raw) continue

          let parsed
          try {
            parsed = JSON.parse(raw)
          } catch {
            console.warn('[SSE] 无法解析:', raw)
            continue
          }

          switch (parsed.type) {
            case 'text':
              onText?.(parsed.content ?? '')
              break
            case 'tool':
              onTool?.(parsed.name ?? '')
              break
            case 'tool_result':
              onToolResult?.(parsed.content ?? '')
              break
            case 'done':
              onDone?.()
              return   // 正常结束，退出循环
            default:
              console.warn('[SSE] 未知 type:', parsed.type)
          }
        }
      }

      // 流关闭但没收到 done（后端异常关闭也视为结束）
      onDone?.()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        onError?.(err)
        onDone?.()   // ✅ 出错时也触发 done，解除前端禁用
      }
    })

  return () => ctrl.abort()
}
