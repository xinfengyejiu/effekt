import request from '@/utils/request'

export function getUserAiModels() {
  return request({ url: '/user/ai-models', method: 'get' })
}

export function getUserAiPreference() {
  return request({ url: '/user/ai-preference', method: 'get' })
}

export function saveUserAiPreference(data) {
  return request({ url: '/user/ai-preference/save', method: 'post', data: data || {} })
}

export function clearUserAiPreference() {
  return request({ url: '/user/ai-preference/clear', method: 'post', data: {} })
}

export function fetchUserAiModels(data) {
  return request({ url: '/user/ai-preference/fetch-models', method: 'post', data: data || {} })
}
