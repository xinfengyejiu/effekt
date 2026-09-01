import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data) {
  return request({ url, method: 'post', data: data || {} })
}

export function getAiReviewList(params) { return get('/ai/review/list', params) }
export function getAiReviewDetail(params) { return get('/ai/review/detail', params) }
export function createAiReview(data) { return post('/ai/review/create', data) }
export function executeAiReview(data) { return post('/ai/review/execute', data) }
export function confirmAiReview(data) { return post('/ai/review/confirm', data) }
export function updateAiReviewFinding(data) { return post('/ai/review/finding/update', data) }
export function importAiReviewCase(data) { return post('/ai/review/case/import', data) }
export function linkAiReviewCase(data) { return post('/ai/review/case/link', data) }
