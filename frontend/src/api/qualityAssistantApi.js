import request from '@/utils/request'

export function getQualityAssistantExamples () {
  return request({
    url: '/quality-assistant/examples',
    method: 'get'
  })
}

export function qualityAssistantChat (data) {
  return request({
    url: '/quality-assistant/chat',
    method: 'post',
    data: data || {},
    timeout: 120000
  })
}

export function getQualityAssistantSession (sessionId) {
  return request({
    url: '/quality-assistant/session/detail',
    method: 'get',
    params: { session_id: sessionId }
  })
}

export function getLatestQualityAssistantSession () {
  return request({
    url: '/quality-assistant/session/latest',
    method: 'get'
  })
}

export function clearQualityAssistantSession (sessionId) {
  return request({
    url: '/quality-assistant/session/clear',
    method: 'post',
    data: { session_id: sessionId }
  })
}

export function executeQualityAssistantAction (data) {
  return request({
    url: '/quality-assistant/action/execute',
    method: 'post',
    data: data || {},
    timeout: 180000
  })
}
