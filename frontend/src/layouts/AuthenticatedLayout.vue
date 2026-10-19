<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <RouterLink
          :to="homeLocation"
          class="flex w-fit items-center gap-3 no-underline"
        >
          <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-xl shadow-sm">
            🇩🇪
          </span>

          <span>
            <span class="block text-base font-bold tracking-tight text-slate-900">
              German Exercises
            </span>
            <span class="block text-xs text-slate-500">
              {{ isAdmin ? 'Administrationsbereich' : 'Ihr persönlicher Lernbereich' }}
            </span>
          </span>
        </RouterLink>

        <div class="flex flex-wrap items-center justify-between gap-3 sm:justify-end sm:gap-5">
          <nav aria-label="Hauptnavigation" class="flex flex-wrap items-center gap-1">
            <RouterLink
              :to="homeLocation"
              :class="[
                baseLinkClass,
                isHomeActive ? activeLinkClass : inactiveLinkClass,
              ]"
            >
              {{ isAdmin ? 'Administration' : 'Übersicht' }}
            </RouterLink>

            <RouterLink
              to="/exercises"
              :class="[
                baseLinkClass,
                isExercisesActive ? activeLinkClass : inactiveLinkClass,
              ]"
            >
              Übungen
            </RouterLink>
          </nav>

          <button
            type="button"
            class="rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-red-50 hover:text-red-700"
            @click="handleLogout"
          >
            Abmelden
          </button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/utils/api'

const route = useRoute()
const currentUser = ref(null)

const baseLinkClass =
  'rounded-xl px-3 py-2 text-sm font-medium transition'
const activeLinkClass = 'bg-blue-50 text-blue-700'
const inactiveLinkClass =
  'text-slate-600 hover:bg-slate-100 hover:text-slate-900'

const isAdmin = computed(
  () =>
    currentUser.value?.role === 'admin' ||
    route.name === 'admin-dashboard',
)

const homeLocation = computed(() =>
  isAdmin.value
    ? { name: 'admin-dashboard' }
    : { name: 'dashboard' },
)

const isHomeActive = computed(
  () =>
    route.name === 'dashboard' ||
    route.name === 'admin-dashboard',
)

const isExercisesActive = computed(
  () =>
    route.path === '/exercises' ||
    route.path.startsWith('/exercises/'),
)

onMounted(async () => {
  try {
    currentUser.value = await api.getCurrentUser()
  } catch (error) {
    // The API interceptor handles expired sessions and logout.
    console.error('Could not load navigation user:', error)
  }
})

function handleLogout() {
  window.dispatchEvent(
    new CustomEvent('auth:logout', {
      detail: { reason: 'manual' },
    }),
  )
}
</script>
