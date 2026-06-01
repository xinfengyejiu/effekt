import request from '@/utils/request'

function get(url, params) {
  return request({ url, method: 'get', params: params || {} })
}

function post(url, data) {
  return request({ url, method: 'post', data: data || {} })
}

export function getAiAgentList(params) { return get('/ai/agent/list', params) }
export function createAiAgent(data) { return post('/ai/agent/create', data) }
export function updateAiAgent(data) { return post('/ai/agent/update', data) }
export function deleteAiAgent(data) { return post('/ai/agent/delete', data) }
export function executeAiAgent(data) { return post('/ai/agent/execute', data) }
export function getAiAgentExecutionList(params) { return get('/ai/agent/execution/list', params) }
export function getAiAgentExecutionDetail(params) { return get('/ai/agent/execution/detail', params) }

export function getAiToolList(params) { return get('/ai/tool/list', params) }
export function createAiTool(data) { return post('/ai/tool/create', data) }
export function updateAiTool(data) { return post('/ai/tool/update', data) }
export function deleteAiTool(data) { return post('/ai/tool/delete', data) }
export function executeAiTool(data) { return post('/ai/tool/execute', data) }
export function getAiToolExecutionList(params) { return get('/ai/tool/execution/list', params) }
export function getAiToolExecutionDetail(params) { return get('/ai/tool/execution/detail', params) }

export function getAiMcpList(params) { return get('/ai/mcp/list', params) }
export function createAiMcp(data) { return post('/ai/mcp/create', data) }
export function updateAiMcp(data) { return post('/ai/mcp/update', data) }
export function deleteAiMcp(data) { return post('/ai/mcp/delete', data) }
export function callAiMcp(data) { return post('/ai/mcp/call', data) }
export function getAiMcpCallLogList(params) { return get('/ai/mcp/call/log/list', params) }
export function getAiMcpCallLogDetail(params) { return get('/ai/mcp/call/log/detail', params) }

export function getAiFlowList(params) { return get('/ai/flow/list', params) }
export function createAiFlow(data) { return post('/ai/flow/create', data) }
export function updateAiFlow(data) { return post('/ai/flow/update', data) }
export function deleteAiFlow(data) { return post('/ai/flow/delete', data) }
export function executeAiFlow(data) { return post('/ai/flow/execute', data) }
export function getAiFlowExecutionList(params) { return get('/ai/flow/execution/list', params) }
export function getAiFlowExecutionDetail(params) { return get('/ai/flow/execution/detail', params) }

export function getAiTaskList(params) { return get('/ai/task/list', params) }
export function getAiTaskDetail(params) { return get('/ai/task/detail', params) }
export function createAiTask(data) { return post('/ai/task/create', data) }
export function executeAiTask(data) { return post('/ai/task/execute', data) }
export function cancelAiTask(data) { return post('/ai/task/cancel', data) }

export function getAiReportList(params) { return get('/ai/report/list', params) }
export function getAiReportDetail(params) { return get('/ai/report/detail', params) }
export function createAiReport(data) { return post('/ai/report/create', data) }
