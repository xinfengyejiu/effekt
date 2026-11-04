import request from '@/utils/request'

/** 文档列表 */
export function getDocumentList(params) {
  return request({
    url: '/document/list',
    method: 'get',
    params
  })
}

/** 文档详情 */
export function getDocumentDetail(params) {
  return request({
    url: '/document/detail',
    method: 'get',
    params
  })
}

/** 上传 PDF（multipart，单文件一次请求） */
export function uploadDocumentPdf({ file, productId, projectId, createdBy }) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('productId', productId)
  formData.append('projectId', projectId)
  if (createdBy != null && createdBy !== '') {
    formData.append('createdBy', createdBy)
  }
  return request({
    url: '/document/upload',
    method: 'post',
    data: formData,
    // PDF/Excel 可能较大，单独放大上传超时
    timeout: 180000
  })
}

/** 创建文档 */
export function createDocument(data) {
  return request({
    url: '/document/create',
    method: 'post',
    data
  })
}

/** 更新文档 */
export function updateDocument(data) {
  return request({
    url: '/document/update',
    method: 'post',
    data
  })
}

/** 删除文档 */
export function deleteDocument(data) {
  return request({
    url: '/document/delete',
    method: 'post',
    data
  })
}

/** 刷新飞书文档 */
export function refreshDocument(data) {
  return request({
    url: '/document/refresh',
    method: 'post',
    data
  })
}

export function getDocumentCaseGenerationStatus(params) {
  return request({
    url: '/document/generation-status',
    method: 'get',
    params
  })
}

/** 生成测试用例（SSE流式） */
export function cancelDocumentCaseGeneration(data) {
  return request({
    url: '/document/cancel-generate-cases',
    method: 'post',
    data
  })
}

export function generateDocumentCasesStreaming(data, onEvent, onError, onDone) {
  const accessToken = localStorage.getItem('accessToken') || ''
  const url = '/it/api/document/generate-cases-streaming'
  const headers = {
    'Content-Type': 'application/json',
    'accessToken': accessToken
  }
  const controller = new AbortController()
  let aborted = false

  let buffer = ''
  const promise = fetch(url, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(data),
    signal: controller.signal
  }).then(response => {

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    function read() {
      return reader.read().then(({ done, value }) => {
        if (done) {
          if (onDone) onDone()
          return
        }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(trimmed.slice(6))
              if (onEvent) onEvent(parsed)
            } catch (e) {
              // ignore parse errors
            }
          }
        }
        return read()
      })
    }
    return read()
  }).catch(err => {
    if (aborted || err.name === 'AbortError') {
      return
    }
    if (onError) onError(err)
  })

  return {
    abort() {
      aborted = true
      controller.abort()
    },
    promise
  }
}


/** 生成测试用例（预览） */
export function generateDocumentCases(data) {
  return request({
    url: '/document/generate-cases',
    method: 'post',
    data,
    // AI 用例生成链路较长，PDF/长文档会切分成多 chunk 多次调用大模型；
    // 单独放大该接口的 axios 超时，避免浏览器先于服务端超时。
    timeout: 600000
  })
}

/** 同步项目最新成功的代码转PRD为文档源 */
export function syncDocumentFromCodePrd(data) {
  return request({
    url: '/document/sync-code-prd',
    method: 'post',
    data
  })
}

/** 生成需求大纲（测点清单） */
export function generateDocumentOutline(data) {
  return request({
    url: '/document/generate-outline',
    method: 'post',
    data,
    timeout: 180000
  })
}

/** 生成计划详情 */
export function getGenerationPlanDetail(params) {
  return request({
    url: '/document/generation-plan/detail',
    method: 'get',
    params
  })
}

/** 按项目取最近一条生成计划（刷新后恢复向导） */
export function getLatestGenerationPlan(params) {
  return request({
    url: '/document/generation-plan/latest',
    method: 'get',
    params
  })
}

/** 更新生成计划（测点勾选等） */
export function updateGenerationPlan(data) {
  return request({
    url: '/document/generation-plan/update',
    method: 'post',
    data
  })
}

/** 刷新覆盖报告 */
export function refreshGenerationPlanCoverage(data) {
  return request({
    url: '/document/generation-plan/coverage',
    method: 'post',
    data
  })
}

/** 确认导入预览候选用例 */
export function importGenerationPlanCases(data) {
  return request({
    url: '/document/generation-plan/import',
    method: 'post',
    data,
    timeout: 120000
  })
}

/** 模块匹配 */
export function matchDocumentModules(data) {
  return request({
    url: '/document/match-modules',
    method: 'post',
    data
  })
}

/** 导入测试用例 */
export function importDocumentCases(data) {
  return request({
    url: '/document/import-cases',
    method: 'post',
    data
  })
}

/** 批量创建模块 */
export function batchCreateDocumentModules(data) {
  return request({
    url: '/document/batch-create-modules',
    method: 'post',
    data
  })
}
