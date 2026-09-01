<!-- src/App.vue -->
<template>
  <div class="container mt-4">

    <!-- 1. Индикатор загрузки (показывается пока проверяем токен) -->
    <div v-if="isLoading" class="text-center mt-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Lade Benutzerdaten...</p>
    </div>

    <!-- 2. Форма входа (если не авторизован) -->
    <LoginForm v-else-if="!isAuthenticated" @login-success="handleLoginSuccess" />

    <!-- 3. Основной интерфейс (для авторизованных) -->
    <template v-else>
      <!-- Шапка -->
      <header class="mb-4 text-center">
        <h1 class="display-5">🇩🇪 German Language Exercises</h1>
        <p class="lead text-muted">Ihre personalisierten Übungen</p>
      </header>

      <!-- Навбар -->
      <NavBar :student-name="currentStudentName" @show-progress="currentView = 'progress'"
        @show-list="currentView = 'list'" />

      <main class="my-4">

        <!-- СПИСОК УПРАЖНЕНИЙ -->
        <ExerciseList v-if="currentView === 'list'" @exercise-select="handleSelectExercise" />

        <!-- КОМПОНЕНТ УПРАЖНЕНИЯ -->
        <div v-else-if="currentView === 'exercise' && selectedExercise">
          <ExerciseComponent :topic-name="selectedExercise.topicName" :exercise-id="selectedExercise.exerciseId"
            @back-to-list="currentView = 'list'" />
        </div>

        <!-- ✅ НОВОЕ: Страница прогресса студента -->
        <StudentProgress v-else-if="currentView === 'progress'" :student-id="currentUserId"
          @back-to-list="currentView = 'list'" />

      </main>

      <!-- Инструкция (упрощенная) -->
      <div class="card mt-4 shadow-sm">
        <div class="card-body">
          <h5 class="card-title">
            <i class="bi bi-info-circle me-2"></i>Anleitung
          </h5>
          <ol class="mb-0 text-muted">
            <li>Wählen Sie eine Übung aus der Liste.</li>
            <li>Lösen Sie die Aufgaben (Lücken füllen oder Vokabeln lernen).</li>
            <li>Überprüfen Sie Ihre Antworten und sehen Sie Ihr Ergebnis.</li>
          </ol>
        </div>
      </div>

      <footer class="mt-5 text-center text-muted small">
        <p>German Exercises App &copy; 2026</p>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LoginForm from './components/LoginForm.vue'
import NavBar from './components/NavBar.vue'
import ExerciseComponent from './components/ExerciseComponent.vue'
import ExerciseList from './components/ExerciseList.vue'
import StudentProgress from './components/StudentProgress.vue' // ✅ Импортируем компонент прогресса
import { api } from '@/utils/api'

// === Состояние приложения ===
const isAuthenticated = ref(false)
const isLoading = ref(true)
const currentStudentName = ref('')
const currentUserId = ref(null)
const currentView = ref('list') // 'list' | 'exercise' | 'progress' ✅ Добавили 'progress'
const selectedExercise = ref(null)

// === Загрузка профиля пользователя ===
const loadUserProfile = async () => {
  const token = localStorage.getItem('authToken')

  if (!token) {
    isAuthenticated.value = false
    isLoading.value = false
    return
  }

  try {
    const user = await api.getCurrentUser()

    currentStudentName.value = user.first_name || user.username
    currentUserId.value = user.id
    isAuthenticated.value = true
    currentView.value = 'list'
  } catch (error) {
    console.error('❌ Failed to load user profile:', error)
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('authToken')
      localStorage.removeItem('refreshToken')
      isAuthenticated.value = false
    }
  } finally {
    isLoading.value = false
  }
}

const handleLoginSuccess = async () => {
  await loadUserProfile()
}

const handleSelectExercise = ({ topicName, exerciseId }) => {
  selectedExercise.value = { topicName, exerciseId }
  currentView.value = 'exercise'
}

onMounted(() => {
  loadUserProfile()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
