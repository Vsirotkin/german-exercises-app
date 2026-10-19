<template>
  <RouterView v-slot="{ Component, route }">
    <AuthenticatedLayout v-if="route.meta.requiresAuth">
      <component :is="Component" />
    </AuthenticatedLayout>

    <component :is="Component" v-else />
  </RouterView>
</template>

<script setup>
import { onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import AuthenticatedLayout from '@/layouts/AuthenticatedLayout.vue'

const router = useRouter()

function handleAuthLogout(event) {
  localStorage.removeItem('authToken')
  localStorage.removeItem('refreshToken')

  const currentRoute = router.currentRoute.value
  const isManualLogout =
    event instanceof CustomEvent && event.detail?.reason === 'manual'
  const isProtectedRoute = currentRoute.matched.some(
    record => record.meta.requiresAuth,
  )

  const target = { name: 'login' }

  // При истечении сессии запоминаем страницу,
  // на которую ученик сможет вернуться после повторного входа.
  if (!isManualLogout && isProtectedRoute) {
    target.query = { redirect: currentRoute.fullPath }
  }

  void router.replace(target)
}

window.addEventListener('auth:logout', handleAuthLogout)

onBeforeUnmount(() => {
  window.removeEventListener('auth:logout', handleAuthLogout)
})
</script>
