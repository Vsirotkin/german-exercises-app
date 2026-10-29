import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const mocks = vi.hoisted(() => ({
  getExerciseFull: vi.fn(),
  checkExerciseAnswer: vi.fn(),
  saveExerciseResult: vi.fn(),
  route: { params: { id: '42' } },
}))

vi.mock('@/utils/api', () => ({
  api: {
    getExerciseFull: mocks.getExerciseFull,
    checkExerciseAnswer: mocks.checkExerciseAnswer,
    saveExerciseResult: mocks.saveExerciseResult,
  },
}))

vi.mock('vue-router', () => ({
  useRoute: () => mocks.route,
}))

import ExercisePage from './ExercisePage.vue'

function createExercise(overrides = {}) {
  return {
    id: 42,
    title: 'Deutsch üben',
    exercise_type: 'multiple_choice',
    multiple_choice_items: [
      {
        id: 101,
        question: 'Was bedeutet „Haus“?',
        options: [
          { id: 1, text: 'house' },
          { id: 2, text: 'car' },
        ],
      },
    ],
    ...overrides,
  }
}

function mountPage() {
  return mount(ExercisePage)
}

describe('ExercisePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.route.params.id = '42'
    mocks.getExerciseFull.mockResolvedValue(createExercise())
    mocks.checkExerciseAnswer.mockResolvedValue({
      is_correct: true,
      correct_answer: 'house',
    })
    mocks.saveExerciseResult.mockResolvedValue({
      score: 1,
      max_score: 1,
      percentage: 100,
      results: [
        { item_id: 101, is_correct: true },
      ],
    })
  })

  it('loads and displays the exercise', async () => {
    const wrapper = mountPage()
    await flushPromises()

    expect(mocks.getExerciseFull).toHaveBeenCalledWith('42')
    expect(wrapper.text()).toContain('Deutsch üben')
    expect(wrapper.text()).toContain('Was bedeutet „Haus“?')
    expect(wrapper.text()).toContain('house')
  })

  it('shows a retry option when loading fails', async () => {
    mocks.getExerciseFull.mockRejectedValueOnce(
      new Error('Network unavailable'),
    )

    const wrapper = mountPage()
    await flushPromises()

    expect(wrapper.text()).toContain('Network unavailable')
    expect(wrapper.text()).toContain('Erneut versuchen')

    mocks.getExerciseFull.mockResolvedValueOnce(createExercise())
    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(mocks.getExerciseFull).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('Deutsch üben')
  })

  it('checks a multiple-choice answer and displays feedback', async () => {
    const wrapper = mountPage()
    await flushPromises()

    await wrapper.get('input[type="radio"][value="1"]').setValue()
    await flushPromises()

    expect(mocks.checkExerciseAnswer).toHaveBeenCalledWith({
      exercise_id: 42,
      item_id: 101,
      answer: '1',
    })
    expect(wrapper.text()).toContain('Richtig!')
  })

  it('does not advance when the current question is unanswered', async () => {
    const exercise = createExercise({
      multiple_choice_items: [
        {
          id: 101,
          question: 'Erste Frage',
          options: [
            { id: 1, text: 'Antwort A' },
            { id: 2, text: 'Antwort B' },
          ],
        },
        {
          id: 102,
          question: 'Zweite Frage',
          options: [
            { id: 3, text: 'Antwort C' },
            { id: 4, text: 'Antwort D' },
          ],
        },
      ],
    })
    mocks.getExerciseFull.mockResolvedValueOnce(exercise)

    const wrapper = mountPage()
    await flushPromises()

    const nextButton = wrapper.findAll('button').find(
      button => button.text().includes('Nächste Aufgabe'),
    )
    await nextButton.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Erste Frage')
    expect(wrapper.text()).toContain(
      'Bitte beantworte zuerst die aktuelle Aufgabe.',
    )
    expect(wrapper.text()).not.toContain('Zweite Frage')
  })

  it('submits answered questions and displays the result', async () => {
    const wrapper = mountPage()
    await flushPromises()

    await wrapper.get('input[type="radio"][value="1"]').setValue()
    await flushPromises()

    const submitButton = wrapper.findAll('button').find(
      button => button.text().includes('Übung abschließen'),
    )
    await submitButton.trigger('click')
    await flushPromises()

    expect(mocks.saveExerciseResult).toHaveBeenCalledWith({
      exercise_id: 42,
      answers: [
        {
          item_id: 101,
          answer: '1',
        },
      ],
    })
    expect(wrapper.text()).toContain('Übung abgeschlossen')
    expect(wrapper.text()).toContain('1 / 1')
    expect(wrapper.text()).toContain('100% richtig')
  })
})
