import request from '@/utils/request'

export function getPlanList(projectId, params) {
  return request({
    url: '/plan/list',
    method: 'get',
    params: Object.assign({ project_id: projectId }, params || {})
  })
}

export function createPlan(projectId, data) {
  return request({
    url: '/plan/create',
    method: 'post',
    data: Object.assign({ project_id: projectId }, data)
  })
}

export function updatePlan(projectId, planId, data) {
  return request({
    url: '/plan/update',
    method: 'post',
    data: Object.assign({ project_id: projectId, id: planId }, data)
  })
}

/** POST /plan/delete，body 传 planId */
export function deletePlan(planId) {
  return request({
    url: '/plan/delete',
    method: 'post',
    data: {
      planId
    }
  })
}

export function getPlanDetail(projectId, planId) {
  return request({
    url: '/plan/detail',
    method: 'get',
    params: {
      project_id: projectId,
      id: planId
    }
  })
}

export function createPlanRound(data) {
  return request({
    url: '/plan/round/create',
    method: 'post',
    data
  })
}

export function getPlanRoundList(projectId, params) {
  return request({
    url: '/plan/round/list',
    method: 'get',
    params: Object.assign({ project_id: projectId }, params || {})
  })
}

export function addPlanCases(projectId, planId, data) {
  return request({
    url: '/plan/case/add',
    method: 'post',
    data: Object.assign({ project_id: projectId, plan_id: planId }, data)
  })
}

export function getPlanCaseList(projectId, planId, params) {
  return request({
    url: '/plan/case/list',
    method: 'get',
    params: Object.assign({ project_id: projectId, plan_id: planId, pageNo: 1, pageSize: 10 }, params || {})
  })
}

export function executePlanCase(projectId, planId, planCaseId, data) {
  return request({
    url: '/plan/case/execute',
    method: 'post',
    data: Object.assign({ project_id: projectId, plan_id: planId, id: planCaseId }, data)
  })
}

export function aiExecutePlanCase(projectId, planId, data) {
  return request({
    url: '/plan/case/ai-execute',
    method: 'post',
    data: Object.assign({ project_id: projectId, plan_id: planId }, data || {})
  })
}

export function getPlanProgress(projectId, planId) {
  return request({
    url: '/plan/progress',
    method: 'get',
    params: {
      project_id: projectId,
      plan_id: planId
    }
  })
}
