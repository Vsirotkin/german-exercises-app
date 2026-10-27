<template>
  <section class="space-y-8">
    <!-- Loading -->
    <div
      v-if="isLoading"
      class="flex min-h-[50vh] items-center justify-center"
    >
      <div class="text-center">
        <div
          class="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"
        ></div>
        <p class="mt-4 text-sm text-slate-500">
          Lade deinen Lernfortschritt...
        </p>
      </div>
    </div>

    <!-- Current-user/profile error -->
    <div
      v-else-if="errorMessage"
      role="alert"
      class="rounded-2xl border border-red-200 bg-red-50 p-6"
    >
      <h1 class="text-lg font-semibold text-red-900">
        Dashboard konnte nicht geladen werden
      </h1>
      <p class="mt-2 text-sm leading-6 text-red-700">
        {{ errorMessage }}
      </p>
      <button
        type="button"
        class="mt-4 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-red-700"
        @click="loadDashboard"
      >
        Erneut versuchen
      </button>
    </div>

    <template v-else>
      <!-- Greeting -->
      <header
        class="relative overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-6 sm:p-8"
      >
        <div
          class="pointer-events-none absolute -right-12 -top-16 h-48 w-48 rounded-full bg-blue-200/30 blur-3xl"
        ></div>

        <div class="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="text-sm font-semibold text-blue-700">
              Dein persönlicher Lernbereich
            </p>
            <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
              Guten Tag, {{ userDisplayName }}! 👋
            </h1>
            <p class="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
              Setze dein Deutschtraining fort und behalte deine bisherigen
              Ergebnisse im Blick.
            </p>
          </div>

          <RouterLink
            to="/exercises"
            class="inline-flex w-fit shrink-0 items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
          >
            Übungen öffnen
            <span aria-hidden="true">→</span>
          </RouterLink>
        </div>
      </header>

      <!-- Statistics are real backend values, or explicitly unavailable -->
      <section>
        <div class="mb-4">
          <h2 class="text-lg font-semibold text-slate-900">
            Dein Fortschritt
          </h2>
          <p class="mt-1 text-sm text-slate-500">
            Basierend auf deinen gespeicherten Übungsergebnissen.
          </p>
        </div>

        <div
          v-if="progressError"
          role="status"
          class="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
        >
          Die Fortschrittsstatistik ist momentan nicht verfügbar.
          {{ progressError }}
        </div>

        <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-sm font-medium text-slate-500">
                  Durchschnittliches Ergebnis
                </p>
                <p class="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                  {{ progress ? formatPercent(progress.average_score) : '—' }}
                </p>
              </div>
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
                📊
              </span>
            </div>
            <p class="mt-3 text-xs leading-5 text-slate-500">
              Durchschnitt aller gespeicherten Ergebnisse
            </p>
          </article>

          <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-sm font-medium text-slate-500">
                  Bestes Ergebnis
                </p>
                <p class="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                  {{ progress ? formatPercent(progress.best_score) : '—' }}
                </p>
              </div>
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-xl">
                🏆
              </span>
            </div>
            <p class="mt-3 text-xs leading-5 text-slate-500">
              Dein höchster gespeicherter Prozentwert
            </p>
          </article>

          <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-sm font-medium text-slate-500">
                  Gespeicherte Ergebnisse
                </p>
                <p class="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                  {{ progress ? progress.total_exercises : '—' }}
                </p>
              </div>
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-50 text-xl">
                ✓
              </span>
            </div>
            <p class="mt-3 text-xs leading-5 text-slate-500">
              Einschließlich erneuter Versuche
            </p>
          </article>

          <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="text-sm font-medium text-slate-500">
                  Verfügbare Übungen
                </p>
                <p class="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                  {{ exerciseCount === null ? '—' : exerciseCount }}
                </p>
              </div>
              <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-50 text-xl">
                📚
              </span>
            </div>
            <p class="mt-3 text-xs leading-5 text-slate-500">
              Im Übungskatalog verfügbar
            </p>
          </article>
        </div>

        <div
          v-if="progress && progress.last_activity"
          class="mt-4 text-sm text-slate-500"
        >
          Letzte Aktivität: {{ formatDate(progress.last_activity) }}
        </div>

        <div
          v-else-if="progress && progress.total_exercises === 0"
          class="mt-4 rounded-xl bg-slate-100 px-4 py-3 text-sm text-slate-600"
        >
          Du hast noch keine Ergebnisse gespeichert. Starte deine erste Übung,
          um deinen Fortschritt hier zu sehen.
        </div>
      </section>

      <!-- Recent history -->
      <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="flex flex-col gap-3 border-b border-slate-200 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <h2 class="text-lg font-semibold text-slate-900">
              Letzte Übungsergebnisse
            </h2>
            <p class="mt-1 text-sm text-slate-500">
              Deine zuletzt gespeicherten Ergebnisse.
            </p>
          </div>

          <RouterLink
            to="/exercises"
            class="inline-flex w-fit items-center gap-1 text-sm font-semibold text-blue-700 no-underline transition hover:text-blue-800"
          >
            Zum Katalog
            <span aria-hidden="true">→</span>
          </RouterLink>
        </div>

        <div
          v-if="historyError"
          role="status"
          class="m-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
        >
          Die Übungshistorie ist momentan nicht verfügbar.
          {{ historyError }}
        </div>

        <div
          v-else-if="history.length === 0"
          class="px-6 py-12 text-center"
        >
          <div class="text-4xl">📝</div>
          <h3 class="mt-4 font-semibold text-slate-900">
            Noch keine Ergebnisse
          </h3>
          <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
            Sobald du eine Übung abschließt, findest du dein Ergebnis hier.
          </p>
          <RouterLink
            to="/exercises"
            class="mt-5 inline-flex items-center justify-center rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white no-underline transition hover:bg-blue-700"
          >
            Erste Übung starten
          </RouterLink>
        </div>

        <div v-else class="divide-y divide-slate-100">
          <article
            v-for="item in recentHistory"
            :key="item.id"
            class="flex flex-col gap-3 px-5 py-4 transition hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between sm:px-6"
          >
            <div class="flex min-w-0 items-start gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-lg">
                📘
              </span>
              <div class="min-w-0">
                <h3 class="truncate font-semibold text-slate-900">
                  {{ item.exercise_title || 'Übung' }}
                </h3>
                <p class="mt-1 text-xs text-slate-500">
                  {{ formatDate(item.completed_at) }}
                </p>
              </div>
            </div>

            <div class="flex items-center justify-between gap-5 sm:justify-end">
              <div class="text-sm text-slate-600">
                {{ formatNumber(item.score) }} /
                {{ formatNumber(item.max_score) }} Punkte
              </div>
              <span
                class="min-w-20 rounded-lg px-3 py-1.5 text-center text-sm font-bold tabular-nums"
                :class="resultClass(item.percentage)"
              >
                {{ formatPercent(item.percentage) }}
              </span>
            </div>
          </article>
        </div>
      </section>

      <!-- Personal recommendations -->
      <section class="overflow-hidden rounded-2xl border border-indigo-100 bg-white shadow-sm">
        <div class="border-b border-indigo-100 bg-indigo-50/60 px-5 py-5 sm:px-6">
          <h2 class="text-lg font-semibold text-slate-900">
            Empfehlungen für dich
          </h2>
          <p class="mt-1 text-sm text-slate-600">
            Deine nächsten Lernschritte, basierend auf deinem Lernstand.
          </p>
        </div>

        <div
          v-if="recommendationsError"
          role="status"
          class="m-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
        >
          Empfehlungen sind momentan nicht verfügbar.
          {{ recommendationsError }}
          <button
            type="button"
            class="ml-2 font-semibold underline"
            @click="loadRecommendations"
          >
            Erneut versuchen
          </button>
        </div>

        <div
          v-else-if="recommendationsLoading"
          class="px-6 py-8 text-sm text-slate-500"
          role="status"
        >
          Empfehlungen werden geladen...
        </div>

        <div
          v-else-if="recommendations.length === 0"
          class="px-6 py-8 text-sm text-slate-600"
        >
          Momentan gibt es keine Empfehlungen. Entdecke weitere Übungen im Katalog.
          <RouterLink
            to="/exercises"
            class="ml-1 font-semibold text-blue-700 hover:text-blue-800"
          >
            Zum Katalog →
          </RouterLink>
        </div>

        <div v-else class="divide-y divide-slate-100">
          <article
            v-for="item in recommendations"
            :key="item.id"
            class="px-5 py-4 sm:px-6"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div class="min-w-0">
                <div class="flex flex-wrap items-center gap-2">
                  <h3 class="font-semibold text-slate-900">
                    {{ item.title || 'Lernempfehlung' }}
                  </h3>
                  <span
                    v-if="item.priority"
                    class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
                  >
                    {{ item.priority === 'high' ? 'Hohe Priorität' : item.priority === 'normal' ? 'Mittlere Priorität' : 'Empfehlung' }}
                  </span>
                </div>
                <p v-if="item.message" class="mt-2 text-sm leading-6 text-slate-700">
                  {{ item.message }}
                </p>
                <p v-if="item.reason" class="mt-1 text-sm leading-6 text-slate-500">
                  {{ item.reason }}
                </p>
                <p v-if="item.topic?.name" class="mt-2 text-xs font-medium text-indigo-700">
                  Thema: {{ item.topic.name }}
                </p>
              </div>

              <RouterLink
                v-if="item.exercise?.id"
                :to="`/exercises/${item.exercise.id}`"
                class="inline-flex w-fit shrink-0 items-center gap-1 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white no-underline transition hover:bg-blue-700"
              >
                Übung öffnen →
              </RouterLink>
            </div>
          </article>
        </div>
      </section>

      <!-- Next action -->
      <section class="flex flex-col gap-5 rounded-2xl border border-blue-100 bg-blue-50 p-6 sm:flex-row sm:items-center sm:justify-between sm:p-7">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">
            Bereit für die nächste Übung?
          </h2>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Öffne den Katalog und wähle eine der für dich verfügbaren Übungen.
          </p>
        </div>
        <RouterLink
          to="/exercises"
          class="inline-flex w-fit shrink-0 items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white no-underline transition hover:bg-blue-700"
        >
          Übungen entdecken
        </RouterLink>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/utils/api'

const user = ref(null)
const progress = ref(null)
const history = ref([])
const exerciseCount = ref(null)
const recommendations = ref([])
const recommendationsLoading = ref(false)
const recommendationsError = ref('')

const isLoading = ref(true)
const errorMessage = ref('')
const progressError = ref('')
const historyError = ref('')
const exerciseError = ref('')

const userDisplayName = computed(() => (
  user.value?.first_name ||
  user.value?.username ||
  'Lernender'
))

const recentHistory = computed(() => history.value.slice(0, 5))

function normalizeList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

async function loadRecommendations() {
  recommendationsLoading.value = true
  recommendationsError.value = ''

  try {
    const response = await api.getRecommendationFeed()
    recommendations.value = normalizeList(response?.recommendations)
  } catch (error) {
    console.error('Failed to load recommendations:', error)
    recommendations.value = []
    recommendationsError.value =
      error?.response?.data?.error?.message ||
      error?.response?.data?.detail ||
      'Bitte versuche es später erneut.'
  } finally {
    recommendationsLoading.value = false
  }
}

function formatNumber(value) {
  const number = Number(value)

  if (!Number.isFinite(number)) return '—'

  return number.toLocaleString('de-DE', {
    maximumFractionDigits: 1,
  })
}

function formatPercent(value) {
  const number = Number(value)

  if (!Number.isFinite(number)) return '—'

  return `${number.toLocaleString('de-DE', {
    maximumFractionDigits: 1,
  })}%`
}

function formatDate(value) {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return '—'

  return date.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function resultClass(percentage) {
  const score = Number(percentage)

  if (!Number.isFinite(score)) {
    return 'bg-slate-100 text-slate-600'
  }

  if (score >= 80) {
    return 'bg-emerald-50 text-emerald-700'
  }

  if (score >= 60) {
    return 'bg-amber-50 text-amber-700'
  }

  return 'bg-red-50 text-red-700'
}

async function loadDashboard() {
  isLoading.value = true
  errorMessage.value = ''
  progressError.value = ''
  historyError.value = ''
  exerciseError.value = ''
  progress.value = null
  history.value = []
  exerciseCount.value = null

  try {
    const currentUser = await api.getCurrentUser()
    user.value = currentUser

    if (!currentUser?.student_id) {
      errorMessage.value =
        'Für dieses Konto ist kein Schülerprofil verknüpft. Bitte wende dich an den Administrator.'
      return
    }

    recommendationsLoading.value = true

    const results = await Promise.allSettled([
      api.getStudentProgress(currentUser.student_id),
      api.getStudentHistory(currentUser.student_id),
      api.getExercisesList(),
      api.getRecommendationFeed(),
    ])

    const [
      progressResult,
      historyResult,
      exercisesResult,
      recommendationsResult,
    ] = results

    if (progressResult.status === 'fulfilled') {
      progress.value = progressResult.value
    } else {
      console.error('Failed to load student progress:', progressResult.reason)
      progressError.value =
        progressResult.reason?.response?.data?.detail ||
        'Bitte versuche es später erneut.'
    }

    if (historyResult.status === 'fulfilled') {
      history.value = normalizeList(historyResult.value)
    } else {
      console.error('Failed to load student history:', historyResult.reason)
      historyError.value =
        historyResult.reason?.response?.data?.detail ||
        'Bitte versuche es später erneut.'
    }

    if (exercisesResult.status === 'fulfilled') {
      exerciseCount.value = normalizeList(exercisesResult.value).length
    } else {
      console.error('Failed to load exercise catalog:', exercisesResult.reason)
      exerciseError.value =
        exercisesResult.reason?.response?.data?.detail ||
        'Bitte versuche es später erneut.'
    }

    if (recommendationsResult.status === 'fulfilled') {
      recommendations.value = normalizeList(
        recommendationsResult.value?.recommendations,
      )
      recommendationsError.value = ''
    } else {
      console.error(
        'Failed to load recommendations:',
        recommendationsResult.reason,
      )
      recommendations.value = []
      recommendationsError.value =
        recommendationsResult.reason?.response?.data?.error?.message ||
        recommendationsResult.reason?.response?.data?.detail ||
        'Bitte versuche es später erneut.'
    }
    recommendationsLoading.value = false
  } catch (error) {
    recommendationsLoading.value = false
    console.error('Failed to load current user:', error)

    errorMessage.value =
      error?.response?.data?.detail ||
      'Die Benutzerdaten konnten nicht geladen werden. Bitte versuche es erneut.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadDashboard)
</script>
