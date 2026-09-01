import request from '@/utils/request'

export function getMobileEnvironmentCheck() {
  return request({ url: '/mobile_automation/environment/check', method: 'get' })
}

export function startMobileAppium() {
  return request({ url: '/mobile_automation/environment/start_appium', method: 'post', timeout: 60000 })
}

export function scanMobileDevices() {
  return request({ url: '/mobile_automation/device/scan', method: 'get' })
}

export function getMobileDeviceList(params) {
  return request({ url: '/mobile_automation/device/list', method: 'get', params: Object.assign({ page_no: 1, page_size: 100 }, params || {}) })
}

export function updateMobileDevice(data) {
  return request({ url: '/mobile_automation/device/update', method: 'post', data })
}

export function getMobileAppList(params) {
  return request({ url: '/mobile_automation/app/list', method: 'get', params: Object.assign({ page_no: 1, page_size: 100 }, params || {}) })
}

export function createMobileApp(data) {
  return request({ url: '/mobile_automation/app/create', method: 'post', data })
}

export function updateMobileApp(data) {
  return request({ url: '/mobile_automation/app/update', method: 'post', data })
}

export function deleteMobileApp(id) {
  return request({ url: '/mobile_automation/app/delete', method: 'post', data: { id } })
}

export function getMobileExecutionConfigList(params) {
  return request({ url: '/mobile_automation/config/list', method: 'get', params: Object.assign({ page_no: 1, page_size: 20 }, params || {}) })
}

export function getMobileExecutionConfig(id) {
  return request({ url: '/mobile_automation/config/detail', method: 'get', params: { id } })
}

export function saveMobileExecutionConfig(data) {
  return request({ url: '/mobile_automation/config/save', method: 'post', data })
}

export function deleteMobileExecutionConfig(id) {
  return request({ url: '/mobile_automation/config/delete', method: 'post', data: { id } })
}

export function runMobileExecutionConfig(id) {
  return request({ url: '/mobile_automation/config/run', method: 'post', data: { id } })
}

export function createMobileExecution(data) {
  return request({ url: '/mobile_automation/execution/create', method: 'post', data })
}

export function retryMobileExecution(executionId) {
  return request({ url: '/mobile_automation/execution/retry', method: 'post', data: { execution_id: executionId } })
}

export function cancelMobileExecution(executionId) {
  return request({ url: '/mobile_automation/execution/cancel', method: 'post', data: { execution_id: executionId } })
}

export function getMobileExecutionList(params) {
  return request({ url: '/mobile_automation/execution/list', method: 'get', params: Object.assign({ page_no: 1, page_size: 20 }, params || {}) })
}

export function getMobileExecutionDetail(executionId) {
  return request({ url: '/mobile_automation/execution/detail', method: 'get', params: { execution_id: executionId } })
}

export function getMobileExecutionProgress(executionId) {
  return request({ url: '/mobile_automation/execution/progress', method: 'get', params: { execution_id: executionId } })
}

export function getMobileExecutionCaseList(executionId) {
  return request({ url: '/mobile_automation/execution/case/list', method: 'get', params: { execution_id: executionId } })
}

export function getMobileExecutionStepList(params) {
  return request({ url: '/mobile_automation/execution/step/list', method: 'get', params })
}

export function getMobileArtifactList(params) {
  return request({ url: '/mobile_automation/artifact/list', method: 'get', params })
}

export function captureMobilePageSnapshot(data) {
  return request({ url: '/mobile_automation/page/snapshot', method: 'post', data })
}

export function previewMobileArtifact(artifactId) {
  return request({ url: '/mobile_automation/artifact/preview', method: 'get', params: { artifact_id: artifactId }, responseType: 'blob', timeout: 120000 })
}

export function downloadMobileArtifact(artifactId) {
  return request({ url: '/mobile_automation/artifact/download', method: 'get', params: { artifact_id: artifactId }, responseType: 'blob', timeout: 120000 })
}

// ── AI 相关 ─

export function aiVerifyMobileCase(data) {
  return request({ url: '/mobile_automation/ai/verify', method: 'post', data, timeout: 60000 })
}

export function aiGenerateMobileScripts(data) {
  return request({ url: '/mobile_automation/ai/generate-scripts', method: 'post', data, timeout: 120000 })
}

export function aiGenerateAndDebugMobileScripts(data) {
  return request({ url: '/mobile_automation/ai/generate-and-debug-scripts', method: 'post', data, timeout: 600000 })
}
