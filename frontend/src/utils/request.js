import axios from 'axios'
import { Message } from 'element-ui'
import router from '../router/index'
import store from '@/vuex/store'
import { clearTokenStorage, tryRefreshAccessToken } from './authToken'

const service = axios.create({
  baseURL: '/it/api',
  timeout: 90000
})

function pushLoginExpired(message) {
  clearTokenStorage()
  localStorage.removeItem('authUser')
  localStorage.removeItem('userMenus')
  store.commit('ClearCurrentUser')
  router.push({ name: 'login' })
  Message.error(message || '登录已失效，请重新登录')
}

/** FastAPI HTTPException 常把业务体放在 detail 里，统一摊平便于读 code/message */
function normalizeApiPayload(data) {
  if (!data || typeof data !== 'object') return data || {}
  const detail = data.detail
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    if (detail.code !== undefined || detail.message !== undefined || detail.success !== undefined) {
      return Object.assign({}, data, detail)
    }
  }
  return data
}

function apiCode(data) {
  const payload = normalizeApiPayload(data)
  if (!payload || payload.code === undefined || payload.code === null) return null
  const n = Number(payload.code)
  return Number.isFinite(n) ? n : null
}

function isMissingToken(data) {
  return apiCode(data) === 40001
}

/** 仅 451：token 无效或已过期，走静默续期并重试一次 */
function isTokenExpiredRefreshable(data) {
  return apiCode(data) === 451
}

function isForbiddenApi(data) {
  return apiCode(data) === 40003
}

/** @param {{ config: object, data?: object }} ctx */
function handleTokenExpiredRefreshAndRetry(ctx) {
  const cfg = (ctx && ctx.config) || {}
  const pdata = (ctx && ctx.data) || {}
  if (cfg.__retriedTokenRefresh) {
    pushLoginExpired(pdata.message || 'token无效或已过期！')
    return Promise.reject(new Error('token无效或已过期'))
  }
  return tryRefreshAccessToken().then(ok => {
    if (!ok) {
      pushLoginExpired(pdata.message || 'token无效或已过期！')
      return Promise.reject(new Error('token无效或已过期'))
    }
    const nextCfg = Object.assign({}, cfg, { __retriedTokenRefresh: true })
    nextCfg.headers = Object.assign({}, nextCfg.headers || {})
    const newAt = localStorage.getItem('accessToken')
    if (newAt) {
      nextCfg.headers.accessToken = newAt
    }
    return service.request(nextCfg)
  })
}

service.interceptors.request.use(
  config => {
    const accessToken = localStorage.getItem('accessToken')
    if (accessToken) {
      config.headers.accessToken = accessToken
    }
    return config
  },
  error => Promise.reject(error)
)

service.interceptors.response.use(
  response => {
    const data = normalizeApiPayload(response && response.data ? response.data : {})
    if (data && data.code === 500) {
      Message.error('服务异常')
      return Promise.reject(new Error(data.message || '服务异常'))
    }
    if (data && isMissingToken(data)) {
      pushLoginExpired(data.message || '缺少token！')
      return Promise.reject(new Error(data.message || '缺少token'))
    }
    if (data && isTokenExpiredRefreshable(data)) {
      return handleTokenExpiredRefreshAndRetry({ config: response.config, data })
    }
    if (data && isForbiddenApi(data)) {
      Message.error(data.message || '无权限访问该接口！')
      return Promise.reject(new Error(data.message || '无权限访问该接口'))
    }
    if (data && data.success === false) {
      Message.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    if (data && data.code !== undefined && data.code !== 20000) {
      Message.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return data
  },
  error => {
    const res = error && error.response
    const data = normalizeApiPayload(res && res.data ? res.data : null)
    if (data && isMissingToken(data) && error.config) {
      pushLoginExpired(data.message || '缺少token！')
      return Promise.reject(new Error(data.message || '缺少token'))
    }
    if (data && isTokenExpiredRefreshable(data) && error.config && !error.config.__retriedTokenRefresh) {
      return handleTokenExpiredRefreshAndRetry({ config: error.config, data })
    }
    if (data && isForbiddenApi(data)) {
      Message.error(data.message || '无权限访问该接口！')
      return Promise.reject(new Error(data.message || '无权限访问该接口'))
    }
    if (data && typeof data === 'object') {
      if (data.success === false) {
        Message.error(data.message || '请求失败')
      } else if (data.code && data.code !== 20000 && data.message) {
        Message.error(data.message || '请求失败')
      }
    } else if (error && error.message) {
      Message.error(error.message)
    }
    return Promise.reject(data && data.message ? new Error(data.message) : error)
  }
)

export default service
