import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data) {
  return request({ url, method: 'post', data: data || {} })
}

export function getAiDataProbeConnections(params) {
  return get('/ai-data-probe/connections', params)
}

export function createAiDataProbeConnection(data) {
  return post('/ai-data-probe/connections', data)
}

export function updateAiDataProbeConnection(data) {
  return post('/ai-data-probe/connections/update', data)
}

export function deleteAiDataProbeConnection(data) {
  return post('/ai-data-probe/connections/delete', data)
}

export function testAiDataProbeConnection(data) {
  return post('/ai-data-probe/connections/test', data)
}

export function getAiDataProbeTables(params) {
  return get('/ai-data-probe/connections/tables', params)
}

export function getAiDataProbeTableColumns(params) {
  return get('/ai-data-probe/connections/table-columns', params)
}

export function importAiDataProbeConnection(data) {
  return post('/ai-data-probe/connections/import-from-project', data)
}

export function getAiDataProbeSessions(params) {
  return get('/ai-data-probe/sessions', params)
}

export function createAiDataProbeSession(data) {
  return post('/ai-data-probe/sessions', data)
}

export function getAiDataProbeSessionDetail(params) {
  return get('/ai-data-probe/session/detail', params)
}

export function renameAiDataProbeSession(data) {
  return post('/ai-data-probe/session/rename', data)
}

export function askAiDataProbe(data) {
  return post('/ai-data-probe/ask', data)
}

export function askAiDataProbeStream(data, onEvent, onError, onDone) {
  const accessToken = localStorage.getItem('accessToken') || ''
  const url = '/it/api/ai-data-probe/ask-stream'
  const headers = {
    'Content-Type': 'application/json',
    accessToken: accessToken
  }
  const controller = new AbortController()
  let aborted = false
  let buffer = ''

  const promise = fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(data || {}),
    signal: controller.signal
  }).then(response => {
    if (!response.ok) {
      throw new Error('HTTP ' + response.status + ': ' + response.statusText)
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    function read() {
      return reader.read().then(({ done, value }) => {
        if (done) {
          if (onDone) onDone()
          return
        }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (let i = 0; i < lines.length; i++) {
          const trimmed = (lines[i] || '').trim()
          if (!trimmed.startsWith('data: ')) continue
          try {
            const parsed = JSON.parse(trimmed.slice(6))
            if (onEvent) onEvent(parsed)
          } catch (e) {
            // ignore partial json
          }
        }
        return read()
      })
    }
    return read()
  }).catch(err => {
    if (aborted || (err && err.name === 'AbortError')) return
    if (onError) onError(err)
  })

  return {
    abort() {
      aborted = true
      controller.abort()
    },
    promise
  }
}

export function rerunAiDataProbeSql(data) {
  return post('/ai-data-probe/rerun-sql', data)
}
