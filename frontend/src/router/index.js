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

// Navigation guard to protect routes
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Check authentication on app start
  if (!authStore.isAuthenticated && !authStore.isLoggedIn) {
    await authStore.checkAuth()
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

