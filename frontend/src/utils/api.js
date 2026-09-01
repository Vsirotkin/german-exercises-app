// src/utils/api.js
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error),
)

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('⚠️ Session expired (401)')
      // Здесь можно добавить авто-разлогин
    }
    return Promise.reject(error)
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

  async refreshToken(refreshToken) {
    const res = await apiClient.post('/auth/token/refresh/', { refresh: refreshToken })
    return res.data
  },

  // ✅ НОВЫЙ МЕТОД: Получение списка всех упражнений
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

  // src/utils/api.js

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
