<template>
  <div class="flex min-h-[80vh] items-center justify-center">
    <div class="w-full max-w-md">
      <div class="mb-8 text-center">
        <div class="mb-3 text-4xl">🇩🇪</div>

        <h1 class="text-3xl font-bold tracking-tight text-slate-900">
          German Exercises
        </h1>

        <p class="mt-2 text-slate-500">
          Ihre personalisierten Deutschübungen
        </p>
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h2 class="text-xl font-semibold text-slate-900">
          Anmeldung
        </h2>

        <form class="mt-6 space-y-5" @submit.prevent="handleLogin">
          <div>
            <label
              for="username"
              class="mb-2 block text-sm font-medium text-slate-700"
            >
              Benutzername
            </label>

            <input
              id="username"
              v-model="username"
              type="text"
              autocomplete="username"
              required
              :disabled="isLoading"
              class="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-50"
            />
          </div>

          <div>
            <label
              for="password"
              class="mb-2 block text-sm font-medium text-slate-700"
            >
              Passwort
            </label>

            <input
              id="password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
              :disabled="isLoading"
              class="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-50"
            />
          </div>

          <div
            v-if="errorMessage"
            role="alert"
            class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {{ errorMessage }}
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {{ isLoading ? 'Anmeldung...' : 'Anmelden' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '@/utils/api'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

function getDefaultLocation(role) {
  return role === 'admin'
    ? { name: 'admin-dashboard' }
    : { name: 'dashboard' }
}

function getSafeRedirect(candidate, role) {
  const fallback = getDefaultLocation(role)

  if (
    typeof candidate !== 'string' ||
    !candidate.startsWith('/') ||
    candidate.startsWith('//') ||
    candidate.startsWith('/\\')
  ) {
    return fallback
  }

  const resolved = router.resolve(candidate)
  const requiresAuth = resolved.matched.some(
    record => record.meta.requiresAuth,
  )

  if (!requiresAuth || resolved.name === 'login') {
    return fallback
  }

  // Keep administrators and students in their own dashboard spaces.
  if (role === 'admin' && resolved.name === 'dashboard') {
    return { name: 'admin-dashboard' }
  }

  if (role !== 'admin' && resolved.name === 'admin-dashboard') {
    return { name: 'dashboard' }
  }

  return resolved.fullPath
}

function getLoginError(error) {
  const detail = error?.response?.data?.detail

  if (
    typeof detail === 'string' &&
    /no active account|given credentials|invalid credentials/i.test(detail)
  ) {
    return 'Benutzername oder Passwort ist falsch oder das Konto ist nicht aktiv.'
  }

  return detail ||
    'Anmeldung fehlgeschlagen. Bitte überprüfen Sie Ihre Daten.'
}

const handleLogin = async () => {
  if (isLoading.value) return

  isLoading.value = true
  errorMessage.value = ''

  let tokensStored = false

  try {
    const response = await api.login({
      username: username.value,
      password: password.value,
    })

    if (
      typeof response?.access !== 'string' ||
      !response.access.trim() ||
      typeof response?.refresh !== 'string' ||
      !response.refresh.trim()
    ) {
      localStorage.removeItem('authToken')
      localStorage.removeItem('refreshToken')

      errorMessage.value =
        'Der Server hat keine gültigen Sitzungstoken zurückgegeben.'
      return
    }

    localStorage.setItem('authToken', response.access)
    localStorage.setItem('refreshToken', response.refresh)
    tokensStored = true

    // Use the authenticated Django response to determine the role.
    const currentUser = await api.getCurrentUser()

    await router.replace(
      getSafeRedirect(route.query.redirect, currentUser?.role),
    )
  } catch (error) {
    console.error('Login failed:', error)

    if (tokensStored) {
      localStorage.removeItem('authToken')
      localStorage.removeItem('refreshToken')
      errorMessage.value =
        'Die Anmeldung konnte nicht abgeschlossen werden. Bitte versuchen Sie es erneut.'
    } else {
      errorMessage.value = getLoginError(error)
    }
  } finally {
    isLoading.value = false
  }
}
</script>
