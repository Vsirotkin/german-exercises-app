// src/utils/api.js
import axios from 'axios'

const TOKEN_KEY = 'authToken'
const REFRESH_KEY = 'refreshToken'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

// ---- refresh-очередь ----
let isRefreshing = false
let pendingRequests = [] // [{ resolve, reject, config }]

const onRefreshed = (token) => {
  pendingRequests.forEach(({ resolve, config }) => {
    config.headers.Authorization = `Bearer ${token}`
    resolve(apiClient(config))
  })
  pendingRequests = []
}

const onRefreshFailed = (error) => {
  pendingRequests.forEach(({ reject }) => reject(error))
  pendingRequests = []
}

// ---- request interceptor ----
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error),
)

// ---- response interceptor ----
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    // не 401 / нет конфига / уже пытались ретраить — просто пробрасываем
    if (status !== 401 || !original || original._retry) {
      return Promise.reject(error)
    }

    // сам запрос на refresh или логин не ретраим — иначе рекурсия
    const url = original.url || ''
    if (url.includes('/auth/token/refresh/') || url.includes('/auth/login/')) {
      return Promise.reject(error)
    }

    const refresh = localStorage.getItem(REFRESH_KEY)
    if (!refresh) {
      // refresh-токена нет — сразу разлогин
      localStorage.removeItem(TOKEN_KEY)
      window.dispatchEvent(new Event('auth:logout'))
      return Promise.reject(error)
    }

    original._retry = true

    // если refresh уже идёт — встаём в очередь
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingRequests.push({ resolve, reject, config: original })
      })
    }

    isRefreshing = true

    try {
      const res = await axios.post(`${apiClient.defaults.baseURL}/auth/token/refresh/`, { refresh })
      const newAccess = res.data.access
      localStorage.setItem(TOKEN_KEY, newAccess)

      onRefreshed(newAccess)
      return apiClient(original)
    } catch (refreshError) {
      onRefreshFailed(refreshError)
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)
      window.dispatchEvent(new Event('auth:logout'))
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

export const api = {
  async login(credentials) {
    const res = await apiClient.post('/auth/login/', credentials)
    return res.data
  },

  async getCurrentUser() {
    const res = await apiClient.get('/me/')
    return res.data
  },

  async refreshToken(token) {
    const res = await apiClient.post('/auth/token/refresh/', { refresh: token })
    return res.data
  },

  async getExercisesList() {
    const res = await apiClient.get('/exercises/')
    return res.data
  },

  async getExerciseFull(id) {
    const res = await apiClient.get(`/exercises/${id}/full/`)
    return res.data
  },

  async getRecommendations(studentId, limit = 5, strategy = 'weak_topics') {
    const res = await apiClient.get('/recommendations/student/topics/', {
      params: { student_id: studentId, limit, strategy },
    })
    return res.data
  },

  async saveExerciseResult(resultData) {
    const res = await apiClient.post('/results/', resultData)
    return res.data
  },

  async getStudentProgress(studentId) {
    const res = await apiClient.get(`/results/student/${studentId}/progress/`)
    return res.data
  },

  async getStudentHistory(studentId) {
    const res = await apiClient.get(`/results/student/${studentId}/`)
    return res.data
  },
}

export default apiClient
