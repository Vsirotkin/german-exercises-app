<!-- src/components/RecommendationsPanel.vue -->
<template>
  <div class="recommendations-panel">
    <!-- Заголовок -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h4 class="mb-0">
        <i class="bi bi-lightbulb me-2"></i>
        Empfehlungen
      </h4>
      <!-- Переключатель стратегий (оставляем, это полезно ученику) -->
      <div class="btn-group btn-group-sm" role="group" v-if="!isLoading && recommendations.length > 0">
        <button v-for="strategy in strategies" :key="strategy.value" @click="changeStrategy(strategy.value)"
          class="btn btn-sm" :class="currentStrategy === strategy.value ? 'btn-primary' : 'btn-outline-primary'"
          :title="strategy.description">
          {{ strategy.label }}
        </button>
      </div>
    </div>

    <!-- Состояние загрузки -->
    <div v-if="isLoading" class="text-center py-3">
      <div class="spinner-border spinner-border-sm text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <small class="text-muted ms-2">Empfehlungen werden geladen...</small>
    </div>

    <!-- Сообщение об ошибке -->
    <div v-else-if="error" class="alert alert-warning py-2 mb-3">
      <i class="bi bi-exclamation-triangle me-2"></i>
      {{ error }}
    </div>

    <!-- Список рекомендаций -->
    <div v-else-if="recommendations.length > 0">
      <div class="list-group">
        <div v-for="(rec, index) in recommendations" :key="rec.exercise_id || index"
          class="list-group-item list-group-item-action recommendation-item" @click="selectExercise(rec.exercise_id)">

          <div class="d-flex justify-content-between align-items-start">
            <div class="flex-grow-1">
              <div class="d-flex align-items-center mb-1">
                <span class="badge bg-secondary me-2">#{{ index + 1 }}</span>
                <strong>{{ rec.title || 'Übung ' + (index + 1) }}</strong>
              </div>
              <small class="text-muted d-block mb-1">{{ rec.description || rec.topic || '' }}</small>

              <!-- Отображение причины рекомендации -->
              <div v-if="rec.reason" class="recommendation-reason small">
                <i class="bi" :class="getReasonIcon(rec.reason)"></i>
                {{ rec.reason }}
              </div>
            </div>

            <!-- Бейдж приоритета (если есть в ответе) -->
            <div v-if="rec.priority" class="text-end ms-2">
              <div class="priority-badge" :class="getPriorityClass(rec.priority)">
                {{ Math.round(rec.priority) }}
              </div>
              <small class="text-muted d-block mt-1" style="font-size: 0.6rem;">Priorität</small>
            </div>
          </div>

          <!-- Теги темы -->
          <div v-if="rec.topic" class="mt-2">
            <span class="badge bg-info text-dark">{{ rec.topic }}</span>
            <span v-if="rec.is_review" class="badge bg-warning text-dark ms-1">Wiederholung</span>
          </div>
        </div>
      </div>

      <!-- Кнопка пути обучения УДАЛЕНА, так как бэкенд еще не поддерживает этот эндпоинт -->
    </div>

    <!-- Сообщение если нет рекомендаций -->
    <div v-else class="alert alert-info">
      <i class="bi bi-info-circle me-2"></i>
      Keine Empfehlungen verfügbar. Beginnen Sie mit Übungen, um personalisierte Empfehlungen zu erhalten.
    </div>

    <!-- Блок пути обучения полностью удален до реализации бэкенда -->
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { api } from '../utils/api.js'

// Props - ID ученика (должен приходить от родителя)
const props = defineProps({
  studentId: {
    type: Number,
    default: null
  }
})

// Emits - выбор упражнения
const emit = defineEmits(['exercise-select'])

// Реактивные данные
const recommendations = ref([])
const isLoading = ref(false)
const error = ref(null)
const currentStrategy = ref('weak_topics')

// Стратегии
const strategies = [
  { value: 'weak_topics', label: 'Schwächen', description: 'Themen mit niedriger Punktzahl' },
  { value: 'mixed', label: 'Gemischte', description: 'Mix aus schwachen und neuen Themen' },
  { value: 'review', label: 'Wiederholung', description: 'Wiederholung alter Themen' }
]

// Методы
const loadRecommendations = async () => {
  if (!props.studentId) {
    recommendations.value = []
    return
  }

  isLoading.value = true
  error.value = null

  try {
    // Вызываем существующий метод из api.js
    // Примечание: бэкенд должен поддерживать query-параметры student_id, limit, strategy
    const data = await api.getRecommendations(props.studentId, 5, currentStrategy.value)

    // Если бэкенд возвращает массив напрямую
    if (Array.isArray(data)) {
      recommendations.value = data
    }
    // Если бэкенд возвращает объект { recommendations: [...] }
    else if (data.recommendations) {
      recommendations.value = data.recommendations
    }
    else {
      recommendations.value = []
    }
  } catch (err) {
    console.error('Error loading recommendations:', err)
    error.value = 'Konnte Empfehlungen nicht laden. Bitte versuchen Sie es später.'
    recommendations.value = []
  } finally {
    isLoading.value = false
  }
}

const changeStrategy = (strategy) => {
  currentStrategy.value = strategy
  loadRecommendations()
}

const selectExercise = (exerciseId) => {
  if (exerciseId) {
    emit('exercise-select', exerciseId)
  }
}

const getReasonIcon = (reason) => {
  if (!reason) return 'bi-lightbulb text-primary'
  const r = reason.toLowerCase()
  if (r.includes('schwach') || r.includes('niedrig')) return 'bi-arrow-down-circle text-danger'
  if (r.includes('neu') || r.includes('new')) return 'bi-plus-circle text-success'
  if (r.includes('wieder') || r.includes('review')) return 'bi-arrow-repeat text-warning'
  return 'bi-lightbulb text-primary'
}

const getPriorityClass = (priority) => {
  if (priority > 70) return 'priority-high'
  if (priority > 40) return 'priority-medium'
  return 'priority-low'
}

// Слежение за изменением ID
watch(() => props.studentId, (newId) => {
  if (newId) {
    loadRecommendations()
  } else {
    recommendations.value = []
  }
})

onMounted(() => {
  if (props.studentId) {
    loadRecommendations()
  }
})
</script>

<style scoped>
.recommendations-panel {
  font-size: 0.9rem;
}

.recommendation-item {
  border-left: 3px solid #007bff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.recommendation-item:hover {
  background-color: #f8f9fa;
  transform: translateX(2px);
}

.recommendation-reason {
  color: #6c757d;
  font-style: italic;
}

.priority-badge {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  border-radius: 50%;
  text-align: center;
  font-weight: bold;
  font-size: 0.7rem;
}

.priority-high {
  background-color: #dc3545;
  color: white;
}

.priority-medium {
  background-color: #ffc107;
  color: #212529;
}

.priority-low {
  background-color: #28a745;
  color: white;
}

.btn-group .btn {
  padding: 0.2rem 0.4rem;
  font-size: 0.75rem;
}
</style>
