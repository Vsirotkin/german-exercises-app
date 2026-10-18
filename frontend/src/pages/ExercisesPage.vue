<template>
  <section class="space-y-8">
    <!-- Заголовок -->
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900">
          Verfügbare Übungen
        </h1>
        <p class="mt-1 text-sm text-slate-500">
          Wähle eine Übung und setze dein Deutschtraining fort.
        </p>
      </div>

      <div class="inline-flex w-fit items-center rounded-full bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700">
        {{ exercises.length }} Übungen
      </div>
    </div>

    <!-- Ошибка -->
    <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ error }}
      <button type="button" class="ml-2 font-semibold underline underline-offset-2" @click="loadExercises">
        Erneut versuchen
      </button>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      <div v-for="placeholder in 3" :key="placeholder"
        class="animate-pulse rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="h-5 w-3/4 rounded bg-slate-200"></div>
        <div class="mt-3 h-4 w-1/2 rounded bg-slate-200"></div>
        <div class="mt-8 h-2 rounded bg-slate-200"></div>
        <div class="mt-6 h-10 rounded-lg bg-slate-200"></div>
      </div>
    </div>

    <!-- Пустой список -->
    <div v-else-if="!error && exercises.length === 0"
      class="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
      <div class="text-4xl">📚</div>
      <h2 class="mt-4 text-lg font-semibold text-slate-900">
        Noch keine Übungen verfügbar
      </h2>
      <p class="mt-2 text-sm text-slate-500">
        Sobald Übungen verfügbar sind, werden sie hier angezeigt.
      </p>
    </div>

    <!-- Список упражнений -->
    <div v-else class="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      <article v-for="exercise in exercises" :key="exercise.id"
        class="group relative flex min-h-[310px] flex-col overflow-hidden rounded-2xl border bg-white shadow-sm transition-[transform,box-shadow,border-color] duration-300 ease-out motion-reduce:transition-none"
        :class="getCardClass(exercise)">
        <!-- Perfekt badge -->
        <div v-if="exercise.status === 'mastered'"
          class="absolute right-4 top-4 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-700 shadow-sm">
          🏆 Perfekt!
        </div>

        <div class="flex flex-1 flex-col p-6">
          <!-- Заголовок -->
          <div class="pr-20">
            <h2 class="text-lg font-semibold leading-snug text-slate-900">
              {{ exercise.title }}
            </h2>

            <div class="mt-3 flex flex-wrap gap-2">
              <span v-for="topic in exercise.topics || []" :key="topic"
                class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                {{ topic }}
              </span>
            </div>
          </div>

          <!-- Статус -->
          <div class="mt-5 flex items-center gap-2 text-sm">
            <span class="flex h-7 w-7 items-center justify-center rounded-full"
              :class="getStatusIconClass(exercise.status)" :title="getStatusTitle(exercise.status)">
              {{ getStatusIcon(exercise.status) }}
            </span>

            <span class="font-medium" :class="getStatusTextClass(exercise.status)">
              {{ getStatusLabel(exercise.status) }}
            </span>
          </div>

          <!-- Прогресс -->
          <div v-if="exercise.score !== null && exercise.score !== undefined" class="mt-5">
            <div class="mb-2 flex items-center justify-between text-sm">
              <span class="text-slate-500">Fortschritt</span>
              <span class="font-semibold" :class="getStatusTextClass(exercise.status)">
                {{ exercise.score }}%
              </span>
            </div>

            <div class="h-2 overflow-hidden rounded-full bg-slate-100">
              <div class="h-full rounded-full transition-all duration-500" :class="getProgressClass(exercise.status)"
                :style="{ width: `${Math.min(Math.max(exercise.score, 0), 100)}%` }"></div>
            </div>
          </div>

          <!-- Кнопка -->
          <div class="mt-auto pt-6">
            <button type="button"
              class="flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition"
              :class="exercise.is_locked
                ? 'cursor-not-allowed bg-slate-100 text-slate-400'
                : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800'" :disabled="exercise.is_locked"
              :title="exercise.is_locked ? getLockTitle() : ''" @click="handleStart(exercise)">
              <span>{{ exercise.is_locked ? '🔒' : '▶' }}</span>
              <span>
                {{ exercise.is_locked ? 'Gesperrt' : 'Übung starten' }}
              </span>
            </button>
          </div>
        </div>

        <!-- Footer -->
        <footer class="flex items-center justify-between border-t border-slate-100 px-6 py-3 text-xs text-slate-400">
          <span class="flex items-center gap-1.5">
            <span>🌐</span>
            {{ exercise.language || 'german' }}
          </span>

          <span class="uppercase tracking-wide">
            {{ formatExerciseType(exercise.exercise_type) }}
          </span>
        </footer>
      </article>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '@/utils/api'

const router = useRouter()

const exercises = ref([])
const loading = ref(true)
const error = ref('')

const loadExercises = async () => {
  loading.value = true
  error.value = ''

  try {
    const data = await api.getExercisesList()

    exercises.value = Array.isArray(data)
      ? data
      : data?.results || []
  } catch (err) {
    console.error('Failed to load exercises:', err)

    error.value = 'Die Übungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

const handleStart = (exercise) => {
  if (exercise.is_locked) {
    return
  }

  router.push({
    name: 'exercise',
    params: {
      id: exercise.id,
    },
  })
}

const getCardClass = (exercise) => {
  if (exercise.is_locked) {
    return 'border-slate-200 opacity-75'
  }

  const classes = {
    mastered: 'border-amber-300 shadow-amber-100 hover:-translate-y-1 hover:shadow-lg',
    completed: 'border-emerald-200 hover:-translate-y-1 hover:shadow-lg',
    review_recommended: 'border-amber-200 hover:-translate-y-1 hover:shadow-lg',
    needs_review: 'border-red-200 hover:-translate-y-1 hover:shadow-lg',
    not_started: 'border-slate-200 hover:-translate-y-1 hover:shadow-lg',
  }

  return classes[exercise.status] || classes.not_started
}


const getStatusLabel = (status) => {
  const labels = {
    mastered: 'Perfekt abgeschlossen',
    completed: 'Abgeschlossen',
    review_recommended: 'Wiederholung empfohlen',
    needs_review: 'Nochmal üben',
    not_started: 'Noch nicht begonnen',
  }

  return labels[status] || 'Noch nicht begonnen'
}

const getStatusTitle = (status) => {
  const titles = {
    mastered: 'Perfekt abgeschlossen!',
    completed: 'Abgeschlossen!',
    review_recommended: 'Wiederholung empfohlen',
    needs_review: 'Nochmal üben',
    not_started: 'Noch nicht begonnen',
  }

  return titles[status] || ''
}

const getStatusIcon = (status) => {
  const icons = {
    mastered: '🏆',
    completed: '✓',
    review_recommended: '!',
    needs_review: '×',
    not_started: '○',
  }

  return icons[status] || '○'
}

const getStatusIconClass = (status) => {
  const classes = {
    mastered: 'bg-amber-100 text-amber-700',
    completed: 'bg-emerald-100 text-emerald-700',
    review_recommended: 'bg-amber-100 text-amber-700',
    needs_review: 'bg-red-100 text-red-700',
    not_started: 'bg-slate-100 text-slate-500',
  }

  return classes[status] || classes.not_started
}

const getStatusTextClass = (status) => {
  const classes = {
    mastered: 'text-amber-700',
    completed: 'text-emerald-700',
    review_recommended: 'text-amber-700',
    needs_review: 'text-red-700',
    not_started: 'text-slate-500',
  }

  return classes[status] || classes.not_started
}

const getProgressClass = (status) => {
  const classes = {
    mastered: 'bg-amber-400',
    completed: 'bg-emerald-500',
    review_recommended: 'bg-amber-400',
    needs_review: 'bg-red-500',
    not_started: 'bg-slate-400',
  }

  return classes[status] || classes.not_started
}

const getLockTitle = () => {
  return 'Vorherige Übung mit weniger als 50% abgeschlossen. Erst wiederholen!'
}

const formatExerciseType = (type) => {
  if (!type) {
    return ''
  }

  return type
    .replace(/_/g, ' ')
    .toUpperCase()
}

onMounted(loadExercises)
</script>
