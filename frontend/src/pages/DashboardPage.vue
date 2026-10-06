<template>
  <section>
    <!-- Loading -->
    <div v-if="isLoading" class="flex min-h-[60vh] items-center justify-center">
      <div class="text-center">
        <div class="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>

        <p class="mt-4 text-sm text-slate-500">
          Lade Benutzerdaten...
        </p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="errorMessage" class="rounded-2xl border border-red-200 bg-red-50 p-6">
      <h1 class="text-lg font-semibold text-red-900">
        Fehler beim Laden
      </h1>

      <p class="mt-2 text-sm text-red-700">
        {{ errorMessage }}
      </p>

      <button type="button"
        class="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700"
        @click="loadDashboard">
        Erneut versuchen
      </button>
    </div>

    <!-- Dashboard -->
    <template v-else>
      <div class="mb-8">
        <p class="text-sm font-medium text-blue-600">
          Deutsch lernen
        </p>

        <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">
          Guten Tag, {{ userDisplayName }}! 👋
        </h1>

        <p class="mt-2 max-w-2xl text-slate-500">
          Setzen Sie Ihr Training fort und verbessern Sie Ihre Deutschkenntnisse.
        </p>
      </div>

      <div class="grid gap-6 md:grid-cols-3">
        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-sm font-medium text-slate-500">
            Mein Fortschritt
          </p>

          <p class="mt-2 text-3xl font-bold text-slate-900">
            —
          </p>

          <p class="mt-1 text-sm text-slate-400">
            Wird bald angezeigt
          </p>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-sm font-medium text-slate-500">
            Übungen
          </p>

          <p class="mt-2 text-3xl font-bold text-slate-900">
            —
          </p>

          <p class="mt-1 text-sm text-slate-400">
            Verfügbare Übungen
          </p>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p class="text-sm font-medium text-slate-500">
            Empfehlung
          </p>

          <p class="mt-2 text-lg font-semibold text-slate-900">
            Bald verfügbar
          </p>

          <p class="mt-1 text-sm text-slate-400">
            Personalisierte Empfehlung
          </p>
        </div>
      </div>

      <div class="mt-8 rounded-2xl border border-blue-100 bg-blue-50 p-6">
        <h2 class="text-lg font-semibold text-slate-900">
          Weiterlernen
        </h2>

        <p class="mt-2 text-sm text-slate-600">
          Ihre persönlichen Übungen und Empfehlungen werden hier angezeigt.
        </p>

        <button type="button"
          class="mt-4 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700">
          Übungen öffnen
        </button>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/utils/api'

const user = ref(null)
const isLoading = ref(true)
const errorMessage = ref('')

const userDisplayName = computed(() => {
  if (!user.value) {
    return ''
  }

  return (
    user.value.first_name ||
    user.value.username ||
    'Lernender'
  )
})

const loadDashboard = async () => {
  isLoading.value = true
  errorMessage.value = ''

  try {
    user.value = await api.getCurrentUser()
  } catch (error) {
    console.error('Failed to load current user:', error)

    errorMessage.value =
      error?.response?.data?.detail ||
      'Die Benutzerdaten konnten nicht geladen werden.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>
