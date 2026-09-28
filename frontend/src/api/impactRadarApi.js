import request from '@/utils/request'

export function parseImpactRadarUrl(data) {
  return request({ url: '/impact-radar/parse-url', method: 'post', data: data || {} })
}

export function runImpactRadar(data) {
  return request({ url: '/impact-radar/run', method: 'post', data: data || {}, timeout: 300000 })
}

export function getImpactRadarList(params) {
  return request({ url: '/impact-radar/run/list', method: 'get', params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {}) })
}

export function getImpactRadarDetail(params) {
  return request({ url: '/impact-radar/run/detail', method: 'get', params: params || {} })
}

export function recomputeImpactRadarLineage(data) {
  return request({ url: '/impact-radar/run/lineage', method: 'post', data: data || {}, timeout: 300000 })
}

export function traceImpactRadarCode(data) {
  return request({ url: '/impact-radar/trace', method: 'post', data: data || {}, timeout: 180000 })
}
