<!-- src/components/VocabularyDrill.vue -->
<template>
  <div class="vocabulary-drill container max-w-2xl mx-auto p-4">

    <!-- Экран упражнения -->
    <div v-if="!isCompleted && currentCardIndex < cards.length" class="card shadow-sm">
      <div class="card-body text-center py-5">
        <!-- Прогресс бар -->
        <div class="progress mb-4" style="height: 6px;">
          <div class="progress-bar bg-primary" :style="{ width: progressPercent + '%' }"></div>
        </div>

        <h2 class="display-4 fw-bold mb-5 text-primary">{{ currentCard.word }}</h2>

        <div class="row g-3">
          <div class="col-md-6" v-for="(option, idx) in shuffledOptions" :key="idx">
            <button @click="selectAnswer(option)" class="btn btn-outline-primary w-100 py-3 fs-5 option-btn"
              :class="getButtonClass(option)" :disabled="hasAnswered">
              {{ option }}
            </button>
          </div>
        </div>

        <div class="mt-4 text-muted">
          Вопрос {{ currentCardIndex + 1 }} из {{ cards.length }}
        </div>
      </div>
    </div>

    <!-- Экран результатов -->
    <div v-else-if="isCompleted && results" class="card shadow-sm border-0">
      <div class="card-body text-center py-5">
        <h2 class="mb-4">
          <i class="bi"
            :class="results.score >= 70 ? 'bi-trophy-fill text-warning' : 'bi-clipboard-check-fill text-primary'"></i>
          Ergebnis
        </h2>

        <div class="display-1 fw-bold mb-3" :class="scoreColorClass">
          {{ Math.round(results.score) }}%
        </div>

        <p class="lead mb-4">
          Richtig: <strong>{{ results.correctCount }}</strong> / {{ cards.length }}
        </p>

        <!-- Список ошибок -->
        <div v-if="results.wrongWords.length > 0" class="text-start bg-light p-3 rounded mb-4">
          <h5 class="small text-uppercase text-muted mb-3">Wiederholung empfohlen:</h5>
          <ul class="list-unstyled mb-0">
            <li v-for="item in results.wrongWords" :key="item.word" class="mb-2">
              <span class="text-danger fw-bold">{{ item.word }}</span>
              <i class="bi bi-arrow-right mx-2 text-muted"></i>
              <span class="text-success">{{ item.correct }}</span>
            </li>
          </ul>
        </div>

        <div class="d-grid gap-2 d-md-flex justify-content-md-center">
          <button @click="emit('back-to-list')" class="btn btn-outline-secondary btn-lg px-4">
            <i class="bi bi-arrow-left me-2"></i>Zurück zur Liste
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '@/utils/api'

const props = defineProps({
  exercise: { type: Object, required: true }
})

const emit = defineEmits(['back-to-list'])

// Состояния
const currentCardIndex = ref(0)
const userAnswers = ref(new Map()) // Map<cardId, { selected, isCorrect }>
const isCompleted = ref(false)
const results = ref(null)
const hasAnswered = ref(false) // Блокировка кнопок после выбора

// Данные
const cards = computed(() => props.exercise.vocabulary_cards || [])

const currentCard = computed(() => cards.value[currentCardIndex.value])

const progressPercent = computed(() => {
  return ((currentCardIndex.value) / cards.value.length) * 100
})

const shuffledOptions = computed(() => {
  if (!currentCard.value) return []
  const options = [
    currentCard.value.correct_translation,
    currentCard.value.distractor_1,
    currentCard.value.distractor_2,
    currentCard.value.distractor_3
  ].filter(Boolean) // Убираем пустые, если есть

  // Алгоритм Фишера-Йетса для честного перемешивания
  const arr = [...options]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
      ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr
})

// === Логика ===

const selectAnswer = (selectedOption) => {
  if (hasAnswered.value || !currentCard.value) return

  const card = currentCard.value
  const isCorrect = selectedOption === card.correct_translation

  // Сохраняем ответ
  userAnswers.value.set(card.id, {
    selected: selectedOption,
    isCorrect: isCorrect,
    correct: card.correct_translation
  })

  hasAnswered.value = true

  // Небольшая задержка, чтобы пользователь увидел цвет, затем переход
  setTimeout(() => {
    if (currentCardIndex.value < cards.value.length - 1) {
      currentCardIndex.value++
      hasAnswered.value = false
    } else {
      finishExercise()
    }
  }, 600)
}

const getButtonClass = (option) => {
  if (!hasAnswered.value) return ''

  const card = currentCard.value
  const answer = userAnswers.value.get(card.id)

  if (!answer) return ''

  // Если это выбранный пользователем вариант
  if (option === answer.selected) {
    return answer.isCorrect ? 'btn-success' : 'btn-danger'
  }

  // Если пользователь ошибся, подсвечиваем правильный зеленым
  if (!answer.isCorrect && option === card.correct_translation) {
    return 'btn-success'
  }

  return 'btn-outline-primary' // Остальные бледные
}

const finishExercise = () => {
  isCompleted.value = true

  let correctCount = 0
  const wrongWords = []

  cards.value.forEach(card => {
    const answer = userAnswers.value.get(card.id)
    if (answer && answer.isCorrect) {
      correctCount++
    } else if (answer) {
      wrongWords.push({ word: card.word, correct: answer.correct })
    }
  })

  // 👇 Считаем процент ТОЛЬКО для отображения на фронте
  const percentage = cards.value.length ? (correctCount / cards.value.length) * 100 : 0

  results.value = {
    score: percentage,  // Для UI: показываем 75%
    correctCount,       // Для бэка: 3 из 4
    wrongWords
  }

  // 👇 Передаём correctCount (сырые баллы) на бэкенд!
  saveResult(correctCount)
}

// 👇 Функция принимает rawScore (сырые баллы), а не процент
const saveResult = async (rawScore) => {
  try {
    await api.saveExerciseResult({
      exercise: props.exercise.id,
      score: rawScore,              // ✅ Теперь это 3 (балла), а не 75 (%)
      total_questions: cards.value.length  // 4 вопроса
      // Если нужно, можно добавить details: { answers: [...] }
    })
  } catch (error) {
    console.error('Fehler beim Speichern:', error)
  }
}

const scoreColorClass = computed(() => {
  if (!results.value) return 'text-primary'
  if (results.value.score >= 80) return 'text-success'
  if (results.value.score >= 60) return 'text-warning'
  return 'text-danger'
})

</script>

<style scoped>
.option-btn {
  transition: all 0.2s ease;
  font-weight: 500;
}

.option-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.max-w-2xl {
  max-width: 42rem;
}
</style>
