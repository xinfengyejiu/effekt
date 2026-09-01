import request from '@/utils/request'

export function getReportList(params) {
  return request({
    url: '/report/list',
    method: 'get',
    params: Object.assign({ pageNo: 1, pageSize: 20 }, params || {})
  })
}

export function generateReport(data) {
  return request({
    url: '/report/generate',
    method: 'post',
    data: data || {}
  })
}

export function uploadHtmlReport(data) {
  return request({
    url: '/report/upload-html',
    method: 'post',
    data,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000
  })
}

export function deleteReport(data) {
  return request({
    url: '/report/delete',
    method: 'post',
    data: data || {}
  })
}

export function getReportDetail(reportId, projectId) {
  return request({
    url: '/report/detail',
    method: 'get',
    params: Object.assign(
      {
        reportId: reportId,
        report_id: reportId,
        id: reportId
      },
      projectId
        ? {
            projectId: projectId,
            project_id: projectId
          }
        : {}
    )
  })
}
