import axios from 'axios'

const TOKEN_KEY = 'authToken'
const REFRESH_KEY = 'refreshToken'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Очередь запросов, ожидающих обновления access-токена.
let isRefreshing = false
let pendingRequests = []

const onRefreshed = (token) => {
  pendingRequests.forEach(({ resolve, config }) => {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
    resolve(apiClient(config))
  })

  pendingRequests = []
}

const onRefreshFailed = (error) => {
  pendingRequests.forEach(({ reject }) => reject(error))
  pendingRequests = []
}

const dispatchAuthLogout = () => {
  window.dispatchEvent(new Event('auth:logout'))
}

// Добавляем текущий access-токен в запрос.
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)

    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error),
)

// При 401 пытаемся обновить access-токен через refresh-токен.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const status = error.response?.status

    if (status !== 401 || !original || original._retry) {
      return Promise.reject(error)
    }

    const url = original.url || ''

    // Не запускаем обновление повторно для login и refresh endpoint.
    if (
      url.includes('/auth/token/refresh/') ||
      url.includes('/auth/login/')
    ) {
      return Promise.reject(error)
    }

    const refresh = localStorage.getItem(REFRESH_KEY)

    if (!refresh) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)
      dispatchAuthLogout()
      return Promise.reject(error)
    }

    original._retry = true

    // Если обновление уже выполняется, ожидаем его результат.
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingRequests.push({ resolve, reject, config: original })
      })
    }

    isRefreshing = true

    try {
      const response = await axios.post(
        `${apiClient.defaults.baseURL}/auth/token/refresh/`,
        { refresh },
      )

      const newAccess = response.data?.access

      if (typeof newAccess !== 'string' || !newAccess.trim()) {
        throw new Error(
          'Token refresh response did not include a valid access token.',
        )
      }

      localStorage.setItem(TOKEN_KEY, newAccess)

      // SimpleJWT при включённой ротации возвращает и новый refresh.
      // Сохраняем его, иначе следующий refresh-запрос может использовать
      // уже заменённый токен.
      const newRefresh = response.data?.refresh

      if (typeof newRefresh === 'string' && newRefresh.trim()) {
        localStorage.setItem(REFRESH_KEY, newRefresh)
      }

      onRefreshed(newAccess)

      return apiClient(original)
    } catch (refreshError) {
      onRefreshFailed(refreshError)

      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)

      dispatchAuthLogout()

      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

export const api = {
  async login(credentials) {
    const response = await apiClient.post('/auth/login/', credentials)
    return response.data
  },

  async getCurrentUser() {
    const response = await apiClient.get('/me/')
    return response.data
  },

  async refreshToken(token) {
    const response = await apiClient.post('/auth/token/refresh/', {
      refresh: token,
    })
    return response.data
  },

  async getExercisesList() {
    const response = await apiClient.get('/exercises/')
    return response.data
  },

  async getAdminStudents() {
    const response = await apiClient.get('/admin/students/')
    return response.data
  },

  async getExerciseFull(id) {
    const response = await apiClient.get(`/exercises/${id}/full/`)
    return response.data
  },

  async getRecommendations(studentId, limit = 5, strategy = 'weak_topics') {
    const response = await apiClient.get('/recommendations/student/topics/', {
      params: { student_id: studentId, limit, strategy },
    })
    return response.data
  },

  async checkExerciseAnswer(data) {
    const response = await apiClient.post('/results/check-answer/', data)
    return response.data
  },

  async saveExerciseResult(resultData) {
    const response = await apiClient.post('/results/', resultData)
    return response.data
  },

  async getStudentProgress(studentId) {
    const response = await apiClient.get(
      `/results/student/${studentId}/progress/`,
    )
    return response.data
  },

  async getStudentHistory(studentId) {
    const response = await apiClient.get(`/results/student/${studentId}/`)
    return response.data
  },

  async validateExerciseImport(data) {
    const response = await apiClient.post(
      '/admin/exercises/import/validate/',
      data,
    )
    return response.data
  },

  async batchImportExercises(data) {
    const response = await apiClient.post(
      '/admin/exercises/import/batch/',
      data,
    )
    return response.data
  },
}

export default apiClient
