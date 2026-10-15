<template>
  <div class="min-h-screen bg-gray-50">
    <div class="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">

      <!-- Loading -->
      <div v-if="loading" class="rounded-xl bg-white p-8 text-center shadow-sm">
        <p class="text-gray-500">Übung wird geladen...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="rounded-xl border border-red-200 bg-red-50 p-6">
        <h2 class="text-lg font-semibold text-red-800">
          Fehler
        </h2>
        <p class="mt-2 text-red-700">
          {{ error }}
        </p>

        <button type="button"
          class="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          @click="router.back()">
          Zurück
        </button>
      </div>

      <!-- Exercise -->
      <div v-else-if="exercise && !finished">

        <!-- Header -->
        <div class="mb-6">
          <button type="button" class="mb-4 text-sm text-gray-500 hover:text-gray-900"
            @click="router.push({ name: 'exercises' })">
            ← Zurück zu den Übungen
          </button>

          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-sm font-medium text-blue-600">
                {{ exercise.topics?.join(', ') }}
              </p>

              <h1 class="mt-1 text-2xl font-bold text-gray-900">
                {{ exercise.title }}
              </h1>
            </div>

            <div class="shrink-0 rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-600">
              {{ currentIndex + 1 }} / {{ cards.length }}
            </div>
          </div>
        </div>

        <!-- Progress -->
        <div class="mb-8 h-2 overflow-hidden rounded-full bg-gray-200">
          <div class="h-full bg-blue-600 transition-all duration-300" :style="{ width: `${progress}%` }"></div>
        </div>

        <!-- Card -->
        <div class="rounded-2xl bg-white p-6 shadow-sm sm:p-8">

          <div class="text-center">
            <p class="text-sm text-gray-500">
              Wähle die richtige Übersetzung
            </p>

            <h2 class="mt-4 text-3xl font-bold text-gray-900">
              {{ currentCard.word }}
            </h2>
          </div>

          <!-- Answers -->
          <div class="mt-8 grid gap-3">
            <button v-for="answer in currentAnswers" :key="answer" type="button" :disabled="selectedAnswer !== null"
              class="w-full rounded-xl border px-5 py-4 text-left text-base font-medium transition"
              :class="getAnswerClass(answer)" @click="selectAnswer(answer)">
              {{ answer }}
            </button>
          </div>

          <!-- Feedback -->
          <div v-if="selectedAnswer !== null" class="mt-6 rounded-xl p-4" :class="selectedAnswer === currentCard.correct_translation
              ? 'bg-green-50 text-green-800'
              : 'bg-red-50 text-red-800'
            ">
            <p class="font-semibold">
              {{
                selectedAnswer === currentCard.correct_translation
                  ? 'Richtig! ✓'
                  : 'Leider falsch.'
              }}
            </p>

            <p v-if="selectedAnswer !== currentCard.correct_translation" class="mt-1">
              Richtige Antwort:
              <strong>{{ currentCard.correct_translation }}</strong>
            </p>
          </div>

          <!-- Next -->
          <div v-if="selectedAnswer !== null" class="mt-6 flex justify-end">
            <button type="button" class="rounded-xl bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700"
              @click="nextCard">
              {{ isLastCard ? 'Ergebnis anzeigen' : 'Nächste Karte →' }}
            </button>
          </div>

        </div>
      </div>

      <!-- Result -->
      <div v-else-if="finished" class="rounded-2xl bg-white p-8 text-center shadow-sm">
        <p class="text-sm font-medium text-blue-600">
          Übung abgeschlossen
        </p>

        <h1 class="mt-2 text-3xl font-bold text-gray-900">
          Fertig! 🎉
        </h1>

        <div class="mx-auto mt-8 max-w-sm rounded-2xl bg-gray-50 p-6">
          <p class="text-sm text-gray-500">
            Ergebnis
          </p>

          <p class="mt-2 text-5xl font-bold text-gray-900">
            {{ correctAnswers }} / {{ cards.length }}
          </p>

          <p class="mt-2 text-gray-600">
            {{ percentage }}% richtig
          </p>
        </div>

        <button type="button" class="mt-8 rounded-xl bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700"
          @click="router.push({ name: 'exercises' })">
          Zurück zu den Übungen
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/utils/api'

const route = useRoute()
const router = useRouter()

const exercise = ref(null)
const loading = ref(true)
const error = ref(null)

const currentIndex = ref(0)
const selectedAnswer = ref(null)
const correctAnswers = ref(0)
const finished = ref(false)

const cards = computed(() => exercise.value?.vocabulary_cards || [])

const currentCard = computed(() => {
  return cards.value[currentIndex.value]
})

const isLastCard = computed(() => {
  return currentIndex.value === cards.value.length - 1
})

const progress = computed(() => {
  if (!cards.value.length) return 0
  return ((currentIndex.value + 1) / cards.value.length) * 100
})

const percentage = computed(() => {
  if (!cards.value.length) return 0
  return Math.round((correctAnswers.value / cards.value.length) * 100)
})

const currentAnswers = computed(() => {
  if (!currentCard.value) return []

  return [
    currentCard.value.correct_translation,
    currentCard.value.distractor_1,
    currentCard.value.distractor_2,
    currentCard.value.distractor_3,
  ].sort(() => Math.random() - 0.5)
})

function selectAnswer(answer) {
  if (selectedAnswer.value !== null) return

  selectedAnswer.value = answer

  if (answer === currentCard.value.correct_translation) {
    correctAnswers.value++
  }
}

function getAnswerClass(answer) {
  if (selectedAnswer.value === null) {
    return 'border-gray-200 bg-white text-gray-800 hover:border-blue-400 hover:bg-blue-50'
  }

  if (answer === currentCard.value.correct_translation) {
    return 'border-green-500 bg-green-50 text-green-800'
  }

  if (answer === selectedAnswer.value) {
    return 'border-red-500 bg-red-50 text-red-800'
  }

  return 'border-gray-200 bg-gray-50 text-gray-400'
}

function nextCard() {
  if (isLastCard.value) {
    finished.value = true
    return
  }

  currentIndex.value++
  selectedAnswer.value = null
}

async function loadExercise() {
  loading.value = true
  error.value = null

  try {
    const id = route.params.id
    exercise.value = await api.getExerciseFull(id)
  } catch (err) {
    console.error(err)
    error.value = 'Die Übung konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

onMounted(loadExercise)
</script>
