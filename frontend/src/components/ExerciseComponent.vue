<!-- src/components/ExerciseComponent.vue -->
<template>
  <!-- Состояние загрузки -->
  <div v-if="isLoading" class="text-center py-5">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading...</span>
    </div>
    <p class="mt-3">Übung wird geladen...</p>
  </div>

  <!-- Ошибка -->
  <div v-else-if="error" class="alert alert-danger">
    <i class="bi bi-exclamation-triangle me-2"></i>
    {{ error }}
    <div class="mt-2">
      <button @click="$emit('back-to-list')" class="btn btn-sm btn-outline-secondary">
        Zurück zur Liste
      </button>
    </div>
  </div>

  <!-- Упражнение загружено -->
  <div v-else-if="exercise">
    <!-- Заголовок -->
    <div class="card mb-4 shadow-sm">
      <div class="card-body">
        <h2 class="card-title h4">{{ exercise.title }}</h2>
        <p class="card-text text-muted mb-2">{{ exercise.description || '' }}</p>
        <span class="badge bg-primary">{{ exercise.language || 'de' }}</span>
        <span class="badge bg-secondary ms-2">{{ exercise.exercise_type }}</span>
      </div>
    </div>

    <!-- Блокировка повторения (Заглушка, пока нет бэкенда для results) -->
    <!-- Если в будущем реализуем эндпоинт /api/results/exercise/{id}/status/, раскомментируем логику -->
    <!--
    <div v-if="isRetryBlocked" class="alert alert-info mb-4">
      <i class="bi bi-clock me-2"></i>
      Diese Übung kann erst in {{ daysUntilRetry }} Tagen wiederholt werden.
    </div>
    -->

    <!-- Рендер в зависимости от типа -->
    <div v-if="!isRetryBlocked">
      <!-- ИСПРАВЛЕНО: exercise_type вместо type -->
      <GapFill v-if="exercise.exercise_type === 'gap_fill'" :exercise="exercise" @back-to-list="$emit('back-to-list')"
        @answers-checked="onAnswersChecked" />

      <VocabularyDrill v-else-if="exercise.exercise_type === 'vocabulary_drill'" :exercise="exercise"
        @back-to-list="$emit('back-to-list')" />

      <div v-else class="alert alert-warning">
        Unbekannter Übungstyp: {{ exercise.exercise_type }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../utils/api' // Используем наш централизованный API клиент
import GapFill from './GapFill.vue'
import VocabularyDrill from './VocabularyDrill.vue'

// Props и emits
const props = defineProps({
  topicName: { type: String, required: true },
  exerciseId: { type: [Number, String], required: true }
})

const emit = defineEmits(['back-to-list'])

// Состояния
const exercise = ref(null)
const isLoading = ref(true)
const error = ref(null)
// retryStatus пока не используем, так как нет соответствующего эндпоинта на бэкенде
const isRetryBlocked = ref(false)

// Загрузка упражнения
const loadExercise = async () => {
  isLoading.value = true
  error.value = null
  exercise.value = null

  try {
    // Используем наш метод из api.js (он сам добавит /api/ и токен)
    const data = await api.getExerciseFull(props.exerciseId)
    exercise.value = data

    // Здесь можно добавить логику проверки статуса повторения,
    // когда бэкенд будет готов (эндпоинт GET /api/results/{exercise_id}/status/)
    // await checkRetryStatus(props.exerciseId)

  } catch (err) {
    console.error('Failed to load exercise:', err)
    error.value = `Fehler beim Laden der Übung: ${err.message || 'Unbekannter Fehler'}`
  } finally {
    isLoading.value = false
  }
}

// Сохранение результата
const onAnswersChecked = async (scoreData) => {
  // scoreData может быть объектом { score: 85, total: 100, answers: [...] }
  // или просто числом. Приведем к формату, который ждет бэкенд.

  const payload = {
    exercise: exercise.value.id,
    score: scoreData.score || scoreData, // Поддержка обоих форматов
    total_questions: scoreData.total || 0,
    details: scoreData.answers || {}
  }

  try {
    // Используем api.saveExerciseResult (он отправит POST /api/results/)
    await api.saveExerciseResult(payload)
    console.log('Ergebnis erfolgreich gespeichert!')
  } catch (err) {
    console.error('Fehler beim Speichern des Ergebnisses:', err)
    // Не показываем ошибку пользователю, чтобы не портить опыт, но логируем
  }
}

// Загрузка при монтировании
onMounted(() => {
  loadExercise()
})
</script>

<style scoped>
.card {
  border: none;
}
</style>
