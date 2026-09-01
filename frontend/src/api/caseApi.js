import request from '@/utils/request'

export function getModuleTree(params) {
  return request({
    url: '/module/tree',
    method: 'get',
    params
  })
}

export function createModule(data) {
  return request({
    url: '/module/create',
    method: 'post',
    data
  })
}

export function updateModule(data) {
  return request({
    url: '/module/update',
    method: 'post',
    data
  })
}

export function deleteModule(data) {
  return request({
    url: '/module/delete',
    method: 'post',
    data
  })
}

export function getCaseList(projectId, params) {
  const query = Object.assign({}, params || {})
  if (projectId !== undefined && projectId !== null && projectId !== '') {
    query.projectId = projectId
  }
  return request({
    url: '/case/list',
    method: 'get',
    params: query
  })
}

export function getCaseDetail(projectId, caseId) {
  return request({
    url: '/case/detail',
    method: 'get',
    params: {
      projectId,
      caseId
    }
  })
}

export function createCase(projectId, data) {
  return request({
    url: '/case/create',
    method: 'post',
    data: Object.assign({ projectId }, data)
  })
}

export function updateCase(projectId, caseId, data) {
  return request({
    url: '/case/update',
    method: 'post',
    data: Object.assign({ projectId, caseId }, data)
  })
}

export function deleteCase(projectId, caseId) {
  return request({
    url: '/case/delete',
    method: 'post',
    data: {
      projectId,
      caseId
    }
  })
}

/** 复制用例 */
export function copyCase(projectId, caseId) {
  return request({
    url: '/case/copy',
    method: 'post',
    data: {
      projectId,
      caseId
    }
  })
}

/** 恢复状态为 0 的用例为正常（1），POST body: { caseIds: number[] } */
export function restoreCases(caseIds) {
  const raw = Array.isArray(caseIds) ? caseIds : [caseIds]
  const caseIdsNorm = raw
    .map(id => Number(id))
    .filter(id => Number.isFinite(id) && id > 0)
  return request({
    url: '/case/restore',
    method: 'post',
    data: { caseIds: caseIdsNorm }
  })
}

/**
 * 根据手工用例生成 UI / 接口自动化脚本（字段均为驼峰）。
 * 典型 body：projectId, caseId, automationType, prompt, caseKey, moduleName, productName,
 * projectName, steps, expectedResults
 */
export function generateCaseAutomation(data) {
  return request({
    url: '/case/generate-automation',
    method: 'post',
    data
  })
}

export function createCaseSnapshot(projectId, caseId) {
  return request({
    url: '/case/snapshot/create',
    method: 'post',
    data: {
      project_id: projectId,
      case_id: caseId
    }
  })
}

export function getCaseSnapshotList(projectId, params) {
  return request({
    url: '/case/snapshot/list',
    method: 'get',
    params: Object.assign({ project_id: projectId, pageNo: 1, pageSize: 10 }, params || {})
  })
}

export function submitCaseReview(projectId, caseId, data) {
  return request({
    url: '/case/review/create',
    method: 'post',
    data: Object.assign({ project_id: projectId, case_id: caseId }, data)
  })
}

export function updateCaseReview(data) {
  return request({
    url: '/case/review/update',
    method: 'post',
    data
  })
}

export function getCaseReviewList(projectId, params) {
  return request({
    url: '/case/review/list',
    method: 'get',
    params: Object.assign({ project_id: projectId, pageNo: 1, pageSize: 10 }, params || {})
  })
}

// 用例导入
export function downloadCaseImportTemplate() {
  return request({
    url: '/import/template',
    method: 'get',
    responseType: 'blob'
  })
}

export function exportCaseExcel(productId, projectId, onDownloadProgress) {
  return request({
    url: '/case/export',
    method: 'get',
    params: { productId, projectId },
    responseType: 'blob',
    timeout: 180000,
    onDownloadProgress
  })
}

export function importCaseExcel(productId, projectId, file) {
  if (file === undefined) {
    file = projectId
    projectId = productId
    productId = ''
  }
  const formData = new FormData()
  // 后端从 request.form 读取产品与项目，保留旧调用兼容。
  if (productId) {
    formData.append('productId', productId)
  }
  formData.append('projectId', projectId)
  formData.append('file', file)
  return request({
    url: '/case/import',
    method: 'post',
    data: formData
  })
}
