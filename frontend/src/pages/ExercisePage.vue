<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/utils/api'

const route = useRoute()

const exercise = ref(null)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const result = ref(null)
const currentIndex = ref(0)

const answers = reactive({})
const checkedAnswers = reactive({})
const checkingAnswerId = ref(null)

const exerciseType = computed(() => exercise.value?.exercise_type)

const cards = computed(() => {
  if (!exercise.value) return []

  switch (exerciseType.value) {
    case 'vocabulary_drill':
      return exercise.value.vocabulary_items || []
    case 'multiple_choice':
      return exercise.value.multiple_choice_items || []
    case 'dropdown':
      return exercise.value.dropdown_items || []
    case 'gap_fill':
      return exercise.value.gap_fill_items || []
    case 'sentence_builder':
      return exercise.value.sentence_builder_items || []
    default:
      return []
  }
})

const currentCard = computed(() => cards.value[currentIndex.value])

const isLastQuestion = computed(
  () => currentIndex.value >= cards.value.length - 1,
)

const resultByItemId = computed(() => {
  const map = {}

  for (const item of result.value?.results || []) {
    map[String(item.item_id)] = item
  }

  return map
})

function getSelectedOption(itemId, partId) {
  const selectedId = answers[itemId]?.[String(partId)]

  if (selectedId === undefined || selectedId === '') return null

  const item = (exercise.value?.dropdown_items || []).find(
    entry => String(entry.id) === String(itemId),
  )

  const part = item?.parts?.find(
    entry => String(entry.id) === String(partId),
  )

  return part?.options?.find(
    option => String(option.id) === String(selectedId),
  ) || null
}

function getOptionText(item, optionId) {
  return item.options?.find(
    option => String(option.id) === String(optionId),
  )?.text || ''
}

async function selectMultipleChoiceOption(card, optionId) {
  if (checkedAnswers[card.id] || checkingAnswerId.value !== null) return

  answers[card.id] = String(optionId)
  checkingAnswerId.value = String(card.id)
  error.value = ''

  try {
    checkedAnswers[card.id] = await api.checkExerciseAnswer({
      exercise_id: exercise.value.id,
      item_id: card.id,
      answer: String(optionId),
    })
  } catch (err) {
    answers[card.id] = ''
    error.value =
      err.response?.data?.error?.message ||
      err.response?.data?.detail ||
      'Die Antwort konnte nicht geprüft werden. Bitte versuche es erneut.'
  } finally {
    checkingAnswerId.value = null
  }
}

function setDropdownAnswer(itemId, partId, optionId) {
  if (!answers[itemId]) {
    answers[itemId] = {}
  }

  answers[itemId][String(partId)] = optionId
}

function setGapFillAnswer(itemId, gapId, value) {
  if (!answers[itemId]) {
    answers[itemId] = {}
  }

  answers[itemId][String(gapId)] = value
}

function addSentenceToken(itemId, tokenId) {
  if (!Array.isArray(answers[itemId])) {
    answers[itemId] = []
  }

  if (!answers[itemId].includes(tokenId)) {
    answers[itemId].push(tokenId)
  }
}

function removeSentenceToken(itemId, tokenId) {
  if (!Array.isArray(answers[itemId])) return

  answers[itemId] = answers[itemId].filter(id => id !== tokenId)
}

function getSentenceText(card) {
  const selectedIds = answers[card.id] || []
  const tokenById = new Map(
    (card.tokens || []).map(token => [token.id, token.text]),
  )

  return selectedIds.map(id => tokenById.get(id) || '').filter(Boolean).join(' ')
}

function isSentenceTokenSelected(card, tokenId) {
  return (answers[card.id] || []).includes(tokenId)
}

function getGapFillSegments(card) {
  const text = String(card.text || '')
  const gaps = card.gaps || []
  const gapByPlaceholder = new Map(
    gaps.map(gap => [gap.placeholder, gap]),
  )
  const segments = []
  const pattern = /\{\{[^}]+\}\}/g
  let lastIndex = 0
  let match

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({
        type: 'text',
        value: text.slice(lastIndex, match.index),
      })
    }

    const gap = gapByPlaceholder.get(match[0])

    if (gap) {
      segments.push({ type: 'gap', gap })
    } else {
      segments.push({ type: 'text', value: match[0] })
    }

    lastIndex = pattern.lastIndex
  }

  if (lastIndex < text.length) {
    segments.push({
      type: 'text',
      value: text.slice(lastIndex),
    })
  }

  return segments
}

function isAnswered(card) {
  if (exerciseType.value === 'multiple_choice') {
    return !!checkedAnswers[card.id]
  }

  if (exerciseType.value === 'sentence_builder') {
    const tokens = card.tokens || []
    const selected = answers[card.id] || []

    return tokens.length > 0 && selected.length === tokens.length
  }

  if (exerciseType.value === 'gap_fill') {
    const gaps = card.gaps || []

    return gaps.length > 0 && gaps.every(gap => {
      const value = answers[card.id]?.[String(gap.id)]
      return typeof value === 'string' && value.trim() !== ''
    })
  }

  if (exerciseType.value === 'dropdown') {
    const selectableParts = (card.parts || []).filter(
      part => part.part_type === 'select',
    )

    return selectableParts.length > 0 &&
      selectableParts.every(part => {
        const value = answers[card.id]?.[String(part.id)]
        return value !== undefined && value !== ''
      })
  }

  const value = answers[card.id]

  return value !== undefined &&
    value !== null &&
    value !== '' &&
    (!Array.isArray(value) || value.length > 0)
}

function getPrompt(card) {
  if (exerciseType.value === 'multiple_choice') {
    return card.question
  }

  return card.word || card.question || ''
}

async function loadExercise() {
  loading.value = true
  error.value = ''
  result.value = null

  try {
    const data = await api.getExerciseFull(route.params.id)
    exercise.value = data

    if (![
      'vocabulary_drill',
      'multiple_choice',
      'dropdown',
      'gap_fill',
      'sentence_builder',
    ].includes(data.exercise_type)) {
      throw new Error(
        `Dieser Übungstyp wird auf dieser Seite noch nicht unterstützt: ${data.exercise_type}`,
      )
    }

    if (!cards.value.length) {
      throw new Error('Dieses Übungsmodul enthält keine Aufgaben.')
    }

    for (const card of cards.value) {
      if (['dropdown', 'gap_fill'].includes(data.exercise_type)) {
        answers[card.id] = {}
      } else if (data.exercise_type === 'sentence_builder') {
        answers[card.id] = []
      } else {
        answers[card.id] = ''
      }
    }

    currentIndex.value = 0
  } catch (err) {
    exercise.value = null
    error.value =
      err.response?.data?.detail ||
      err.message ||
      'Die Übung konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function nextQuestion() {
  if (!currentCard.value || !isAnswered(currentCard.value)) {
    error.value = 'Bitte beantworte zuerst die aktuelle Aufgabe.'
    return
  }

  error.value = ''

  if (!isLastQuestion.value) {
    currentIndex.value += 1
  }
}

function previousQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value -= 1
    error.value = ''
  }
}

async function submitAnswers() {
  if (submitting.value || !exercise.value) return

  const unanswered = cards.value.some(card => !isAnswered(card))

  if (unanswered) {
    error.value = 'Bitte beantworte alle Aufgaben, bevor du abschließt.'
    return
  }

  submitting.value = true
  error.value = ''

  try {
    const formattedAnswers = cards.value.map(card => {
      let answer

      if (['dropdown', 'gap_fill'].includes(exerciseType.value)) {
        answer = { ...answers[card.id] }
      } else if (exerciseType.value === 'sentence_builder') {
        answer = [...answers[card.id]]
      } else {
        answer = String(answers[card.id])
      }

      return {
        item_id: card.id,
        answer,
      }
    })

    result.value = await api.saveExerciseResult({
      exercise_id: exercise.value.id,
      answers: formattedAnswers,
    })
  } catch (err) {
    error.value =
      err.response?.data?.detail ||
      err.response?.data?.error ||
      'Die Antworten konnten nicht gespeichert werden.'
  } finally {
    submitting.value = false
  }
}

onMounted(loadExercise)
</script>

<template>
  <main class="mx-auto max-w-3xl px-4 py-8">
    <div v-if="loading" class="py-12 text-center">
      Übung wird geladen …
    </div>

    <section
      v-else-if="error && !exercise"
      class="rounded-lg border border-red-300 p-5"
      role="alert"
    >
      <h1 class="mb-2 text-xl font-bold">Fehler</h1>
      <p>{{ error }}</p>
      <button
        class="mt-4 rounded bg-gray-800 px-4 py-2 text-white"
        @click="loadExercise"
      >
        Erneut versuchen
      </button>
    </section>

    <section v-else-if="result" class="space-y-6">
      <div class="text-center">
        <h1 class="text-2xl font-bold">Übung abgeschlossen</h1>
        <p class="mt-3 text-lg">Fertig! 🎉</p>
        <p class="mt-5 text-gray-600">Ergebnis</p>
        <p class="mt-1 text-4xl font-bold">
          {{ result.score }} / {{ result.max_score }}
        </p>
        <p class="mt-2 text-xl">
          {{ result.percentage }}% richtig
        </p>
      </div>

      <div>
        <h2 class="mb-4 text-xl font-semibold">Deine Antworten</h2>

        <article
          v-for="card in cards"
          :key="card.id"
          class="mb-4 rounded-xl border p-4 shadow-sm transition-colors duration-200 motion-reduce:transition-none"
          :class="
            resultByItemId[String(card.id)]?.is_correct === true
              ? 'border-emerald-300 bg-emerald-50'
              : resultByItemId[String(card.id)]?.is_correct === false
                ? 'border-red-300 bg-red-50'
                : 'border-slate-200 bg-white'
          "
        >
          <template v-if="exerciseType === 'gap_fill'">
            <p class="font-medium leading-8">
              <template
                v-for="(segment, index) in getGapFillSegments(card)"
                :key="index"
              >
                <span v-if="segment.type === 'text'">
                  {{ segment.value }}
                </span>
                <strong v-else class="mx-1 underline">
                  {{ answers[card.id]?.[String(segment.gap.id)] || '—' }}
                </strong>
              </template>
            </p>
          </template>

          <template v-else-if="exerciseType === 'sentence_builder'">
            <p class="text-lg font-medium">
              {{ getSentenceText(card) || '—' }}
            </p>

            <div
              v-if="
                resultByItemId[String(card.id)]?.is_correct === false
                && resultByItemId[String(card.id)]?.correct_answer
              "
              class="mt-3 rounded-lg border border-emerald-200 bg-white/80 p-3"
            >
              <p class="text-sm font-medium text-emerald-700">
                Richtige Lösung
              </p>
              <p class="mt-1 font-semibold text-emerald-800">
                {{ resultByItemId[String(card.id)].correct_answer }}
              </p>
            </div>
          </template>

          <template v-else-if="exerciseType === 'dropdown'">
            <p class="mb-3 font-medium">
              <template v-for="part in card.parts" :key="part.id">
                <span v-if="part.part_type === 'text'">
                  {{ part.text }}
                </span>
                <span v-else>
                  <strong>
                    {{ getSelectedOption(card.id, part.id)?.text || '—' }}
                  </strong>
                </span>
              </template>
            </p>
          </template>

          <template v-else>
            <p class="font-medium">{{ getPrompt(card) }}</p>
            <p class="mt-2">
              Deine Antwort:
              <strong>
                {{
                  exerciseType === 'multiple_choice'
                    ? getOptionText(card, answers[card.id])
                    : answers[card.id]
                }}
              </strong>
            </p>
          </template>

          <p
            v-if="resultByItemId[String(card.id)]"
            class="mt-4 border-t border-current/10 pt-3 font-bold"
            :class="
              resultByItemId[String(card.id)].is_correct
                ? 'text-emerald-700'
                : 'text-red-700'
            "
          >
            {{
              resultByItemId[String(card.id)].is_correct
                ? '✓ Richtig'
                : '✗ Leider falsch'
            }}
          </p>
        </article>
      </div>
    </section>

    <section v-else-if="exercise" class="space-y-6">
      <header>
        <h1 class="text-2xl font-bold">{{ exercise.title }}</h1>
        <p class="mt-1 text-gray-600">
          Aufgabe {{ currentIndex + 1 }} von {{ cards.length }}
        </p>
      </header>

      <div
        v-if="error"
        class="rounded border border-red-300 p-3 text-red-700"
        role="alert"
      >
        {{ error }}
      </div>

      <article v-if="currentCard" class="rounded-lg border p-5">
        <template v-if="exerciseType === 'gap_fill'">
          <p class="mb-5 text-lg leading-9">
            <template
              v-for="(segment, index) in getGapFillSegments(currentCard)"
              :key="index"
            >
              <span v-if="segment.type === 'text'">
                {{ segment.value }}
              </span>
              <input
                v-else
                type="text"
                :value="answers[currentCard.id]?.[String(segment.gap.id)] ?? ''"
                class="mx-1 inline-block w-32 rounded border px-2 py-1 text-base"
                :aria-label="`Antwort für ${segment.gap.placeholder}`"
                @input="
                  setGapFillAnswer(
                    currentCard.id,
                    segment.gap.id,
                    $event.target.value
                  )
                "
              />
            </template>
          </p>
        </template>

        <template v-else-if="exerciseType === 'sentence_builder'">
          <h2 class="mb-4 text-lg font-medium">
            Ordne die Wörter zu einem Satz:
          </h2>

          <div class="mb-5 min-h-14 rounded border bg-gray-50 p-3">
            <button
              v-for="tokenId in answers[currentCard.id]"
              :key="tokenId"
              type="button"
              class="mr-2 mb-2 rounded border bg-white px-3 py-2 hover:bg-red-50"
              :aria-label="`Wort entfernen: ${currentCard.tokens.find(token => token.id === tokenId)?.text || tokenId}`"
              @click="removeSentenceToken(currentCard.id, tokenId)"
            >
              {{ currentCard.tokens.find(token => token.id === tokenId)?.text }}
              <span aria-hidden="true">×</span>
            </button>

            <span
              v-if="!answers[currentCard.id]?.length"
              class="text-gray-500"
            >
              Wähle die Wörter in der richtigen Reihenfolge.
            </span>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              v-for="token in currentCard.tokens"
              :key="token.id"
              type="button"
              class="rounded border px-3 py-2 disabled:cursor-not-allowed disabled:opacity-40"
              :disabled="isSentenceTokenSelected(currentCard, token.id)"
              @click="addSentenceToken(currentCard.id, token.id)"
            >
              {{ token.text }}
            </button>
          </div>
        </template>

        <template v-else-if="exerciseType === 'dropdown'">
          <p class="mb-5 text-lg leading-9">
            <template v-for="part in currentCard.parts" :key="part.id">
              <span v-if="part.part_type === 'text'">
                {{ part.text }}
              </span>

              <select
                v-else-if="part.part_type === 'select'"
                :value="answers[currentCard.id]?.[String(part.id)] ?? ''"
                class="mx-1 rounded border bg-white px-2 py-1 text-base"
                :aria-label="`Antwort für Teil ${part.id}`"
                @change="
                  setDropdownAnswer(
                    currentCard.id,
                    part.id,
                    $event.target.value,
                  )
                "
              >
                <option value="" disabled>Bitte auswählen</option>
                <option
                  v-for="option in part.options"
                  :key="option.id"
                  :value="String(option.id)"
                >
                  {{ option.text }}
                </option>
              </select>
            </template>
          </p>
        </template>

        <template v-else-if="exerciseType === 'multiple_choice'">
          <div class="card-scene">
            <div
              class="card-inner"
              :class="{ 'card-flipped': checkedAnswers[currentCard.id] }"
            >
              <div class="card-face rounded-lg p-2">
                <h2 class="mb-5 text-lg font-medium">
                  {{ getPrompt(currentCard) }}
                </h2>

                <div class="space-y-3">
                  <label
                    v-for="option in currentCard.options"
                    :key="option.id"
                    class="flex cursor-pointer items-center gap-3 rounded border p-3 hover:bg-gray-50"
                    :class="{
                      'cursor-not-allowed opacity-60':
                        checkedAnswers[currentCard.id] ||
                        checkingAnswerId === String(currentCard.id),
                    }"
                  >
                    <input
                      type="radio"
                      :name="`answer-${currentCard.id}`"
                      :value="String(option.id)"
                      :checked="answers[currentCard.id] === String(option.id)"
                      :disabled="
                        !!checkedAnswers[currentCard.id] ||
                        checkingAnswerId === String(currentCard.id)
                      "
                      @change="
                        selectMultipleChoiceOption(currentCard, option.id)
                      "
                    />
                    <span>{{ option.text }}</span>
                  </label>
                </div>

                <p
                  v-if="checkingAnswerId === String(currentCard.id)"
                  class="mt-4 text-sm text-gray-600"
                  role="status"
                >
                  Antwort wird geprüft …
                </p>
              </div>

              <div
                v-if="checkedAnswers[currentCard.id]"
                class="card-face card-back rounded-lg border p-5"
                :class="
                  checkedAnswers[currentCard.id].is_correct
                    ? 'border-green-300 bg-green-50'
                    : 'border-red-300 bg-red-50'
                "
                aria-live="polite"
              >
                <p class="mb-3 text-xl font-semibold">
                  {{
                    checkedAnswers[currentCard.id].is_correct
                      ? 'Richtig!'
                      : 'Leider falsch.'
                  }}
                </p>

                <template v-if="!checkedAnswers[currentCard.id].is_correct">
                  <p class="text-sm text-gray-600">Richtige Antwort:</p>
                  <p class="mt-1 text-lg font-medium">
                    {{ checkedAnswers[currentCard.id].correct_answer }}
                  </p>
                </template>

                <p v-else class="text-sm">
                  Gut gemacht — deine Antwort ist richtig.
                </p>
              </div>
            </div>
          </div>
        </template>

        <template v-else>
          <h2 class="mb-5 text-lg font-medium">
            {{ getPrompt(currentCard) }}
          </h2>

          <div class="space-y-3">
            <label
              v-for="option in currentCard.options"
              :key="option.id"
              class="flex cursor-pointer items-center gap-3 rounded border p-3 hover:bg-gray-50"
            >
              <input
                v-model="answers[currentCard.id]"
                type="radio"
                :name="`answer-${currentCard.id}`"
                :value="String(option.id)"
              />
              <span>{{ option.text }}</span>
            </label>
          </div>
        </template>
      </article>

      <div class="flex flex-wrap justify-between gap-3">
        <button
          class="rounded border px-4 py-2 disabled:opacity-40"
          :disabled="currentIndex === 0 || submitting"
          @click="previousQuestion"
        >
          Zurück
        </button>

        <button
          v-if="!isLastQuestion"
          class="rounded bg-gray-800 px-4 py-2 text-white disabled:opacity-40"
          :disabled="submitting"
          @click="nextQuestion"
        >
          Nächste Aufgabe
        </button>

        <button
          v-else
          class="rounded bg-green-700 px-4 py-2 text-white disabled:opacity-40"
          :disabled="submitting"
          @click="submitAnswers"
        >
          {{ submitting ? 'Wird geprüft …' : 'Übung abschließen' }}
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.card-scene {
  perspective: 1000px;
}

.card-inner {
  display: grid;
  transform-style: preserve-3d;
  transition: transform 500ms ease;
}

.card-inner > .card-face {
  grid-area: 1 / 1;
  backface-visibility: hidden;
}

.card-inner > .card-back {
  transform: rotateY(180deg);
}

.card-inner.card-flipped {
  transform: rotateY(180deg);
}

@media (prefers-reduced-motion: reduce) {
  .card-inner {
    transition: none;
  }
}
</style>
