import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data) {
  return request({ url, method: 'post', data: data || {} })
}

export function createAssetGovernanceScan(data) {
  return post('/test-asset/governance/scan/create', data)
}

export function getAssetGovernanceScanList(params) {
  return get('/test-asset/governance/scan/list', params)
}

export function getAssetGovernanceScanDetail(params) {
  return get('/test-asset/governance/scan/detail', params)
}

export function executeAssetGovernanceScan(data) {
  return post('/test-asset/governance/scan/execute', data)
}

export function getAssetGovernanceIssueList(params) {
  return get('/test-asset/governance/issue/list', params)
}

export function updateAssetGovernanceIssue(data) {
  return post('/test-asset/governance/issue/update', data)
}

export function applyAssetGovernanceAction(data) {
  return post('/test-asset/governance/action/apply', data)
}
