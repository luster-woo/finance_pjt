import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken') || localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 동시 401 응답이 여러 개 올 때 refresh를 한 번만 호출하기 위한 공유 Promise
let _refreshPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const request = error.config
    const refresh = localStorage.getItem('refreshToken')

    if (error.response?.status === 401 && !request?._retry) {
      request._retry = true

      if (refresh) {
        try {
          if (!_refreshPromise) {
            _refreshPromise = axios
              .post(`${api.defaults.baseURL}/accounts/refresh/`, { refresh })
              .finally(() => { _refreshPromise = null })
          }
          const { data } = await _refreshPromise
          localStorage.setItem('accessToken', data.access)
          request.headers.Authorization = `Bearer ${data.access}`
          return api(request)
        } catch {
          // refresh 토큰도 유효하지 않으면 아래에서 인증 정보를 정리합니다.
        }
      }

      const isLoginRequest = request?.url?.includes('/accounts/login/')
      clearAuth()
      if (!isLoginRequest && window.location.pathname !== '/login') {
        const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`)
        window.location.assign(`/login?redirect=${redirect}`)
      }
    }

    return Promise.reject(error)
  },
)

export function saveAuth(data) {
  localStorage.setItem('accessToken', data.access)
  localStorage.removeItem('token')  // 구 키 제거
  if (data.refresh) localStorage.setItem('refreshToken', data.refresh)
  window.dispatchEvent(new Event('auth-changed'))
}

export function clearAuth() {
  localStorage.removeItem('accessToken')
  localStorage.removeItem('refreshToken')
  localStorage.removeItem('token')
  window.dispatchEvent(new Event('auth-changed'))
}

export function getErrorMessage(error, fallback = '요청 처리 중 오류가 발생했습니다.') {
  const data = error.response?.data
  if (typeof data === 'string') return data
  if (data?.detail) return data.detail
  if (data?.message) return data.message
  if (data && typeof data === 'object') {
    const first = Object.values(data).flat()[0]
    if (first) return String(first)
  }
  return fallback
}
