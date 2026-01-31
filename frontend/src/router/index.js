import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Dashboard from '../views/Dashboard.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Timeout per evitare che checkAuth blocchi indefinitamente
const withTimeout = (promise, ms) => {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms))
  ])
}

// Navigation guard to protect routes
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Check authentication on app start (timeout 5s - non bloccare se API lenta)
  if (!authStore.isAuthenticated && !authStore.isLoggedIn) {
    try {
      await withTimeout(authStore.checkAuth(), 5000)
    } catch {
      // Timeout o errore: procedi con stato attuale
    }
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    // Check both isAuthenticated and isLoggedIn for compatibility
    if (!authStore.isAuthenticated && !authStore.isLoggedIn) {
      // Redirect to home with login param if not authenticated
      next('/?login=true')
      return
    }
  }

  next()
})

export default router

