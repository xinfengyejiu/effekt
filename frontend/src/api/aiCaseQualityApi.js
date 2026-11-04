import request from '@/utils/request'

/** AI 用例改写率 / 废稿率汇总 */
export function getAiCaseQualitySummary (params) {
  return request({
    url: '/ai-case-quality/summary',
    method: 'get',
    params: params || {}
  })
}

/** 已改写用例列表 */
export function getAiCaseRewrittenList (params) {
  return request({
    url: '/ai-case-quality/rewritten-list',
    method: 'get',
    params: params || {}
  })
}

/** 失败根因归因汇总 */
export function getFailureAttributionSummary (params) {
  return request({
    url: '/failure-attribution/summary',
    method: 'get',
    params: params || {}
  })
}
