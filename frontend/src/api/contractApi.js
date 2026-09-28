import request from '@/utils/request'

export function getContractSuiteList (params) {
  return request({
    url: '/contract/suite/list',
    method: 'get',
    params: Object.assign({ page_no: 1, page_size: 20 }, params || {})
  })
}

export function getContractSuiteDetail (id) {
  return request({ url: '/contract/suite/detail', method: 'get', params: { id } })
}

export function createContractSuite (data) {
  return request({ url: '/contract/suite/create', method: 'post', data })
}

export function updateContractSuite (data) {
  return request({ url: '/contract/suite/update', method: 'post', data })
}

export function deleteContractSuite (id) {
  return request({ url: '/contract/suite/delete', method: 'post', data: { id } })
}

export function toggleContractSuite (id) {
  return request({ url: '/contract/suite/toggle', method: 'post', data: { id } })
}

export function previewContractSource (data) {
  return request({ url: '/contract/source/preview', method: 'post', data })
}

export function runContractSuite (id) {
  return request({ url: '/contract/suite/run', method: 'post', data: { id } })
}

export function getContractRunList (params) {
  return request({
    url: '/contract/run/list',
    method: 'get',
    params: Object.assign({ page_no: 1, page_size: 20 }, params || {})
  })
}

export function getContractRunDetail (id) {
  return request({ url: '/contract/run/detail', method: 'get', params: { id } })
}

export function designContractInterface (data) {
  return request({
    url: '/contract/ai/design',
    method: 'post',
    data: data || {},
    timeout: 180000
  })
}

export function analyzeContractRunItem (data) {
  return request({ url: '/contract/ai/analyze', method: 'post', data: data || {} })
}
