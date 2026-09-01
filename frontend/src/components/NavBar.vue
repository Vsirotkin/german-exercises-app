<!-- src/components/NavBar.vue -->
<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
    <div class="container">
      <!-- КНОПКА: Домой (всегда видна) -->
      <button @click="$emit('show-list')" class="btn btn-outline-primary btn-sm me-2" title="Zurück zur Übungsliste">
        <i class="bi bi-house me-1"></i> Start
      </button>

      <span class="navbar-brand">🇩🇪 German Exercises</span>

      <div class="navbar-nav ms-auto">
        <span class="navbar-text me-3">
          Hallo, {{ studentName }}!
        </span>

        <!-- Кнопка Прогресс -->
        <button @click="$emit('show-progress')" class="btn btn-outline-primary btn-sm me-2">
          <i class="bi bi-graph-up me-1"></i> Fortschritt
        </button>

        <!-- Кнопка выхода -->
        <button class="btn btn-outline-danger btn-sm" @click="logout">
          <i class="bi bi-box-arrow-right me-1"></i> Abmelden
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
// === Props ===
defineProps({
  studentName: {
    type: String,
    default: ''
  }
})

// === Emits ===
// 'show-list' для возврата на главную
const emit = defineEmits(['logout', 'show-progress', 'show-list'])

// === Methods ===
const logout = () => {
  localStorage.removeItem('authToken')
  localStorage.removeItem('refreshToken')
  emit('logout')
  window.location.reload()
}
</script>
