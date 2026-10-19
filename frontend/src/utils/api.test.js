/**
 * @vitest-environment jsdom
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => {
  const client = vi.fn()
  const requestUse = vi.fn()
  const responseUse = vi.fn()
  const axiosPost = vi.fn()

  client.defaults = { baseURL: '/api' }
  client.interceptors = {
    request: { use: requestUse },
    response: { use: responseUse },
  }
  client.get = vi.fn()
  client.post = vi.fn()

  return {
    client,
    requestUse,
    responseUse,
    axiosPost,
  }
})

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mocks.client),
    post: (...args) => mocks.axiosPost(...args),
  },
}))

import { api } from './api.js'

const requestInterceptor = mocks.requestUse.mock.calls[0][0]
const responseErrorInterceptor = mocks.responseUse.mock.calls[0][1]

function createStorage() {
  let store = {}

  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(store, key)
        ? store[key]
        : null
    },
    setItem(key, value) {
      store[key] = String(value)
    },
    removeItem(key) {
      delete store[key]
    },
    clear() {
      store = {}
    },
  }
}

const storage = createStorage()
const fakeWindow = { dispatchEvent: vi.fn() }

beforeEach(() => {
  vi.clearAllMocks()
  storage.clear()

  vi.stubGlobal('localStorage', storage)
  vi.stubGlobal('window', fakeWindow)
})

describe('API client', () => {
  it('adds the authToken as a Bearer Authorization header', () => {
    storage.setItem('authToken', 'test-access-token')

    const config = requestInterceptor({ headers: {} })

    expect(config.headers.Authorization).toBe(
      'Bearer test-access-token',
    )
  })

  it('does not add an Authorization header when no token exists', () => {
    const config = requestInterceptor({ headers: {} })

    expect(config.headers.Authorization).toBeUndefined()
  })

  it('stores both rotated tokens and retries the original request', async () => {
    storage.setItem('authToken', 'old-access-token')
    storage.setItem('refreshToken', 'old-refresh-token')

    mocks.axiosPost.mockResolvedValue({
      data: {
        access: 'new-access-token',
        refresh: 'new-refresh-token',
      },
    })
    mocks.client.mockResolvedValue({ data: 'retried-response' })

    const original = {
      url: '/exercises/',
      headers: { Authorization: 'Bearer old-access-token' },
    }

    const result = await responseErrorInterceptor({
      config: original,
      response: { status: 401 },
    })

    expect(mocks.axiosPost).toHaveBeenCalledWith(
      '/api/auth/token/refresh/',
      { refresh: 'old-refresh-token' },
    )
    expect(storage.getItem('authToken')).toBe('new-access-token')
    expect(storage.getItem('refreshToken')).toBe('new-refresh-token')
    expect(mocks.client).toHaveBeenCalledWith(original)
    expect(result).toEqual({ data: 'retried-response' })
  })

  it('clears both tokens and signals logout when refresh fails', async () => {
    storage.setItem('authToken', 'expired-access-token')
    storage.setItem('refreshToken', 'expired-refresh-token')

    mocks.axiosPost.mockRejectedValue(new Error('Refresh token expired'))

    await expect(
      responseErrorInterceptor({
        config: {
          url: '/exercises/',
          headers: {},
        },
        response: { status: 401 },
      }),
    ).rejects.toThrow('Refresh token expired')

    expect(storage.getItem('authToken')).toBeNull()
    expect(storage.getItem('refreshToken')).toBeNull()
    expect(fakeWindow.dispatchEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'auth:logout' }),
    )
  })

  it('exposes the login API method', () => {
    expect(api.login).toBeTypeOf('function')
  })
})
