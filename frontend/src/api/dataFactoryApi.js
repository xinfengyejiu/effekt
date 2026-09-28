import request from '@/utils/request'

export function getBuilderList(projectId, params) {
  return request({
    url: '/data/builder/list',
    method: 'get',
    params: Object.assign({ projectId: projectId, pageNo: 1, pageSize: 10 }, params || {})
  })
}

export function getBuilderDetail(projectId, builderId) {
  return request({
    url: '/data/builder/detail',
    method: 'get',
    params: {
      projectId: projectId,
      builderId: builderId,
      id: builderId
    }
  })
}

export function createBuilder(projectId, data) {
  return request({
    url: '/data/builder/create',
    method: 'post',
    data: Object.assign({ projectId: projectId }, data)
  })
}

export function updateBuilder(projectId, builderId, data) {
  return request({
    url: '/data/builder/update',
    method: 'post',
    data: Object.assign({ projectId: projectId, builderId: builderId, id: builderId }, data)
  })
}

export function deleteBuilder(projectId, builderId) {
  return request({
    url: '/data/builder/delete',
    method: 'post',
    data: {
      projectId: projectId,
      builderId: builderId,
      id: builderId
    }
  })
}

export function executeBuilder(projectId, builderId, data) {
  return request({
    url: '/data/builder/execute',
    method: 'post',
    data: Object.assign({ projectId: projectId, builderId: builderId }, data || {})
  })
}

export function getDataTaskStatus(projectId, taskId) {
  return request({
    url: '/data/task/status',
    method: 'get',
    params: {
      projectId: projectId,
      taskId: taskId
    }
  })
}

export function getDataTaskList(projectId, params) {
  return request({
    url: '/data/task/list',
    method: 'get',
    params: Object.assign({ projectId: projectId, pageNo: 1, pageSize: 20 }, params || {})
  })
}

export function aiGenerateBuilder(data) {
  return request({
    url: '/data/builder/ai-generate',
    method: 'post',
    data: data || {},
    timeout: 180000
  })
}

export function aiRefineBuilder(data) {
  return request({
    url: '/data/builder/ai-refine',
    method: 'post',
    data: data || {},
    timeout: 180000
  })
}

export function saveAsScene(data) {
  return request({
    url: '/data/builder/save-as-scene',
    method: 'post',
    data: data || {}
  })
}

export function sqlDraftBuilder(data) {
  return request({
    url: '/data/builder/sql-draft',
    method: 'post',
    data: data || {}
  })
}

export function ocrGenerateBuilder(formData) {
  return request({
    url: '/data/builder/ocr-generate',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
}
