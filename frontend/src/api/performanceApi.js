import request from '@/utils/request'

export function getPerformanceScenarioList(params) {
  return request({ url: '/performance/scenarios', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function createPerformanceScenario(data) {
  return request({ url: '/performance/scenarios', method: 'post', data })
}

export function updatePerformanceScenario(id, data) {
  return request({ url: '/performance/scenarios/' + id, method: 'put', data })
}

export function deletePerformanceScenario(id) {
  return request({ url: '/performance/scenarios/' + id, method: 'delete' })
}

export function getPerformanceScriptList(params) {
  return request({ url: '/performance/scripts', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function uploadPerformanceScript(data) {
  return request({ url: '/performance/scripts/upload', method: 'post', data, headers: data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined })
}

export function generatePerformancePlan(data) {
  return request({ url: '/performance/scripts/generate-plan', method: 'post', data })
}

export function generatePerformanceScript(data) {
  return request({ url: '/performance/scripts/generate-script', method: 'post', data })
}

export function getPerformanceExecutionConfigList(params) {
  return request({ url: '/performance/execution-configs', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function createPerformanceExecutionConfig(data) {
  return request({ url: '/performance/execution-configs', method: 'post', data })
}

export function updatePerformanceExecutionConfig(id, data) {
  return request({ url: '/performance/execution-configs/' + id, method: 'put', data })
}

export function createPerformanceRun(data) {
  return request({ url: '/performance/runs', method: 'post', data })
}

export function getPerformanceRunList(params) {
  return request({ url: '/performance/runs', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function stopPerformanceRun(id) {
  return request({ url: '/performance/runs/' + id + '/stop', method: 'post', data: {} })
}

export function retryPerformanceRun(id) {
  return request({ url: '/performance/runs/' + id + '/retry', method: 'post', data: {} })
}

export function getPerformanceReport(runId) {
  return request({ url: '/performance/reports/' + runId, method: 'get' })
}

export function getPerformanceNativeReport(runId) {
  return request({ url: '/performance/reports/' + runId + '/native', method: 'get' })
}

export function getPerformanceReportMetrics(runId, params) {
  return request({ url: '/performance/reports/' + runId + '/metrics', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function getPerformanceGateResults(runId, params) {
  return request({ url: '/performance/reports/' + runId + '/gate-results', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function createPerformanceAiAnalysis(runId, data) {
  return request({ url: '/performance/reports/' + runId + '/ai-analysis', method: 'post', data: data || {} })
}

export function getPerformanceBaselineList(params) {
  return request({ url: '/performance/baselines', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function createPerformanceBaselineFromRun(data) {
  return request({ url: '/performance/baselines/from-run', method: 'post', data })
}

export function activatePerformanceBaseline(id) {
  return request({ url: '/performance/baselines/' + id + '/active', method: 'put', data: {} })
}

export function getPerformanceMachineList(params) {
  return request({ url: '/performance/test-machines', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function getAvailablePerformanceMachineList(params) {
  return request({ url: '/performance/test-machines/available', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 200 }, params || {}) })
}

export function createPerformanceMachine(data) {
  return request({ url: '/performance/test-machines', method: 'post', data })
}

export function updatePerformanceMachine(id, data) {
  return request({ url: '/performance/test-machines/' + id, method: 'put', data })
}

export function deletePerformanceMachine(id) {
  return request({ url: '/performance/test-machines/' + id, method: 'delete' })
}
