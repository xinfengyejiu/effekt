import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data) {
  return request({ url, method: 'post', data: data || {} })
}

export function getWeakNetworkAiTasks(params) {
  return get('/weak-network-ai/tasks', params)
}

export function createWeakNetworkAiTask(data) {
  return post('/weak-network-ai/tasks', data)
}

export function getWeakNetworkAiTaskDetail(params) {
  return get('/weak-network-ai/tasks/detail', params)
}

export function updateWeakNetworkAiTask(data) {
  return post('/weak-network-ai/tasks/update', data)
}

export function orchestrateWeakNetworkAiTask(data) {
  return post('/weak-network-ai/tasks/orchestrate', data)
}

export function confirmWeakNetworkAiTask(data) {
  return post('/weak-network-ai/tasks/confirm', data)
}

export function addWeakNetworkAiEvidence(data) {
  return post('/weak-network-ai/tasks/evidence', data)
}

export function uploadWeakNetworkAiEvidence(formData) {
  return request({
    url: '/weak-network-ai/tasks/evidence-upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function judgeWeakNetworkAiTask(data) {
  return post('/weak-network-ai/tasks/judge', data)
}

export function dismissWeakNetworkAiFindings(data) {
  return post('/weak-network-ai/findings/dismiss', data)
}

export function confirmWeakNetworkAiFindingsToBug(data) {
  return post('/weak-network-ai/findings/confirm-to-bug', data)
}
