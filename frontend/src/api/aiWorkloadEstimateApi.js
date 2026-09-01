import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data, config) {
  return request(Object.assign({ url, method: 'post', data: data || {} }, config || {}))
}

function download(url, params) {
  return request({ url, method: 'get', params: params || {}, responseType: 'blob', timeout: 120000 })
}

export function createWorkloadEstimate(data) { return post('/ai/workload-estimate/create', data) }
export function getWorkloadEstimateList(params) { return get('/ai/workload-estimate/list', params) }
export function getWorkloadEstimateDetail(params) { return get('/ai/workload-estimate/detail', params) }
export function exportWorkloadEstimateExcel(params) { return download('/ai/workload-estimate/export', params) }
export function executeWorkloadEstimate(data) { return post('/ai/workload-estimate/execute', data, { timeout: 360000 }) }
export function assignWorkloadEstimateOwner(data) { return post('/ai/workload-estimate/assign', data) }
export function deleteWorkloadEstimate(data) { return post('/ai/workload-estimate/delete', data) }
export function saveWorkloadEstimateActual(data) { return post('/ai/workload-estimate/actual/save', data) }
export function confirmWorkloadEstimate(data) { return post('/ai/workload-estimate/confirm', data) }
export function retryWorkloadEstimate(data) { return post('/ai/workload-estimate/retry', data, { timeout: 360000 }) }
