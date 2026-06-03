import request from '@/utils/request'

export function getKnowledgeDocumentList(params) {
  return request({ url: '/knowledge/document/list', method: 'get', params })
}

export function uploadKnowledgeDocument({ file, productId, projectId, createdBy, autoParse }) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('productId', productId)
  formData.append('projectId', projectId)
  if (createdBy != null && createdBy !== '') formData.append('createdBy', createdBy)
  if (autoParse != null) formData.append('autoParse', autoParse ? 1 : 0)
  return request({ url: '/knowledge/document/upload', method: 'post', data: formData })
}

export function parseKnowledgeDocument(data) {
  return request({ url: '/knowledge/document/parse', method: 'post', data })
}

export function deleteKnowledgeDocument(data) {
  return request({ url: '/knowledge/document/delete', method: 'post', data })
}

export function searchKnowledge(data) {
  return request({ url: '/knowledge/search', method: 'post', data })
}

export function chatKnowledge(data) {
  return request({ url: '/knowledge/chat', method: 'post', data })
}

export function getKnowledgeSessions(params) {
  return request({ url: '/knowledge/chat/session/list', method: 'get', params })
}

export function getKnowledgeMessages(params) {
  return request({ url: '/knowledge/chat/message/list', method: 'get', params })
}

export function deleteKnowledgeSession(data) {
  return request({ url: '/knowledge/chat/session/delete', method: 'post', data })
}

export function getKnowledgeModelSetting(params) {
  return request({ url: '/knowledge/model-setting/detail', method: 'get', params })
}

export function saveKnowledgeModelSetting(data) {
  return request({ url: '/knowledge/model-setting/save', method: 'post', data })
}

export function testKnowledgeModelSetting(data) {
  return request({ url: '/knowledge/model-setting/test', method: 'post', data })
}
