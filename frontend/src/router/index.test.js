import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  guards: [],
  getCurrentUser: vi.fn(),
}))

vi.mock('vue-router', () => ({
  createRouter: vi.fn(() => ({
    beforeEach: (guard) => mocks.guards.push(guard),
  })),
  createWebHistory: vi.fn(),
}))

vi.mock('@/utils/api', () => ({
  api: {
    getCurrentUser: mocks.getCurrentUser,
  },
}))

import router from './index.js'

const guard = mocks.guards[0]

function destination(name, meta = {}, fullPath = '/dashboard') {
  return {
    name,
    meta,
    matched: [{ meta }],
    fullPath,
  }
}

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})

describe('router access guards', () => {
  it('redirects unauthenticated users to login and preserves the destination', async () => {
    const to = destination(
      'exercise',
      { requiresAuth: true },
      '/exercises/42',
    )

    await expect(guard(to)).resolves.toEqual({
      name: 'login',
      query: { redirect: '/exercises/42' },
    })

    expect(mocks.getCurrentUser).not.toHaveBeenCalled()
  })

  it('redirects an authenticated admin away from the student dashboard', async () => {
    localStorage.setItem('authToken', 'test-token')
    mocks.getCurrentUser.mockResolvedValue({ role: 'admin' })

    await expect(
      guard(destination('dashboard', {
        requiresAuth: true,
        studentOnly: true,
      })),
    ).resolves.toEqual({ name: 'admin-dashboard' })
  })

  it('redirects a non-admin away from the admin dashboard', async () => {
    localStorage.setItem('authToken', 'test-token')
    mocks.getCurrentUser.mockResolvedValue({ role: 'student' })

    await expect(
      guard(destination('admin-dashboard', {
        requiresAuth: true,
        requiresAdmin: true,
      })),
    ).resolves.toEqual({ name: 'dashboard' })
  })

  it('sends an authenticated admin from login to the admin dashboard', async () => {
    localStorage.setItem('authToken', 'test-token')
    mocks.getCurrentUser.mockResolvedValue({ role: 'admin' })

    await expect(
      guard(destination('login', { requiresGuest: true }, '/login')),
    ).resolves.toEqual({ name: 'admin-dashboard' })
  })

  it('sends an authenticated student from login to the student dashboard', async () => {
    localStorage.setItem('authToken', 'test-token')
    mocks.getCurrentUser.mockResolvedValue({ role: 'student' })

    await expect(
      guard(destination('login', { requiresGuest: true }, '/login')),
    ).resolves.toEqual({ name: 'dashboard' })
  })

  it('fails closed for the admin route when user verification fails', async () => {
    localStorage.setItem('authToken', 'test-token')
    mocks.getCurrentUser.mockRejectedValue(new Error('Network error'))

    await expect(
      guard(destination('admin-dashboard', {
        requiresAuth: true,
        requiresAdmin: true,
      })),
    ).resolves.toEqual({ name: 'dashboard' })
  })
})
