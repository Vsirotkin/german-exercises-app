<!-- src/components/GapFill.vue -->
<template>
  <div v-if="!exercise || !exercise.sentences" class="alert alert-warning">
    Keine Daten verfügbar.
  </div>

  <div v-else>
    <div v-for="sentence in exercise.sentences" :key="sentence.id" class="sentence-card card mb-3 shadow-sm">
      <div class="card-body">
        <div class="sentence-display mb-3">
          <span v-for="(part, index) in getSentenceParts(sentence)" :key="index" class="sentence-part">
            <template v-if="part.type === 'text'">
              {{ part.content }}
            </template>

            <template v-else-if="part.type === 'gap'">
              <select v-model="userAnswers[part.key]" class="form-select gap-select d-inline-block"
                style="width: auto; min-width: 140px;" :class="getSelectClass(part.key)" :disabled="hasSubmitted">
                <option value="" disabled>--- wählen ---</option>
                <option v-for="opt in part.options" :key="opt" :value="opt">
                  {{ opt }}
                </option>
              </select>
            </template>
          </span>
        </div>

        <div class="text-muted small">
          <i class="bi bi-info-circle me-1"></i>
          Satz {{ sentence.order || sentence.id }}
        </div>
      </div>
    </div>

    <div class="action-bar mt-4">
      <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
        <div class="status">
          <span class="badge" :class="getCompletionBadgeClass()">
            {{ getCompletionStatus() }}
          </span>
        </div>

        <div class="buttons" v-if="!hasSubmitted">
          <button @click="emit('back-to-list')" class="btn btn-outline-secondary me-2">
            <i class="bi bi-arrow-left me-2"></i>Zurück
          </button>
          <button @click="resetAnswers" class="btn btn-outline-secondary me-2">
            <i class="bi bi-arrow-clockwise me-2"></i>Zurücksetzen
          </button>
          <button @click="checkAnswers" class="btn btn-primary" :disabled="!isAllFilled">
            <i class="bi bi-check-circle me-2"></i>Überprüfen
          </button>
        </div>

        <div class="buttons" v-else>
          <button @click="emit('back-to-list')" class="btn btn-outline-secondary">
            <i class="bi bi-arrow-left me-2"></i>Zurück zur Liste
          </button>
        </div>
      </div>
    </div>

    <div v-if="hasSubmitted && checkResults" class="results-card card mt-4" :class="resultsCardClass">
      <div class="card-body">
        <h5 class="card-title">
          <i class="bi" :class="resultsIconClass"></i>
          Ergebnis: {{ Math.round(checkResults.percentage) }}%
        </h5>
        <p class="card-text">{{ getResultsMessage() }}</p>

        <div class="progress mb-3" style="height: 25px;">
          <div class="progress-bar" :class="progressBarClass" :style="{ width: checkResults.percentage + '%' }">
            {{ Math.round(checkResults.percentage) }}%
          </div>
        </div>

        <div v-if="checkResults.percentage < 100" class="alert alert-light border">
          <small class="text-muted">
            💡 <strong>Tipp:</strong> Wiederholen Sie das Thema
            <span class="fw-bold">{{ exercise.topics?.[0] || 'Deutsch' }}</span>.
          </small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '@/utils/api'

const props = defineProps({
  exercise: { type: Object, required: true },
  retryStatus: { type: Object, default: () => ({}) }
})

const emit = defineEmits(['back-to-list', 'answers-checked'])

const userAnswers = ref({})
const checkResults = ref(null)
const hasSubmitted = ref(false)

const getSentenceParts = (sentence) => {
  if (!sentence?.text) return []

  const parts = []
  const gapOptions = sentence.gap_options || []
  const sortedGaps = [...gapOptions].sort((a, b) => a.placeholder_index - b.placeholder_index)

  if (sortedGaps.length === 0) {
    return [{ type: 'text', content: sentence.text }]
  }

  const marker = '___'
  const partsTemp = sentence.text.split(marker)

  if (partsTemp.length <= 1) {
    return [{ type: 'text', content: sentence.text }]
  }

  partsTemp.forEach((partText, i) => {
    if (partText?.trim()) {
      parts.push({ type: 'text', content: partText })
    }

    if (i < partsTemp.length - 1) {
      const gapData = sortedGaps[i]
      if (!gapData) return

      parts.push({
        type: 'gap',
        key: `s${sentence.id}_g${i}`,
        options: gapData.options || [],
        correctAnswer: gapData.correct_answer
      })
    }
  })

  return parts
}

const isAllFilled = computed(() => {
  if (!props.exercise) return false

  let totalGaps = 0
  props.exercise.sentences.forEach(s => {
    totalGaps += getSentenceParts(s).filter(p => p.type === 'gap').length
  })

  const filledCount = Object.keys(userAnswers.value).length
  return filledCount === totalGaps && totalGaps > 0
})

const getCompletionStatus = () => {
  if (!props.exercise) return '0/0'

  let total = 0
  props.exercise.sentences.forEach(s => {
    total += getSentenceParts(s).filter(p => p.type === 'gap').length
  })

  const filled = Object.keys(userAnswers.value).length
  return `${filled}/${total}`
}

const getCompletionBadgeClass = () => {
  const status = getCompletionStatus()
  if (status.startsWith('0/')) return 'bg-secondary'

  const [f, t] = status.split('/')
  return parseInt(f) < parseInt(t) ? 'bg-warning' : 'bg-success'
}

const checkAnswers = () => {
  if (!isAllFilled.value) return

  let correctCount = 0
  let totalGaps = 0
  const resultsMap = {}

  props.exercise.sentences.forEach(sentence => {
    getSentenceParts(sentence).forEach(part => {
      if (part.type === 'gap') {
        totalGaps++
        const userVal = userAnswers.value[part.key]
        const isCorrect = userVal === part.correctAnswer

        if (isCorrect) correctCount++
        resultsMap[part.key] = { isCorrect, userVal, correctVal: part.correctAnswer }
      }
    })
  })

  // 👇 Считаем процент ТОЛЬКО для отображения на фронте
  const percentage = totalGaps ? (correctCount / totalGaps) * 100 : 0

  checkResults.value = {
    percentage,           // Для UI: показываем 75%
    correctCount,         // Для бэка: 3 из 4
    totalGaps,            // Для бэка: всего вопросов
    details: resultsMap
  }

  hasSubmitted.value = true

  // 👇 Отправляем сырые баллы на бэкенд
  saveResult(correctCount, totalGaps)

  // 👇 Сохраняем обратную совместимость: отправляем процент для родительского UI (если нужно)
  emit('answers-checked', percentage)
}

// 👇 Новая функция: сохраняет результат с сырыми баллами
const saveResult = async (correctCount, totalGaps) => {
  try {
    await api.saveExerciseResult({
      exercise: props.exercise.id,
      score: correctCount,        // ✅ Сырые баллы (например, 3)
      total_questions: totalGaps  // ✅ Всего вопросов (например, 4)
      // При необходимости можно добавить details: checkResults.value.details
    })
  } catch (error) {
    console.error('Fehler beim Speichern:', error)
  }
}

const resetAnswers = () => {
  userAnswers.value = {}
  checkResults.value = null
  hasSubmitted.value = false
}

const getSelectClass = (key) => {
  if (!hasSubmitted.value || !checkResults.value) return ''
  const res = checkResults.value.details[key]
  if (!res) return ''
  return res.isCorrect ? 'is-valid' : 'is-invalid'
}

const resultsCardClass = computed(() => {
  if (!checkResults.value) return ''
  return checkResults.value.percentage >= 70 ? 'border-success' : 'border-danger'
})

const resultsIconClass = computed(() => {
  if (!checkResults.value) return 'bi-question-circle'
  return checkResults.value.percentage >= 70
    ? 'bi-check-circle-fill text-success'
    : 'bi-x-circle-fill text-danger'
})

const getResultsMessage = () => {
  if (!checkResults.value) return ''

  const s = Math.round(checkResults.value.percentage)
  if (s === 100) return 'Perfekt! Alle Antworten sind richtig! 🎉'
  if (s >= 80) return 'Sehr gut gemacht! 👍'
  if (s >= 60) return 'Gut, aber es geht noch besser.'
  return 'Üben Sie weiter, um sich zu verbessern.'
}

const progressBarClass = computed(() => {
  if (!checkResults.value) return 'bg-secondary'

  const s = checkResults.value.percentage
  if (s >= 80) return 'bg-success'
  if (s >= 60) return 'bg-warning'
  return 'bg-danger'
})
</script>

<style scoped>
.sentence-display {
  font-size: 1.2rem;
  line-height: 2.2;
}

.sentence-part {
  margin: 0 2px;
  white-space: pre-wrap;
}

.gap-select {
  display: inline-block;
  vertical-align: middle;
  font-weight: 500;
}

.sentence-card {
  border-left: 5px solid #0d6efd;
}

.results-card {
  border-left-width: 5px;
  animation: fadeIn 0.5s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
