<!-- src/components/StudentProgress.vue -->
<template>
  <div class="student-progress">
    <!-- Заголовок -->
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h4 class="mb-0">
        <i class="bi bi-graph-up me-2"></i>
        Lernfortschritt
      </h4>
      <button @click="loadData" class="btn btn-sm btn-outline-primary" :disabled="isLoading">
        <i class="bi bi-arrow-clockwise" :class="{ 'spin': isLoading }"></i>
        Aktualisieren
      </button>
    </div>

    <!-- Если ID не передан -->
    <div v-if="!studentId" class="alert alert-warning">
      <i class="bi bi-person-x me-2"></i>
      Benutzer nicht identifiziert. Bitte melden Sie sich erneut an.
    </div>

    <!-- Загрузка -->
    <div v-else-if="isLoading" class="text-center py-3">
      <div class="spinner-border spinner-border-sm text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <small class="text-muted ms-2">Fortschritt wird geladen...</small>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="alert alert-warning py-2 mb-3">
      <i class="bi bi-exclamation-triangle me-2"></i>
      {{ error }}
    </div>

    <!-- Прогресс -->
    <div v-else-if="progress" class="progress-container">
      <!-- Статистика -->
      <div class="card mb-3 shadow-sm">
        <div class="card-body">
          <div class="row text-center">
            <div class="col-4">
              <div class="stat-number">{{ progress.total_exercises || 0 }}</div>
              <div class="stat-label">Übungen</div>
            </div>
            <div class="col-4">
              <div class="stat-number text-success">{{ Math.round(progress.average_score || 0) }}%</div>
              <div class="stat-label">Ø Score</div>
            </div>
            <div class="col-4">
              <div class="stat-number text-primary">{{ Math.round(progress.best_score || 0) }}%</div>
              <div class="stat-label">Beste</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Бар прогресса -->
      <div class="mb-3">
        <div class="d-flex justify-content-between mb-1">
          <span class="small fw-bold">Gesamtfortschritt</span>
          <span class="small">{{ Math.round(progress.average_score || 0) }}%</span>
        </div>
        <div class="progress" style="height: 8px;">
          <div class="progress-bar" :class="getProgressBarClass(progress.average_score)"
            :style="{ width: (progress.average_score || 0) + '%' }"></div>
        </div>
      </div>

      <!-- Последняя активность -->
      <div v-if="progress.last_activity" class="card bg-light border-0">
        <div class="card-body py-2">
          <div class="d-flex align-items-center">
            <i class="bi bi-clock-history text-muted me-2"></i>
            <div>
              <small class="text-muted d-block">Letzte Aktivität</small>
              <span class="small fw-bold">{{ formatDate(progress.last_activity) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="alert alert-info small">
        <i class="bi bi-info-circle me-1"></i>
        Noch keine Übungen abgeschlossen.
      </div>

      <!-- История (сворачиваемая) -->
      <div v-if="history.length > 0" class="mt-3">
        <button @click="showHistory = !showHistory" class="btn btn-sm btn-link text-decoration-none p-0 mb-2">
          <i class="bi" :class="showHistory ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
          {{ showHistory ? 'Verlauf verbergen' : 'Verlauf anzeigen (' + history.length + ')' }}
        </button>

        <div v-if="showHistory" class="list-group shadow-sm">
          <div v-for="(item, idx) in history.slice(0, 10)" :key="idx"
            class="list-group-item list-group-item-action py-2">
            <div class="d-flex justify-content-between align-items-center">
              <div class="overflow-hidden">
                <div class="fw-bold text-truncate">{{ item.exercise_title || 'Übung #' + item.exercise }}</div>
                <small class="text-muted">{{ formatDate(item.completed_at) }}</small>
              </div>
              <span class="badge ms-2" :class="getScoreBadgeClass(item.score)">
                {{ Math.round(item.score) }}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { api } from '../utils/api'

// === Props ===
// Родитель (App.vue) должен передать ID текущего пользователя
const props = defineProps({
  studentId: {
    type: [Number, String],
    required: true
  }
})

// === State ===
const progress = ref(null)
const history = ref([])
const isLoading = ref(false)
const error = ref(null)
const showHistory = ref(false)

// === Methods ===
const loadData = async () => {
  if (!props.studentId) return

  isLoading.value = true
  error.value = null

  try {
    // Используем методы из api.js
    // Примечание: api.js должен принимать ID
    const [progData, histData] = await Promise.all([
      api.getStudentProgress(props.studentId),
      api.getStudentHistory(props.studentId)
    ])

    progress.value = progData
    // История может прийти как объект { results: [...] } или массив. Нормализуем.
    history.value = Array.isArray(histData) ? histData : (histData.results || [])

  } catch (err) {
    console.error('Error loading progress:', err)
    error.value = 'Konnte Fortschrittsdaten nicht laden.'
    // Не сбрасываем прогресс при ошибке, чтобы показать старые данные, если они есть
    if (!progress.value) progress.value = null
  } finally {
    isLoading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('de-DE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

const getProgressBarClass = (score) => {
  if (!score) return 'bg-secondary'
  if (score >= 80) return 'bg-success'
  if (score >= 60) return 'bg-warning'
  return 'bg-danger'
}

const getScoreBadgeClass = (score) => {
  if (!score) return 'bg-secondary'
  if (score >= 80) return 'bg-success'
  if (score >= 60) return 'bg-warning'
  return 'bg-danger'
}

// Watch за изменением ID (если вдруг пользователь сменился)
watch(() => props.studentId, (newId) => {
  if (newId) loadData()
})

onMounted(() => {
  if (props.studentId) loadData()
})
</script>

<style scoped>
.student-progress {
  font-size: 0.9rem;
}

.stat-number {
  font-size: 1.4rem;
  font-weight: 700;
}

.stat-label {
  font-size: 0.7rem;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.progress-container {
  animation: fadeIn 0.4s ease-out;
}

.list-group-item {
  border-left: none;
  border-right: none;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
