import request from '@/utils/request'

function download(url, params) {
  return request({ url, method: 'get', params: params || {}, responseType: 'blob', timeout: 120000 })
}

export function getProjectList(params) {
  return request({
    url: '/project/list',
    method: 'get',
    params: Object.assign({ pageNo: 1, pageSize: 10 }, params || {})
  })
}

export function getProjectDetail(projectId) {
  return request({
    url: '/project/detail',
    method: 'get',
    params: {
      id: projectId
    }
  })
}

export function createProject(data) {
  return request({
    url: '/project/create',
    method: 'post',
    data
  })
}

export function updateProject(data) {
  return request({
    url: '/project/update',
    method: 'post',
    data
  })
}

export function deleteProject(data) {
  return request({
    url: '/project/delete',
    method: 'post',
    data
  })
}

export function getProjectMembers(projectId, params) {
  return request({
    url: '/project/member/list',
    method: 'get',
    params: Object.assign({ project_id: projectId, pageNo: 1, pageSize: 10 }, params || {})
  })
}

export function createProjectMember(data) {
  return request({
    url: '/project/member/create',
    method: 'post',
    data
  })
}

export function getProjectEnvironments(projectId, params) {
  return request({
    url: '/environment/list',
    method: 'get',
    params: Object.assign({ project_id: projectId, pageNo: 1, pageSize: 10 }, params || {})
  })
}

export function createEnvironment(data) {
  return request({
    url: '/environment/create',
    method: 'post',
    data
  })
}

export function updateEnvironment(data) {
  return request({
    url: '/environment/update',
    method: 'post',
    data
  })
}

export function deleteEnvironment(data) {
  return request({
    url: '/environment/delete',
    method: 'post',
    data
  })
}

/** 项目 Webhook 配置 */
export function getProjectHookList(params) {
  return request({
    url: '/project/hook/list',
    method: 'get',
    params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {})
  })
}

export function getProjectHookDetail(hookId) {
  return request({
    url: '/project/hook/detail',
    method: 'get',
    params: { hookId }
  })
}

export function createProjectHook(data) {
  return request({
    url: '/project/hook/create',
    method: 'post',
    data: data || {}
  })
}

export function updateProjectHook(data) {
  return request({
    url: '/project/hook/update',
    method: 'post',
    data: data || {}
  })
}

export function deleteProjectHook(data) {
  return request({
    url: '/project/hook/delete',
    method: 'post',
    data: data || {}
  })
}

/** 按项目发送 Webhook 测试/通知消息 */
export function sendProjectHookMessage(data) {
  return request({
    url: '/project/hook/send',
    method: 'post',
    data: data || {}
  })
}

export function getProjectCodePrdConfig(params) {
  return request({
    url: '/project/code-prd/config',
    method: 'get',
    params: params || {}
  })
}

export function saveProjectCodePrdConfig(data) {
  return request({
    url: '/project/code-prd/config/save',
    method: 'post',
    data: data || {}
  })
}

export function getProjectCodePrdBranches(params) {
  return request({
    url: '/project/code-prd/branches',
    method: 'get',
    params: params || {}
  })
}

export function getProjectCodePrdList(params) {
  return request({
    url: '/project/code-prd/list',
    method: 'get',
    params: Object.assign({ pageNo: 1, pageSize: 10 }, params || {})
  })
}

export function getProjectCodePrdDetail(params) {
  return request({
    url: '/project/code-prd/detail',
    method: 'get',
    params: params || {}
  })
}

export function generateProjectCodePrd(data) {
  return request({
    url: '/project/code-prd/generate',
    method: 'post',
    data: data || {},
    timeout: 360000
  })
}

export function exportProjectCodePrdDocx(params) {
  return download('/project/code-prd/export-docx', params)
}
