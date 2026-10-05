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
            <label for="username" class="mb-2 block text-sm font-medium text-slate-700">
              Benutzername
            </label>

            <input id="username" v-model="username" type="text" autocomplete="username" required
              class="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100" />
          </div>

          <div>
            <label for="password" class="mb-2 block text-sm font-medium text-slate-700">
              Passwort
            </label>

            <input id="password" v-model="password" type="password" autocomplete="current-password" required
              class="w-full rounded-lg border border-slate-300 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100" />
          </div>

          <div v-if="errorMessage" class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {{ errorMessage }}
          </div>

          <button type="submit" :disabled="isLoading"
            class="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60">
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

const handleLogin = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await api.login({
      username: username.value,
      password: password.value,
    })

    if (response?.access) {
      localStorage.setItem('authToken', response.access)
    }

    if (response?.refresh) {
      localStorage.setItem('refreshToken', response.refresh)
    }

    const redirect = route.query.redirect || '/dashboard'

    await router.replace(redirect)
  } catch (error) {
    console.error('Login failed:', error)

    errorMessage.value =
      error?.response?.data?.detail ||
      'Anmeldung fehlgeschlagen. Bitte überprüfen Sie Ihre Daten.'
  } finally {
    isLoading.value = false
  }
}
</script>
