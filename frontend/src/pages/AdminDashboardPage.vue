<template>
  <section class="space-y-8">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-sm font-semibold text-blue-600">
          Administration
        </p>
        <h1 class="mt-2 text-3xl font-bold tracking-tight text-slate-900">
          Lernendenübersicht
        </h1>
        <p class="mt-2 max-w-2xl text-slate-600">
          Überblick über Schülerprofile, gespeicherte Übungsergebnisse und
          den bisherigen Lernfortschritt.
        </p>
      </div>

      <button
        type="button"
        :disabled="isLoading"
        class="inline-flex w-fit items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
        @click="loadStudents"
      >
        Aktualisieren
      </button>
    </div>

    <div
      v-if="errorMessage"
      role="alert"
      class="rounded-2xl border border-red-200 bg-red-50 p-5"
    >
      <h2 class="font-semibold text-red-900">
        Die Lernendendaten konnten nicht geladen werden.
      </h2>
      <p class="mt-2 text-sm text-red-700">
        {{ errorMessage }}
      </p>
      <button
        type="button"
        class="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700"
        @click="loadStudents"
      >
        Erneut versuchen
      </button>
    </div>

    <div v-if="isLoading" class="flex min-h-48 items-center justify-center">
      <div class="text-center">
        <div class="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>
        <p class="mt-4 text-sm text-slate-500">
          Lade Lernendenstatistik...
        </p>
      </div>
    </div>

    <template v-else-if="!errorMessage">
      <div class="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-slate-500">
                Schülerprofile gesamt
              </p>
              <p class="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                {{ students.length }}
              </p>
            </div>
            <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl">
              👥
            </span>
          </div>
          <p class="mt-3 text-sm text-slate-500">
            Alle in der Datenbank angelegten Profile
          </p>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-slate-500">
                Mit Ergebnissen
              </p>
              <p class="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                {{ activeStudents }}
              </p>
            </div>
            <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-xl">
              ✓
            </span>
          </div>
          <p class="mt-3 text-sm text-slate-500">
            Profile mit mindestens einem gespeicherten Ergebnis
          </p>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-slate-500">
                Ergebnisse gesamt
              </p>
              <p class="mt-3 text-3xl font-bold tracking-tight text-slate-900">
                {{ totalResults }}
              </p>
            </div>
            <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-50 text-xl">
              📈
            </span>
          </div>
          <p class="mt-3 text-sm text-slate-500">
            Gespeicherte Bearbeitungen aller Schüler
          </p>
        </article>
      </div>

      <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="border-b border-slate-200 px-5 py-5 sm:px-6">
          <h2 class="text-lg font-semibold text-slate-900">
            Statistik nach Schüler
          </h2>
          <p class="mt-1 text-sm text-slate-500">
            Die Angaben basieren auf gespeicherten Übungsergebnissen.
            Für Profile ohne Ergebnisse werden keine Leistungswerte angezeigt.
          </p>
        </div>

        <div v-if="students.length === 0" class="px-6 py-12 text-center">
          <div class="text-4xl">📚</div>
          <h3 class="mt-4 font-semibold text-slate-900">
            Noch keine Schülerprofile vorhanden
          </h3>
          <p class="mt-2 text-sm text-slate-500">
            Sobald Profile angelegt sind, werden sie hier angezeigt.
          </p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-[980px] w-full divide-y divide-slate-200 text-left text-sm">
            <thead class="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th scope="col" class="px-5 py-3.5">Schüler</th>
                <th scope="col" class="px-4 py-3.5">Niveau</th>
                <th scope="col" class="px-4 py-3.5 text-right">Ergebnisse</th>
                <th scope="col" class="px-4 py-3.5 text-right">Durchschnitt</th>
                <th scope="col" class="px-4 py-3.5 text-right">Bestes Ergebnis</th>
                <th scope="col" class="px-5 py-3.5">Letzte Aktivität</th>
              </tr>
            </thead>

            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="student in students"
                :key="student.id"
                class="transition hover:bg-slate-50"
              >
                <td class="px-5 py-4">
                  <div class="font-semibold text-slate-900">
                    {{ student.first_name }} {{ student.last_name }}
                  </div>
                  <div class="mt-1 text-xs text-slate-500">
                    {{ student.email }}
                  </div>
                  <div class="mt-1 text-xs text-slate-400">
                    Profil #{{ student.id }}
                  </div>
                </td>

                <td class="px-4 py-4">
                  <span class="inline-flex rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
                    {{ student.level || '—' }}
                  </span>
                </td>

                <td class="px-4 py-4 text-right tabular-nums text-slate-700">
                  {{ student.total_exercises }}
                </td>

                <td class="px-4 py-4 text-right tabular-nums">
                  <span :class="student.total_exercises ? 'font-semibold text-slate-900' : 'text-slate-400'">
                    {{ formatScore(student.average_score, student.total_exercises) }}
                  </span>
                </td>

                <td class="px-4 py-4 text-right tabular-nums">
                  <span :class="student.total_exercises ? 'font-semibold text-slate-900' : 'text-slate-400'">
                    {{ formatScore(student.best_score, student.total_exercises) }}
                  </span>
                </td>

                <td class="px-5 py-4 text-slate-600">
                  {{ formatDate(student.last_activity) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="border-t border-slate-100 bg-slate-50 px-5 py-3 text-xs text-slate-500 sm:px-6">
          {{ students.length }} Profile · Leistungswerte aus dem Backend
        </div>
      </section>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/utils/api'

const students = ref([])
const isLoading = ref(true)
const errorMessage = ref('')

const activeStudents = computed(
  () => students.value.filter(student => student.total_exercises > 0).length,
)

const totalResults = computed(
  () => students.value.reduce(
    (total, student) => total + Number(student.total_exercises || 0),
    0,
  ),
)

function formatScore(score, totalExercises) {
  if (!totalExercises) return '—'

  const value = Number(score)
  if (!Number.isFinite(value)) return '—'

  return `${value.toLocaleString('de-DE', {
    maximumFractionDigits: 1,
  })}%`
}

function formatDate(value) {
  if (!value) return 'Noch keine Aktivität'

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

async function loadStudents() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const data = await api.getAdminStudents()

    students.value = Array.isArray(data)
      ? data
      : Array.isArray(data?.results)
        ? data.results
        : []
  } catch (error) {
    console.error('Failed to load admin student statistics:', error)

    errorMessage.value =
      error?.response?.data?.detail ||
      'Die Statistik konnte nicht geladen werden.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadStudents)
</script>
