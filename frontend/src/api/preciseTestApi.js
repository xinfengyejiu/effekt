import request from '@/utils/request'

export function getPreciseAnalysisList(params) {
  return request({ url: '/precise/analysis/list', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function createPreciseAnalysis(data) {
  return request({ url: '/precise/analysis/create', method: 'post', data })
}

export function getPreciseAnalysisDetail(id) {
  return request({ url: '/precise/analysis/' + id, method: 'get' })
}

export function parsePreciseDiff(id, data) {
  return request({ url: '/precise/analysis/' + id + '/parse-diff', method: 'post', data: data || {} })
}

export function createPreciseAiImpact(id, data) {
  return request({ url: '/precise/analysis/' + id + '/ai-impact', method: 'post', data: data || {} })
}

export function getPreciseRelationList(params) {
  return request({ url: '/precise/relations/list', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function createPreciseRelation(data) {
  return request({ url: '/precise/relations/create', method: 'post', data })
}

export function updatePreciseRelation(id, data) {
  return request({ url: '/precise/relations/' + id, method: 'put', data })
}

export function deletePreciseRelation(id) {
  return request({ url: '/precise/relations/' + id, method: 'delete' })
}

export function importPreciseRelations(data) {
  return request({ url: '/precise/relations/import', method: 'post', data })
}

export function generatePreciseRecommendations(id, data) {
  return request({ url: '/precise/analysis/' + id + '/recommend', method: 'post', data: data || {} })
}

export function getPreciseRecommendations(id, params) {
  return request({ url: '/precise/analysis/' + id + '/recommendations', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 100 }, params || {}) })
}

export function acceptPreciseRecommendations(data) {
  return request({ url: '/precise/recommendations/accept', method: 'post', data })
}

export function executePreciseAnalysis(id, data) {
  return request({ url: '/precise/analysis/' + id + '/execute', method: 'post', data: data || {} })
}

export function getPreciseExecutionList(params) {
  return request({ url: '/precise/executions/list', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function syncPreciseJenkins(data) {
  return request({ url: '/precise/executions/sync-jenkins', method: 'post', data: data || {} })
}

export function uploadPreciseCoverage(data) {
  return request({ url: '/precise/coverage/upload', method: 'post', data, headers: { 'Content-Type': 'multipart/form-data' } })
}

export function pullPreciseCoverageFromJenkins(data) {
  return request({ url: '/precise/coverage/pull-from-jenkins', method: 'post', data })
}

export function getPreciseCoverageList(params) {
  return request({ url: '/precise/coverage/list', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function getPreciseCoverageDetail(id) {
  return request({ url: '/precise/coverage/' + id, method: 'get' })
}

export function calculatePreciseIncremental(id, data) {
  return request({ url: '/precise/coverage/' + id + '/calculate-incremental', method: 'post', data: data || {} })
}

export function createPreciseAiRiskAnalysis(id, data) {
  return request({ url: '/precise/coverage/' + id + '/ai-risk-analysis', method: 'post', data: data || {} })
}

export function evaluatePreciseGate(data) {
  return request({ url: '/precise/gate/evaluate', method: 'post', data })
}

export function getPreciseGateResult(id) {
  return request({ url: '/precise/gate/result/' + id, method: 'get' })
}
