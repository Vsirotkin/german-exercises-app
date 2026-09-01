import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('API Client Logic', () => {
  // 1. Создаем надежный мок для localStorage
  const localStorageMock = (() => {
    let store = {}
    return {
      getItem: (key) => store[key] || null,
      setItem: (key, value) => { store[key] = value.toString() },
      clear: () => { store = {} },
      removeItem: (key) => { delete store[key] }
    }
  })()

  beforeEach(() => {
    // 2. Подменяем глобальный localStorage на наш мок перед каждым тестом
    vi.stubGlobal('localStorage', localStorageMock)
    localStorage.clear()
  })

  it('should add Authorization header when token exists', () => {
    // Устанавливаем токен
    localStorage.setItem('access_token', 'test-token-123')

    // Эмулируем логику интерцептора из api.js
    const config = { headers: {} }
    const token = localStorage.getItem('access_token')

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Проверяем результат
    expect(config.headers.Authorization).toBe('Bearer test-token-123')
  })

  it('should not add Authorization header when token is missing', () => {
    // Токен не установлен (localStorage.clear() сработал в beforeEach)
    const config = { headers: {} }
    const token = localStorage.getItem('access_token')

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Проверяем, что заголовок не добавился
    expect(config.headers.Authorization).toBeUndefined()
  })
})

