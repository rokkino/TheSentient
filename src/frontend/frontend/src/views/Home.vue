<template>
  <div class="home">
    <!-- Background with subtle gradient -->
    <div class="home-background"></div>
    
    <div class="home-container">
      <!-- Header -->
      <div class="home-header">
        <div class="logo-section">
          <div class="logo-icon">⚡</div>
          <h1 class="home-title">The Sentient</h1>
        </div>
        <p class="home-subtitle">Advanced Portfolio Intelligence & Trading Platform</p>
      </div>

      <!-- Auth Section -->
      <div v-if="!isLoggedIn" class="auth-section">
        <div class="auth-card">
          <div class="auth-header">
            <h2 class="auth-title">Welcome</h2>
            <p class="auth-subtitle">Access your trading intelligence platform</p>
          </div>
          
          <div class="auth-actions">
            <button @click="showLoginModal = true" class="auth-btn primary">
              <span>Sign In</span>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button @click="showRegisterModal = true" class="auth-btn secondary">
              Create Account
            </button>
          </div>
        </div>
      </div>

      <!-- Welcome Back Section -->
      <div v-else class="welcome-section">
        <div class="welcome-card">
          <div class="welcome-header">
            <h2>Welcome back</h2>
            <p class="welcome-username">{{ currentUser?.username }}</p>
          </div>
          <button @click="goToDashboard" class="auth-btn primary">
            <span>Go to Dashboard</span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Features Grid -->
      <div class="features-section">
        <div class="features-header">
          <h3 class="features-title">Platform Capabilities</h3>
          <p class="features-description">Enterprise-grade tools for professional traders</p>
        </div>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <div class="feature-icon">📊</div>
            </div>
            <h4 class="feature-title">Real-time Analytics</h4>
            <p class="feature-description">Advanced charting with technical indicators and pattern recognition</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <div class="feature-icon">📰</div>
            </div>
            <h4 class="feature-title">AI News Intelligence</h4>
            <p class="feature-description">Machine learning-powered sentiment analysis and trading signals</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <div class="feature-icon">📅</div>
            </div>
            <h4 class="feature-title">Earnings Calendar</h4>
            <p class="feature-description">Comprehensive earnings tracking with predictive analytics</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon-wrapper">
              <div class="feature-icon">🤖</div>
            </div>
            <h4 class="feature-title">Trading Automation</h4>
            <p class="feature-description">AI-driven trading bots with competitive performance tracking</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Login Modal -->
    <LoginModal 
      v-if="showLoginModal" 
      @close="showLoginModal = false" 
      @login-success="handleLoginSuccess"
      @switch-to-register="() => { showLoginModal = false; showRegisterModal = true; }"
    />

    <!-- Register Modal -->
    <RegisterModal 
      v-if="showRegisterModal" 
      @close="showRegisterModal = false" 
      @register-success="handleRegisterSuccess"
      @switch-to-login="() => { showRegisterModal = false; showLoginModal = true; }"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginModal from '../components/LoginModal.vue'
import RegisterModal from '../components/RegisterModal.vue'

const router = useRouter()
const authStore = useAuthStore()

const showLoginModal = ref(false)
const showRegisterModal = ref(false)

const isLoggedIn = computed(() => authStore.isLoggedIn || authStore.isAuthenticated)
const currentUser = computed(() => authStore.currentUser || authStore.user)

onMounted(async () => {
  await authStore.checkAuth()
  if (authStore.isLoggedIn) {
    router.push('/dashboard')
  } else {
    // Check for login query param
    const urlParams = new URLSearchParams(window.location.search)
    if (urlParams.get('login') === 'true') {
      showLoginModal.value = true
      // Clean up the URL
      window.history.replaceState({}, document.title, '/')
    }
  }
})

const handleLoginSuccess = () => {
  showLoginModal.value = false
  router.push('/dashboard')
}

const handleRegisterSuccess = () => {
  showRegisterModal.value = false
  router.push('/dashboard')
}

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  overflow-x: hidden;
}

.home-background {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(66, 153, 225, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.05) 0%, transparent 50%),
    linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
  z-index: 0;
}

.home-container {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  width: 100%;
}

/* Header */
.home-header {
  text-align: center;
  margin-bottom: 80px;
}

.logo-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 16px;
}

.logo-icon {
  font-size: 48px;
  filter: drop-shadow(0 0 20px rgba(66, 153, 225, 0.3));
}

.home-title {
  font-size: 72px;
  font-weight: 800;
  letter-spacing: -2px;
  background: linear-gradient(135deg, #ffffff 0%, #a0aec0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  line-height: 1;
}

.home-subtitle {
  font-size: 20px;
  color: #6b7280;
  font-weight: 400;
  letter-spacing: 0.5px;
  margin-top: 12px;
}

/* Auth Section */
.auth-section,
.welcome-section {
  display: flex;
  justify-content: center;
  margin-bottom: 100px;
}

.auth-card,
.welcome-card {
  background: rgba(26, 26, 26, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 48px;
  max-width: 480px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-title {
  font-size: 32px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.auth-subtitle {
  font-size: 15px;
  color: #9ca3af;
  margin: 0;
  font-weight: 400;
}

.welcome-header {
  text-align: center;
  margin-bottom: 32px;
}

.welcome-header h2 {
  font-size: 32px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.welcome-username {
  font-size: 18px;
  color: #4299e1;
  font-weight: 500;
  margin: 0;
}

.auth-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.auth-btn {
  padding: 14px 24px;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  letter-spacing: 0.3px;
}

.auth-btn.primary {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.auth-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(66, 153, 225, 0.4);
}

.auth-btn.primary:active {
  transform: translateY(0);
}

.auth-btn.secondary {
  background: rgba(255, 255, 255, 0.05);
  color: #e5e7eb;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.auth-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

/* Features Section */
.features-section {
  margin-top: 100px;
}

.features-header {
  text-align: center;
  margin-bottom: 48px;
}

.features-title {
  font-size: 42px;
  font-weight: 800;
  color: #ffffff;
  margin: 0 0 12px 0;
  letter-spacing: -1px;
}

.features-description {
  font-size: 16px;
  color: #6b7280;
  margin: 0;
  font-weight: 400;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.feature-card {
  background: rgba(26, 26, 26, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 32px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
}

.feature-card:hover {
  transform: translateY(-4px);
  background: rgba(26, 26, 26, 0.8);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}

.feature-icon-wrapper {
  margin-bottom: 20px;
}

.feature-icon {
  font-size: 40px;
  display: inline-block;
  filter: grayscale(0.2);
  transition: transform 0.3s;
}

.feature-card:hover .feature-icon {
  transform: scale(1.1);
}

.feature-title {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 12px 0;
  letter-spacing: -0.3px;
}

.feature-description {
  color: #9ca3af;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  font-weight: 400;
}

/* Responsive - Tablet & Mobile */
@media (max-width: 768px) {
  .home {
    padding: 20px 16px;
    padding-bottom: max(20px, env(safe-area-inset-bottom));
    align-items: flex-start;
  }

  .home-header {
    margin-bottom: 40px;
    margin-top: 20px;
  }

  .logo-icon {
    font-size: 32px;
  }

  .home-title {
    font-size: 42px;
  }
  
  .home-subtitle {
    font-size: 15px;
    padding: 0 10px;
  }
  
  .auth-card,
  .welcome-card {
    padding: 24px;
    max-width: 100%;
    margin-bottom: 40px;
  }

  .auth-btn {
    min-height: 48px;
    padding: 14px 24px;
  }

  .features-section {
    margin-top: 60px;
  }

  .features-header {
    margin-bottom: 32px;
  }

  .features-title {
    font-size: 28px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .feature-card {
    padding: 24px;
  }
}

/* Small mobile */
@media (max-width: 480px) {
  .home {
    padding: 12px 12px;
    padding-bottom: max(12px, env(safe-area-inset-bottom));
  }

  .home-header {
    margin-bottom: 28px;
    margin-top: 12px;
  }

  .logo-section {
    gap: 10px;
  }

  .logo-icon {
    font-size: 28px;
  }

  .home-title {
    font-size: 32px;
  }
  
  .home-subtitle {
    font-size: 13px;
  }
  
  .auth-card,
  .welcome-card {
    padding: 20px 16px;
    border-radius: 20px;
  }

  .auth-title,
  .welcome-header h2 {
    font-size: 24px;
  }

  .auth-subtitle {
    font-size: 13px;
  }

  .auth-btn {
    min-height: 48px;
    font-size: 14px;
  }

  .features-title {
    font-size: 22px;
  }

  .features-description {
    font-size: 14px;
  }

  .feature-card {
    padding: 20px 16px;
  }

  .feature-icon {
    font-size: 32px;
  }

  .feature-title {
    font-size: 17px;
  }

  .feature-description {
    font-size: 13px;
  }
}
</style>
