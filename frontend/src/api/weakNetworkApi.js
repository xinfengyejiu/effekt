import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data) {
  return request({ url, method: 'post', data: data || {} })
}

export function getWeakNetworkProfiles(params) {
  return get('/weak-network/profiles', params)
}

export function createWeakNetworkProfile(data) {
  return post('/weak-network/profiles', data)
}

export function updateWeakNetworkProfile(data) {
  return post('/weak-network/profiles/update', data)
}

export function deleteWeakNetworkProfile(data) {
  return post('/weak-network/profiles/delete', data)
}

export function createWeakNetworkSession(data) {
  return post('/weak-network/sessions', data)
}

export function getWeakNetworkSessions(params) {
  return get('/weak-network/sessions', params)
}

export function downloadWeakNetworkSession(sessionId) {
  return request({
    url: '/weak-network/sessions/' + sessionId + '/download',
    method: 'get',
    responseType: 'blob',
    timeout: 120000
  })
}
