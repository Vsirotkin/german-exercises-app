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

// НОВАЯ ФУНКЦИЯ: создание dropdown упражнения с 2 частями
function createDropdownExercise() {
  return createExercise({
    exercise_type: 'dropdown',
    dropdown_items: [
      {
        id: 201,
        parts: [
          { part_type: 'text', text: 'Ich ' },
          {
            part_type: 'select',
            id: 101,
            options: [
              { id: 1, text: 'gehe' },
              { id: 2, text: 'geht' },
              { id: 3, text: 'gehen' },
            ]
          },
          { part_type: 'text', text: ' nach Hause. ' },
          {
            part_type: 'select',
            id: 102,
            options: [
              { id: 4, text: 'jede' },
              { id: 5, text: 'jeden' },
              { id: 6, text: 'jedem' },
            ]
          },
          { part_type: 'text', text: ' Tag.' },
        ]
      }
    ],
  })
}

// НОВАЯ ФУНКЦИЯ: создание gap_fill упражнения с 2 пропусками
function createGapFillExercise() {
  return createExercise({
    exercise_type: 'gap_fill',
    gap_fill_items: [
      {
        id: 301,
        text: 'Der {{gap1}} liegt auf dem {{gap2}}.',
        gaps: [
          { id: 201, placeholder: '{{gap1}}', correct_answer: 'Ball' },
          { id: 202, placeholder: '{{gap2}}', correct_answer: 'Tisch' },
        ]
      }
    ],
  })
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

  // НОВЫЕ ТЕСТЫ: регрессионные тесты для dropdown и gap_fill с unit_id

  it('handles dropdown exercise with mixed correct/incorrect parts in results', async () => {
    // Упражнение с dropdown
    mocks.getExerciseFull.mockResolvedValue(createDropdownExercise())

    // Ответы: часть 1 правильная (gehe), часть 2 неправильная (jeden вместо jede)
    const wrapper = mountPage()
    await flushPromises()

    // Установить ответы
    const selects = wrapper.findAll('select')
    await selects[0].setValue('1') // gehe (правильно)
    await selects[1].setValue('5') // jeden (неправильно, должно быть jede)

    // Мокаем результат с двумя unit_id, один правильный, один неправильный
    mocks.saveExerciseResult.mockResolvedValueOnce({
      score: 1,
      max_score: 2,
      percentage: 50,
      results: [
        { item_id: 201, unit_id: 101, is_correct: true, score: 1, max_score: 1 },
        { item_id: 201, unit_id: 102, is_correct: false, score: 0, max_score: 1 },
      ],
    })

    // Отправляем ответы
    const submitButton = wrapper.findAll('button').find(
      button => button.text().includes('Übung abschließen'),
    )
    await submitButton.trigger('click')
    await flushPromises()

    // Проверяем, что результаты отображаются правильно
    expect(wrapper.text()).toContain('1 / 2')
    expect(wrapper.text()).toContain('50% richtig')

    // Проверяем, что каждая часть отмечена своим цветом
    const strongElements = wrapper.findAll('strong')
    expect(strongElements[0].classes()).toContain('text-emerald-700') // Первая часть правильная
    expect(strongElements[1].classes()).toContain('text-red-700') // Вторая часть неправильная

    // Карточка должна быть отмечена как неправильная (не все части правильные)
    const article = wrapper.find('article')
    expect(article.classes()).toContain('border-red-300')
    expect(article.classes()).toContain('bg-red-50')
  })

  it('handles gap_fill exercise with mixed correct/incorrect gaps in results', async () => {
    // Упражнение с gap_fill
    mocks.getExerciseFull.mockResolvedValue(createGapFillExercise())

    const wrapper = mountPage()
    await flushPromises()

    // Установить ответы: первый пропуск правильный, второй неправильный
    const inputs = wrapper.findAll('input[type="text"]')
    await inputs[0].setValue('Ball') // Правильно
    await inputs[1].setValue('Boden') // Неправильно (должно быть Tisch)

    // Мокаем результат с двумя unit_id
    mocks.saveExerciseResult.mockResolvedValueOnce({
      score: 1,
      max_score: 2,
      percentage: 50,
      results: [
        { item_id: 301, unit_id: 201, is_correct: true, score: 1, max_score: 1 },
        { item_id: 301, unit_id: 202, is_correct: false, score: 0, max_score: 1 },
      ],
    })

    // Отправляем ответы
    const submitButton = wrapper.findAll('button').find(
      button => button.text().includes('Übung abschließen'),
    )
    await submitButton.trigger('click')
    await flushPromises()

    // Проверяем результаты
    expect(wrapper.text()).toContain('1 / 2')
    expect(wrapper.text()).toContain('50% richtig')

    // Проверяем цветовую кодировку каждого пропуска
    const strongElements = wrapper.findAll('strong')
    expect(strongElements[0].classes()).toContain('text-emerald-700') // Ball - правильно
    expect(strongElements[1].classes()).toContain('text-red-700') // Boden - неправильно

    // Карточка должна быть отмечена как неправильная
    const article = wrapper.find('article')
    expect(article.classes()).toContain('border-red-300')
    expect(article.classes()).toContain('bg-red-50')
  })

  it('correctly matches results by unit_id when results are in different order', async () => {
    // Упражнение с dropdown
    mocks.getExerciseFull.mockResolvedValue(createDropdownExercise())

    const wrapper = mountPage()
    await flushPromises()

    // Установить ответы
    const selects = wrapper.findAll('select')
    await selects[0].setValue('1') // gehe
    await selects[1].setValue('5') // jeden

    // Мокаем результат с изменённым порядком unit_id (102 перед 101)
    mocks.saveExerciseResult.mockResolvedValueOnce({
      score: 2,
      max_score: 2,
      percentage: 100,
      results: [
        { item_id: 201, unit_id: 102, is_correct: true, score: 1, max_score: 1 }, // Второй сначала
        { item_id: 201, unit_id: 101, is_correct: true, score: 1, max_score: 1 }, // Первый вторым
      ],
    })

    // Отправляем ответы
    const submitButton = wrapper.findAll('button').find(
      button => button.text().includes('Übung abschließen'),
    )
    await submitButton.trigger('click')
    await flushPromises()

    // Проверяем, что оба отображаются как правильные, несмотря на порядок
    const strongElements = wrapper.findAll('strong')
    expect(strongElements[0].classes()).toContain('text-emerald-700') // Первая часть
    expect(strongElements[1].classes()).toContain('text-emerald-700') // Вторая часть

    // Карточка должна быть отмечена как правильная
    const article = wrapper.find('article')
    expect(article.classes()).toContain('border-emerald-300')
    expect(article.classes()).toContain('bg-emerald-50')
  })

  it('maintains backward compatibility for multiple_choice without unit_id', async () => {
    // Стандартное multiple_choice упражнение без unit_id
    mocks.getExerciseFull.mockResolvedValue(createExercise())

    const wrapper = mountPage()
    await flushPromises()

    // Выбрать ответ
    await wrapper.get('input[type="radio"][value="1"]').setValue()
    await flushPromises()

    // Мокаем результат БЕЗ unit_id (старый формат)
    mocks.saveExerciseResult.mockResolvedValueOnce({
      score: 1,
      max_score: 1,
      percentage: 100,
      results: [
        { item_id: 101, is_correct: true, score: 1, max_score: 1 },
      ],
    })

    // Отправляем ответы
    const submitButton = wrapper.findAll('button').find(
      button => button.text().includes('Übung abschließen'),
    )
    await submitButton.trigger('click')
    await flushPromises()

    // Проверяем, что результат отображается правильно
    expect(wrapper.text()).toContain('1 / 1')
    expect(wrapper.text()).toContain('100% richtig')

    // Карточка должна быть отмечена как правильная
    const article = wrapper.find('article')
    expect(article.classes()).toContain('border-emerald-300')
    expect(article.classes()).toContain('bg-emerald-50')

    // Проверяем текст результата
    expect(wrapper.text()).toContain('✓ Richtig')
  })

  it('handles dropdown exercise where all parts are correct', async () => {
    // Упражнение с dropdown, все части правильные
    mocks.getExerciseFull.mockResolvedValue(createDropdownExercise())

    const wrapper = mountPage()
    await flushPromises()

    // Установить правильные ответы
    const selects = wrapper.findAll('select')
    await selects[0].setValue('1') // gehe (правильно)
    await selects[1].setValue('4') // jede (правильно)

    // Мокаем результат со всеми правильными unit_id
    mocks.saveExerciseResult.mockResolvedValueOnce({
      score: 2,
      max_score: 2,
      percentage: 100,
      results: [
        { item_id: 201, unit_id: 101, is_correct: true, score: 1, max_score: 1 },
        { item_id: 201, unit_id: 102, is_correct: true, score: 1, max_score: 1 },
      ],
    })

    // Отправляем ответы
    const submitButton = wrapper.findAll('button').find(
      button => button.text().includes('Übung abschließen'),
    )
    await submitButton.trigger('click')
    await flushPromises()

    // Проверяем, что карточка отмечена как полностью правильная
    const article = wrapper.find('article')
    expect(article.classes()).toContain('border-emerald-300')
    expect(article.classes()).toContain('bg-emerald-50')

    // Проверяем, что все части зелёные
    const strongElements = wrapper.findAll('strong')
    expect(strongElements[0].classes()).toContain('text-emerald-700')
    expect(strongElements[1].classes()).toContain('text-emerald-700')

    expect(wrapper.text()).toContain('✓ Richtig')
  })
})
