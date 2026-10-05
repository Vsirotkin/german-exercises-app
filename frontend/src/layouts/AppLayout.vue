<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <RouterLink to="/dashboard" class="text-xl font-bold tracking-tight text-slate-900 no-underline">
          🇩🇪 German Exercises
        </RouterLink>

        <nav class="flex items-center gap-6 text-sm font-medium">
          <RouterLink to="/dashboard" class="text-slate-600 no-underline transition hover:text-slate-900"
            active-class="!text-blue-600">
            Dashboard
          </RouterLink>

          <button type="button" class="text-slate-600 transition hover:text-red-600" @click="handleLogout">
            Abmelden
          </button>
        </nav>
      </div>
    </header>

    <main class="mx-auto max-w-7xl px-6 py-8">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const handleLogout = () => {
  localStorage.removeItem('authToken')
  localStorage.removeItem('refreshToken')

  router.push({ name: 'login' })
}
</script>
