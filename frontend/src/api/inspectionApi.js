import request from '@/utils/request'

// ═══════════════════════════════════════════════
// 巡检组
// ═══════════════════════════════════════════════

export function getInspectionGroupList(params) {
  return request({
    url: '/inspection/group/list',
    method: 'get',
    params: Object.assign({ page_no: 1, page_size: 100 }, params || {})
  })
}

export function getInspectionGroupDetail(id) {
  return request({ url: '/inspection/group/detail', method: 'get', params: { id } })
}

export function createInspectionGroup(data) {
  return request({ url: '/inspection/group/create', method: 'post', data })
}

export function updateInspectionGroup(data) {
  return request({ url: '/inspection/group/update', method: 'post', data })
}

export function deleteInspectionGroup(id) {
  return request({ url: '/inspection/group/delete', method: 'post', data: { id } })
}

export function toggleInspectionGroup(id) {
  return request({ url: '/inspection/group/toggle', method: 'post', data: { id } })
}

export function runInspectionGroup(id) {
  return request({ url: '/inspection/group/run', method: 'post', data: { id } })
}

// ═══════════════════════════════════════════════
// 巡检任务
// ═══════════════════════════════════════════════

export function getInspectionTaskList(params) {
  return request({
    url: '/inspection/task/list',
    method: 'get',
    params: Object.assign({ page_no: 1, page_size: 20 }, params || {})
  })
}

export function getInspectionTaskDetail(id) {
  return request({ url: '/inspection/task/detail', method: 'get', params: { id } })
}

export function createInspectionTask(data) {
  return request({ url: '/inspection/task/create', method: 'post', data })
}

export function updateInspectionTask(data) {
  return request({ url: '/inspection/task/update', method: 'post', data })
}

export function deleteInspectionTask(id) {
  return request({ url: '/inspection/task/delete', method: 'post', data: { id } })
}

export function toggleInspectionTask(id) {
  return request({ url: '/inspection/task/toggle', method: 'post', data: { id } })
}

export function executeInspectionTask(id) {
  return request({ url: '/inspection/task/execute', method: 'post', data: { id } })
}

// ═══════════════════════════════════════════════
// 巡检项
// ═══════════════════════════════════════════════

export function getInspectionItemList(params) {
  return request({
    url: '/inspection/item/list',
    method: 'get',
    params: Object.assign({ page_no: 1, page_size: 100 }, params || {})
  })
}

export function createInspectionItem(data) {
  return request({ url: '/inspection/item/create', method: 'post', data })
}

export function updateInspectionItem(data) {
  return request({ url: '/inspection/item/update', method: 'post', data })
}

export function deleteInspectionItem(id) {
  return request({ url: '/inspection/item/delete', method: 'post', data: { id } })
}

export function batchCreateInspectionItems(data) {
  return request({ url: '/inspection/item/batch-create', method: 'post', data })
}

export function testInspectionItem(data) {
  return request({ url: '/inspection/item/test', method: 'post', data, timeout: 60000 })
}

// ═══════════════════════════════════════════════
// 数据库连接配置
// ═══════════════════════════════════════════════

export function getInspectionDbConfigList(params) {
  return request({
    url: '/inspection/db-config/list',
    method: 'get',
    params: Object.assign({ page_no: 1, page_size: 100 }, params || {})
  })
}

export function createInspectionDbConfig(data) {
  return request({ url: '/inspection/db-config/create', method: 'post', data })
}

export function updateInspectionDbConfig(data) {
  return request({ url: '/inspection/db-config/update', method: 'post', data })
}

export function deleteInspectionDbConfig(id) {
  return request({ url: '/inspection/db-config/delete', method: 'post', data: { id } })
}

export function testInspectionDbConnection(data) {
  return request({ url: '/inspection/db-config/test', method: 'post', data, timeout: 15000 })
}

// ═══════════════════════════════════════════════
// 执行记录
// ═══════════════════════════════════════════════

export function getInspectionExecutionList(params) {
  return request({
    url: '/inspection/execution/list',
    method: 'get',
    params: Object.assign({ page_no: 1, page_size: 20 }, params || {})
  })
}

export function getInspectionExecutionDetail(id) {
  return request({ url: '/inspection/execution/detail', method: 'get', params: { id } })
}

// ═══════════════════════════════════════════════
// 统计报表
// ═══════════════════════════════════════════════

export function getInspectionDashboard(params) {
  return request({ url: '/inspection/report/dashboard', method: 'get', params: params || {} })
}

export function getInspectionTrend(params) {
  return request({ url: '/inspection/report/trend', method: 'get', params: params || {} })
}
