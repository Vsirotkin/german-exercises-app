
<template>
  <div class="min-h-screen bg-gray-50">
    <div class="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <!-- Loading -->
      <div
        v-if="loading"
        class="rounded-xl bg-white p-8 text-center shadow-sm"
      >
        <p class="text-gray-500">Übung wird geladen...</p>
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="rounded-xl border border-red-200 bg-red-50 p-6"
      >
        <h2 class="text-lg font-semibold text-red-800">Fehler</h2>
        <p class="mt-2 text-red-700">{{ error }}</p>

        <button
          type="button"
          class="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          @click="router.push({ name: 'exercises' })"
        >
          Zurück zu den Übungen
        </button>
      </div>

      <!-- Exercise -->
      <div v-else-if="exercise && !finished">
        <div class="mb-6">
          <button
            type="button"
            class="mb-4 text-sm text-gray-500 hover:text-gray-900"
            @click="router.push({ name: 'exercises' })"
          >
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

            <div
              class="shrink-0 rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-600"
            >
              {{ currentIndex + 1 }} / {{ cards.length }}
            </div>
          </div>
        </div>

        <!-- Progress -->
        <div class="mb-8 h-2 overflow-hidden rounded-full bg-gray-200">
          <div
            class="h-full bg-blue-600 transition-all duration-300"
            :style="{ width: `${progress}%` }"
          />
        </div>

        <!-- Question -->
        <div class="rounded-2xl bg-white p-6 shadow-sm sm:p-8">
          <div class="text-center">
            <p class="text-sm text-gray-500">
              Wähle die richtige Übersetzung
            </p>

            <h2 class="mt-4 text-3xl font-bold text-gray-900">
              {{ currentCard.prompt }}
            </h2>
          </div>

          <!-- Options from backend -->
          <div class="mt-8 grid gap-3">
            <button
              v-for="option in currentCard.options"
              :key="option.id"
              type="button"
              class="w-full rounded-xl border px-5 py-4 text-left text-base font-medium transition"
              :class="
                selectedOptionId === option.id
                  ? 'border-blue-500 bg-blue-50 text-blue-800'
                  : 'border-gray-200 bg-white text-gray-800 hover:border-blue-400 hover:bg-blue-50'
              "
              @click="selectOption(option.id)"
            >
              {{ option.text }}
            </button>
          </div>

          <p class="mt-5 text-sm text-gray-500">
            Die Antwort wird nach Abschluss der Übung vom Server überprüft.
          </p>

          <!-- Navigation -->
          <div class="mt-6 flex justify-end">
            <button
              type="button"
              :disabled="!selectedOptionId"
              class="rounded-xl bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              @click="nextCard"
            >
              {{ isLastCard ? 'Übung abschließen' : 'Nächste Karte →' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Submitting -->
      <div
        v-else-if="submitting"
        class="rounded-xl bg-white p-8 text-center shadow-sm"
      >
        <p class="text-gray-500">Antworten werden überprüft...</p>
      </div>

      <!-- Result -->
      <div
        v-else-if="finished && result"
        class="rounded-2xl bg-white p-6 shadow-sm sm:p-8"
      >
        <div class="text-center">
          <p class="text-sm font-medium text-blue-600">
            Übung abgeschlossen
          </p>

          <h1 class="mt-2 text-3xl font-bold text-gray-900">
            Fertig! 🎉
          </h1>

          <div class="mx-auto mt-8 max-w-sm rounded-2xl bg-gray-50 p-6">
            <p class="text-sm text-gray-500">Ergebnis</p>

            <p class="mt-2 text-5xl font-bold text-gray-900">
              {{ result.score }} / {{ result.max_score }}
            </p>

            <p class="mt-2 text-gray-600">
              {{ result.percentage }}% richtig
            </p>
          </div>
        </div>

        <!-- Per-question feedback from backend -->
        <div class="mt-8 space-y-3">
          <h2 class="text-lg font-semibold text-gray-900">
            Deine Antworten
          </h2>

          <div
            v-for="card in cards"
            :key="card.id"
            class="rounded-xl border p-4"
            :class="
              resultByItemId[card.id]?.is_correct
                ? 'border-green-200 bg-green-50'
                : 'border-red-200 bg-red-50'
            "
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <p class="font-semibold text-gray-900">
                  {{ card.prompt }}
                </p>

                <p class="mt-1 text-sm text-gray-700">
                  Deine Antwort:
                  {{ selectedOptionText(card) }}
                </p>
              </div>

              <span
                class="shrink-0 text-sm font-semibold"
                :class="
                  resultByItemId[card.id]?.is_correct
                    ? 'text-green-700'
                    : 'text-red-700'
                "
              >
                {{
                  resultByItemId[card.id]?.is_correct
                    ? 'Richtig ✓'
                    : 'Falsch ✗'
                }}
              </span>
            </div>
          </div>
        </div>

        <div class="mt-8 flex justify-center">
          <button
            type="button"
            class="rounded-xl bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700"
            @click="router.push({ name: 'exercises' })"
          >
            Zurück zu den Übungen
          </button>
        </div>
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
const submitting = ref(false)
const error = ref(null)
const finished = ref(false)

const currentIndex = ref(0)
const answers = ref({})
const result = ref(null)

const cards = computed(
  () => exercise.value?.vocabulary_items || [],
)

const currentCard = computed(
  () => cards.value[currentIndex.value],
)

const selectedOptionId = computed(
  () => {
    const card = currentCard.value
    return card ? answers.value[String(card.id)] || null : null
  },
)

const isLastCard = computed(
  () => currentIndex.value === cards.value.length - 1,
)

const progress = computed(
  () => cards.value.length
    ? ((currentIndex.value + 1) / cards.value.length) * 100
    : 0,
)

const resultByItemId = computed(() => {
  const lookup = {}

  for (const item of result.value?.results || []) {
    lookup[String(item.item_id)] = item
  }

  return lookup
})

function selectOption(optionId) {
  if (!currentCard.value || submitting.value) return

  answers.value = {
    ...answers.value,
    [String(currentCard.value.id)]: optionId,
  }
}

function selectedOptionText(card) {
  const selectedId = answers.value[String(card.id)]

  return card.options.find(
    option => option.id === selectedId,
  )?.text || 'Keine Antwort'
}

async function nextCard() {
  if (!selectedOptionId.value || submitting.value) return

  if (!isLastCard.value) {
    currentIndex.value++
    return
  }

  await submitAnswers()
}

async function submitAnswers() {
  submitting.value = true
  error.value = null

  try {
    const payload = {
      exercise_id: exercise.value.id,
      answers: cards.value.map(card => ({
        item_id: card.id,
        answer: answers.value[String(card.id)],
      })),
    }

    // The backend evaluates and saves the result.
    result.value = await api.saveExerciseResult(payload)
    finished.value = true
  } catch (err) {
    console.error('Exercise submission failed:', err)

    error.value =
      err.response?.data?.error?.message
      || 'Die Antworten konnten nicht überprüft werden. Bitte versuche es erneut.'
  } finally {
    submitting.value = false
  }
}

async function loadExercise() {
  loading.value = true
  error.value = null

  try {
    const id = route.params.id
    const data = await api.getExerciseFull(id)

    if (!data || !Array.isArray(data.vocabulary_items)) {
      throw new Error('Unexpected exercise response structure.')
    }

    if (data.exercise_type !== 'vocabulary_drill') {
      throw new Error(
        `Dieser Übungstyp wird auf dieser Seite noch nicht unterstützt: ${data.exercise_type}`,
      )
    }

    if (data.vocabulary_items.length === 0) {
      throw new Error('Diese Übung enthält noch keine Aufgaben.')
    }

    exercise.value = data
  } catch (err) {
    console.error('Exercise loading failed:', err)

    error.value =
      err.response?.data?.detail
      || err.message
      || 'Die Übung konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

onMounted(loadExercise)
</script>
