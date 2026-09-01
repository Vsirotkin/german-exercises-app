<!-- src/components/ExerciseList.vue -->
<template>
  <div class="exercise-list">
    <!-- Заголовок -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2><i class="bi bi-list-task me-2"></i>Verfügbare Übungen</h2>
      <span class="badge bg-primary">{{ exercises.length }} Übungen</span>
    </div>

    <!-- Список карточек -->
    <div class="row">
      <div v-for="ex in exercises" :key="ex.id" class="col-md-6 col-lg-4 mb-4">
        <div class="card h-100 exercise-card shadow-sm" :class="getCardClass(ex.status)"
          :title="ex.is_locked ? 'Vorherige Übung mit &lt; 50% abgeschlossen. Erst wiederholen!' : ''"
          :style="ex.status === 'mastered' ? { animation: 'goldPulse 2s infinite' } : {}">
          <!-- 🎖 Бейдж Perfekt! -->
          <div v-if="ex.status === 'mastered'" class="perfekt-badge">
            🏆 Perfekt!
          </div>

          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h5 class="card-title mb-0">{{ ex.title }}</h5>
              <div class="d-flex align-items-center gap-2">
                <span class="badge bg-primary">A1</span>
                <span class="status-icon" :title="getStatusTitle(ex.status)">
                  <i v-if="ex.status === 'mastered'" class="bi bi-trophy-fill text-gold"></i>
                  <i v-else-if="ex.status === 'completed'" class="bi bi-check-circle-fill text-success"></i>
                  <i v-else-if="ex.status === 'review_recommended'"
                    class="bi bi-exclamation-circle-fill text-warning"></i>
                  <i v-else-if="ex.status === 'needs_review'" class="bi bi-x-circle-fill text-danger"></i>
                </span>
              </div>
            </div>

            <p class="card-text text-muted small mb-3">{{ ex.topics?.join(', ') || '' }}</p>

            <!-- 📊 Прогресс-бар -->
            <div v-if="ex.score !== null && ex.score !== undefined" class="mb-3">
              <div class="d-flex justify-content-between small mb-1">
                <span class="text-muted">Fortschritt</span>
                <span class="fw-bold" :class="getScoreClass(ex.status)">{{ ex.score }}%</span>
              </div>
              <div class="progress" style="height: 6px;">
                <div class="progress-bar"
                  :class="ex.status === 'mastered' ? 'perfekt-progress' : 'bg-' + getStatusColor(ex.status)"
                  :style="{ width: ex.score + '%' }"></div>
              </div>
            </div>

            <div class="d-grid">
              <button class="btn" :class="ex.is_locked ? 'btn-secondary' : 'btn-primary'" :disabled="ex.is_locked"
                @click="!ex.is_locked && handleStart(ex)">
                <i :class="ex.is_locked ? 'bi bi-lock-fill' : 'bi bi-play-circle'"></i>
                {{ ex.is_locked ? 'Gesperrt' : 'Übung starten' }}
              </button>
            </div>
          </div>

          <div class="card-footer bg-transparent border-top-0 pt-0">
            <div class="d-flex justify-content-between align-items-center small text-muted">
              <span><i class="bi bi-translate me-1"></i>german</span>
              <span class="text-uppercase" style="font-size: 0.7rem;">{{ (ex.exercise_type || '').replace('_', ' ')
                }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2">Lade Übungen...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/utils/api'  // ✅ Именованный импорт, как в твоём api.js

const exercises = ref([])
const loading = ref(true)

// ✅ Загрузка через ПРАВИЛЬНЫЙ метод из api.js
const loadExercises = async () => {
  try {
    const data = await api.getExercisesList()  // ← вот этот метод!
    exercises.value = data
    console.log('✅ Exercises loaded:', data.length)
  } catch (err) {
    console.error('❌ Failed to load exercises:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadExercises()
})

// ✅ Эмитим в формате, который ждёт App.vue: { topicName, exerciseId }
const emit = defineEmits(['exercise-select'])

const handleStart = (ex) => {
  emit('exercise-select', {
    topicName: ex.topics?.[0] || '',
    exerciseId: ex.id
  })
}

// === Хелперы для стилей ===
const getCardClass = (status) => {
  const map = {
    mastered: 'border-gold',
    completed: 'border-success',
    review_recommended: 'border-warning',
    needs_review: 'border-danger',
    not_started: ''
  }
  return map[status] || ''
}

const getStatusColor = (status) => {
  const map = {
    mastered: 'gold',
    completed: 'success',
    review_recommended: 'warning',
    needs_review: 'danger',
    not_started: 'secondary'
  }
  return map[status] || 'secondary'
}

const getScoreClass = (status) => {
  const map = {
    mastered: 'text-gold',
    completed: 'text-success',
    review_recommended: 'text-warning',
    needs_review: 'text-danger'
  }
  return map[status] || 'text-muted'
}

const getStatusTitle = (status) => {
  const map = {
    mastered: 'Perfekt abgeschlossen! 🏆',
    completed: 'Abgeschlossen! ✅',
    review_recommended: 'Wiederholung empfohlen ⚠',
    needs_review: 'Nochmal üben ❌',
    not_started: 'Noch nicht begonnen'
  }
  return map[status] || ''
}
</script>

<style scoped>
.exercise-card {
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.exercise-card:hover:not(.locked) {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1) !important;
}

/* 🟡 Золотые стили */
.exercise-card.border-gold {
  border-color: #FFD700 !important;
}

.text-gold {
  color: #D4AF37 !important;
}

.bg-gold {
  background-color: #FFD700 !important;
}

.perfekt-progress {
  background: linear-gradient(90deg, #FFD700, #FFA500) !important;
  transition: all 0.3s ease;
}

.perfekt-progress:hover {
  transform: scaleY(1.2);
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
}

/* 🎖 Бейдж */
.perfekt-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #000;
  font-weight: bold;
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 20px;
  box-shadow: 0 2px 6px rgba(255, 215, 0, 0.4);
  z-index: 10;
  transform: rotate(5deg);
}

/* ✨ Анимация свечения для 100% */
@keyframes goldPulse {

  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.4);
  }

  50% {
    box-shadow: 0 0 0 8px rgba(255, 215, 0, 0);
  }
}
</style>
