/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import VocabularyDrill from './VocabularyDrill.vue'

// Мокаем модуль api, чтобы тесты не делали реальных сетевых запросов
vi.mock('../utils/api', () => ({
  api: {
    saveExerciseResult: vi.fn().mockResolvedValue({ data: { id: 1 } })
  }
}))

import { api } from '../utils/api'

describe('VocabularyDrill.vue', () => {
  const mockExercise = {
    id: 1,
    title: 'Krankenhaus Übung',
    vocabulary_cards: [
      {
        id: 101,
        word: 'der Arzt',
        correct_translation: 'врач',
        distractor_1: 'аптекарь',
        distractor_2: 'пациент',
        distractor_3: 'медсестра'
      },
      {
        id: 102,
        word: 'das Krankenhaus',
        correct_translation: 'больница',
        distractor_1: 'школа',
        distractor_2: 'аптека',
        distractor_3: 'дом'
      }
    ]
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // Включаем фейковые таймеры для контроля setTimeout (600мс) в компоненте
    vi.useFakeTimers()
  })

  it('успешно монтируется и отображает первое слово', () => {
    const wrapper = mount(VocabularyDrill, {
      props: { exercise: mockExercise }
    })

    expect(wrapper.text()).toContain('der Arzt')
    expect(wrapper.text()).toContain('Вопрос 1 из 2')
    expect(wrapper.find('.progress-bar').attributes('style')).toContain('width: 0%')
  })

  it('корректно обрабатывает выбор правильного ответа и переходит к следующему', async () => {
    const wrapper = mount(VocabularyDrill, {
      props: { exercise: mockExercise }
    })

    // Находим кнопку с правильным переводом
    const buttons = wrapper.findAll('.option-btn')
    const correctButton = buttons.find(btn => btn.text() === 'врач')

    // Симулируем клик
    await correctButton.trigger('click')

    // 1. Проверяем мгновенную реакцию UI
    expect(wrapper.vm.hasAnswered).toBe(true)
    expect(correctButton.classes()).toContain('btn-success')

    // 2. "Перематываем" время на 600мс (время задержки в компоненте)
    await vi.advanceTimersByTimeAsync(600)
    await wrapper.vm.$nextTick()

    // 3. Проверяем, что перешли ко второму вопросу
    expect(wrapper.vm.currentCardIndex).toBe(1)
    expect(wrapper.vm.hasAnswered).toBe(false)
    expect(wrapper.text()).toContain('das Krankenhaus')
    expect(wrapper.find('.progress-bar').attributes('style')).toContain('width: 50%')
  })

  it('завершает упражнение, вычисляет результат и отправляет СЫРЫЕ баллы на бэкенд', async () => {
    const wrapper = mount(VocabularyDrill, {
      props: { exercise: mockExercise }
    })

    // Отвечаем правильно на первый вопрос
    let buttons = wrapper.findAll('.option-btn')
    await buttons.find(btn => btn.text() === 'врач').trigger('click')
    await vi.advanceTimersByTimeAsync(600)
    await wrapper.vm.$nextTick()

    // Отвечаем правильно на второй вопрос
    buttons = wrapper.findAll('.option-btn')
    await buttons.find(btn => btn.text() === 'больница').trigger('click')
    await vi.advanceTimersByTimeAsync(600)
    await wrapper.vm.$nextTick()

    // Проверяем экран результатов
    expect(wrapper.vm.isCompleted).toBe(true)
    expect(wrapper.text()).toContain('Ergebnis')
    expect(wrapper.text()).toContain('100%') // Процент для UI
    expect(wrapper.text()).toContain('Richtig: 2 / 2')

    // 🛡️ КРИТИЧЕСКАЯ ПРОВЕРКА: убеждаемся, что на бэк ушли сырые баллы (2), а не проценты (100)
    expect(api.saveExerciseResult).toHaveBeenCalledTimes(1)
    expect(api.saveExerciseResult).toHaveBeenCalledWith({
      exercise: 1,
      score: 2,               // ✅ Сырые баллы!
      total_questions: 2
    })
  })
})

