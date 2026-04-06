import request from './index.js'

/**
 * 获取所有文档列表
 * @returns {Promise<{ documents: string[] }>}
 */
export const getDocumentsAPI = () => request.get('/documents')

/**
 * 上传文件
 * @param {File} file
 * @param {(percent: number) => void} onProgress
 * @returns {Promise<{ status, message, filename, chunks_count, source }>}
 */
export const uploadDocumentAPI = (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  return request.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total) {
        onProgress?.(Math.round((e.loaded * 100) / e.total))
      }
    }
  })
}

/**
 * 删除文档
 * @param {string} filename
 * @returns {Promise<{ status, message }>}
 */
export const deleteDocumentAPI = (filename) =>
  request.delete(`/documents/${encodeURIComponent(filename)}`)

/**
 * 文档分析接口
 * @param {File} file - 上传的文档文件
 * @param {string} question - 用户问题（可选）
 * @param {string} threadId - 会话 ID
 */
export function analyzeDocumentAPI(file, question = '', threadId = '') {
  const formData = new FormData()
  formData.append('file', file)
  if (question) formData.append('question', question)
  if (threadId) formData.append('thread_id', threadId)

  return request.post('/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000 // 文档分析可能较慢，给 60s
  })
}