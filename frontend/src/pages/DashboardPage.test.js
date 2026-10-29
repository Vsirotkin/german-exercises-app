import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const mocks = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  getStudentProgress: vi.fn(),
  getStudentHistory: vi.fn(),
  getExercisesList: vi.fn(),
  getRecommendationFeed: vi.fn(),
}))

vi.mock('@/utils/api', () => ({
  api: mocks,
}))

import DashboardPage from './DashboardPage.vue'

function mountDashboard() {
  return mount(DashboardPage, {
    global: {
      stubs: {
        RouterLink: {
          props: ['to'],
          template: '<a :href="typeof to === \'string\' ? to : \'#\'"><slot /></a>',
        },
      },
    },
  })
}

function mockSuccessfulDashboard({
  user = { id: 1, student_id: 10, first_name: 'Anna', username: 'anna' },
  progress = {
    average_score: 75,
    best_score: 100,
    total_exercises: 4,
    last_activity: null,
  },
  history = [],
  exercises = [],
  recommendations = [],
} = {}) {
  mocks.getCurrentUser.mockResolvedValue(user)
  mocks.getStudentProgress.mockResolvedValue(progress)
  mocks.getStudentHistory.mockResolvedValue(history)
  mocks.getExercisesList.mockResolvedValue(exercises)
  mocks.getRecommendationFeed.mockResolvedValue({ recommendations })
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads dashboard data and displays the student name and statistics', async () => {
    mockSuccessfulDashboard({
      progress: {
        average_score: 75,
        best_score: 100,
        total_exercises: 4,
        last_activity: null,
      },
      exercises: [{ id: 1 }, { id: 2 }],
    })

    const wrapper = mountDashboard()
    await flushPromises()

    expect(wrapper.text()).toContain('Guten Tag, Anna!')
    expect(wrapper.text()).toContain('Durchschnittliches Ergebnis')
    expect(wrapper.text()).toContain('75%')
    expect(wrapper.text()).toContain('100%')
    expect(wrapper.text()).toContain('Verfügbare Übungen')
    expect(mocks.getStudentProgress).toHaveBeenCalledWith(10)
    expect(mocks.getStudentHistory).toHaveBeenCalledWith(10)
    expect(mocks.getExercisesList).toHaveBeenCalled()
    expect(mocks.getRecommendationFeed).toHaveBeenCalled()
    expect(wrapper.text()).not.toContain('Lade deinen Lernfortschritt...')
  })

  it('shows a profile error and does not request student data without student_id', async () => {
    mocks.getCurrentUser.mockResolvedValue({
      id: 2,
      username: 'unlinked-user',
    })

    const wrapper = mountDashboard()
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain(
      'Für dieses Konto ist kein Schülerprofil verknüpft.',
    )
    expect(mocks.getStudentProgress).not.toHaveBeenCalled()
    expect(mocks.getStudentHistory).not.toHaveBeenCalled()
    expect(mocks.getExercisesList).not.toHaveBeenCalled()
    expect(mocks.getRecommendationFeed).not.toHaveBeenCalled()
  })

  it('keeps the dashboard visible when progress loading fails', async () => {
    mockSuccessfulDashboard()
    mocks.getStudentProgress.mockRejectedValue(new Error('Progress unavailable'))

    const wrapper = mountDashboard()
    await flushPromises()

    expect(wrapper.text()).toContain('Guten Tag, Anna!')
    expect(wrapper.text()).toContain(
      'Die Fortschrittsstatistik ist momentan nicht verfügbar.',
    )
    await wrapper.get('[role="tablist"] button:nth-child(3)').trigger('click')
    expect(wrapper.text()).toContain('Letzte Übungsergebnisse')
  })

  it('renders personalized recommendations and their exercise link', async () => {
    mockSuccessfulDashboard({
      recommendations: [
        {
          id: 7,
          title: 'Wiederhole die Wortstellung',
          priority: 'high',
          message: 'Übe deutsche Hauptsätze.',
          reason: 'Die letzten Ergebnisse zeigen Übungsbedarf.',
          topic: { name: 'Wortstellung' },
          exercise: { id: 42 },
        },
      ],
    })

    const wrapper = mountDashboard()
    await flushPromises()

    await wrapper.get('[role="tablist"] button:nth-child(2)').trigger('click')
    expect(wrapper.text()).toContain('Empfehlungen für dich')
    expect(wrapper.text()).toContain('Wiederhole die Wortstellung')
    expect(wrapper.text()).toContain('Hohe Priorität')
    expect(wrapper.text()).toContain('Wortstellung')
    expect(wrapper.find('a[href="/exercises/42"]').exists()).toBe(true)
  })

  it('shows empty states when history and recommendations are empty', async () => {
    mockSuccessfulDashboard()

    const wrapper = mountDashboard()
    await flushPromises()

    await wrapper.get('[role="tablist"] button:nth-child(3)').trigger('click')
    expect(wrapper.text()).toContain('Noch keine Ergebnisse')

    await wrapper.get('[role="tablist"] button:nth-child(2)').trigger('click')
    expect(wrapper.text()).toContain('Momentan gibt es keine Empfehlungen.')
  })
})
