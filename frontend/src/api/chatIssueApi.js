import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data) {
  return request({ url, method: 'post', data: data || {} })
}

export function importChatIssue(data) {
  return post('/chat-issue/import', data)
}

export function importChatIssueFile(formData) {
  return request({
    url: '/chat-issue/import-file',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function getChatIssueList(params) {
  return get('/chat-issue/list', params)
}

export function getChatIssueDetail(params) {
  return get('/chat-issue/detail', params)
}

export function updateChatIssueItem(data) {
  return post('/chat-issue/item/update', data)
}

export function deleteChatIssueItem(data) {
  return post('/chat-issue/item/delete', data)
}

export function analyzeChatIssue(data) {
  return post('/chat-issue/analyze', data)
}

export function dismissChatIssue(data) {
  return post('/chat-issue/dismiss', data)
}

export function confirmChatIssueToBug(data) {
  return post('/chat-issue/confirm-to-bug', data)
}

export function chatIssueToCase(data) {
  return post('/chat-issue/to-case', data)
}
