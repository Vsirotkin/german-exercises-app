<!-- src/components/LoginForm.vue -->
<template>
  <div class="login-form-container">
    <h2 class="text-center mb-4">🇩🇪 Вход в систему</h2>
    <form @submit.prevent="handleLogin" class="p-4 border rounded shadow-sm bg-white">
      <div class="mb-3">
        <label for="username" class="form-label">Имя пользователя</label>
        <input id="username" v-model="username" type="text" class="form-control" required
          placeholder="Введите имя пользователя" />
      </div>
      <div class="mb-3">
        <label for="password" class="form-label">Пароль</label>
        <input id="password" v-model="password" type="password" class="form-control" required
          placeholder="Введите пароль" />
      </div>
      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <button type="submit" class="btn btn-primary w-100" :disabled="loading">
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { api } from '@/utils/api'; // Импорт нашего обновленного модуля

const username = ref('');
const password = ref('');
const error = ref('');
const loading = ref(false);
const emit = defineEmits(['login-success']);

const handleLogin = async () => {
  error.value = '';
  loading.value = true;

  try {
    // Вызов метода login из нового модуля
    const data = await api.login({
      username: username.value,
      password: password.value
    });

    // Django возвращает { access: "...", refresh: "..." }
    if (data.access) {
      localStorage.setItem('authToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);
      emit('login-success');
    } else {
      error.value = 'Ошибка формата ответа';
    }
  } catch (err) {
    console.error('Login error:', err);
    if (err.response?.status === 401) {
      error.value = 'Неверное имя пользователя или пароль';
    } else {
      error.value = 'Ошибка сети или сервера';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-form-container {
  max-width: 400px;
  margin: 2rem auto;
}
</style>
