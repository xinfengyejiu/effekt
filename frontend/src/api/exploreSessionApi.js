import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data) {
  return request({ url, method: 'post', data: data || {} })
}

export function createExploreSession(data) {
  return post('/explore/session/create', data)
}

export function getExploreSessionList(params) {
  return get('/explore/session/list', params)
}

export function getExploreSessionDetail(params) {
  return get('/explore/session/detail', params)
}

export function updateExploreSession(data) {
  return post('/explore/session/update', data)
}

export function startExploreSession(data) {
  return post('/explore/session/start', data)
}

export function endExploreSession(data) {
  return post('/explore/session/end', data)
}

export function archiveExploreSession(data) {
  return post('/explore/session/archive', data)
}

export function addExploreEntry(data) {
  return post('/explore/session/entry/add', data)
}

export function updateExploreEntry(data) {
  return post('/explore/session/entry/update', data)
}

export function deleteExploreEntry(data) {
  return post('/explore/session/entry/delete', data)
}

export function uploadExploreScreenshot(formData) {
  return request({
    url: '/explore/session/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function exploreToBug(data) {
  return post('/explore/session/to-bug', data)
}

export function exploreToCaseDraft(data) {
  return post('/explore/session/to-case-draft', data)
}
