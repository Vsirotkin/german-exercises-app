import { createRouter, createWebHistory } from 'vue-router'

import { api } from '@/utils/api'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import DashboardPage from '@/pages/DashboardPage.vue'
import AdminDashboardPage from '@/pages/AdminDashboardPage.vue'
import ExercisesPage from '@/pages/ExercisesPage.vue'
import ExercisePage from '@/pages/ExercisePage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { requiresGuest: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardPage,
    meta: {
      requiresAuth: true,
      studentOnly: true,
    },
  },
  {
    path: '/admin-dashboard',
    name: 'admin-dashboard',
    component: AdminDashboardPage,
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
  },
  {
    path: '/exercises',
    name: 'exercises',
    component: ExercisesPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/exercises/:id',
    name: 'exercise',
    component: ExercisePage,
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: { name: 'home' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const token = localStorage.getItem('authToken')
  const requiresAuth = to.matched.some(
    record => record.meta.requiresAuth,
  )
  const requiresGuest = to.matched.some(
    record => record.meta.requiresGuest,
  )
  const requiresAdmin = to.matched.some(
    record => record.meta.requiresAdmin,
  )
  const studentOnly = to.matched.some(
    record => record.meta.studentOnly,
  )

  if (requiresAuth && !token) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  // Role-specific routes and the guest login page must verify the user
  // against Django rather than trusting a client-side role flag.
  if (token && (requiresGuest || requiresAdmin || studentOnly)) {
    let currentUser

    try {
      currentUser = await api.getCurrentUser()
    } catch {
      // Fail closed for the administrative route if the role cannot
      // be confirmed. The backend still enforces the actual permissions.
      if (requiresAdmin) {
        return { name: 'dashboard' }
      }

      // Avoid a navigation loop on temporary API/network failures.
      return true
    }

    const isAdmin = currentUser?.role === 'admin'

    if (requiresGuest) {
      return {
        name: isAdmin ? 'admin-dashboard' : 'dashboard',
      }
    }

    if (requiresAdmin && !isAdmin) {
      return { name: 'dashboard' }
    }

    if (studentOnly && isAdmin) {
      return { name: 'admin-dashboard' }
    }
  }

  return true
})

export default router
