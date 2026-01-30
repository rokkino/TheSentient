<template>
  <div class="modal-overlay">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <div class="modal-header-content">
          <h2 class="modal-title">Sign In</h2>
          <p class="modal-subtitle">Access your trading platform</p>
        </div>
        <button class="close-btn" @click="$emit('close')" aria-label="Close">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      
      <div class="modal-body">
        <div v-if="error" class="error-message">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 5V8M8 11H8.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span>{{ error }}</span>
        </div>
        
        <form @submit.prevent="handleLogin" class="auth-form">
          <div class="form-group">
            <label for="username">Username</label>
            <div class="input-wrapper">
              <input
                id="username"
                v-model="username"
                type="text"
                placeholder="Enter your username"
                @keyup.enter="handleLogin"
                :disabled="loading"
                autocomplete="username"
                required
              />
            </div>
          </div>
          
          <div class="form-group">
            <label for="password">Password</label>
            <div class="input-wrapper">
              <input
                id="password"
                v-model="password"
                type="password"
                placeholder="Enter your password"
                @keyup.enter="handleLogin"
                :disabled="loading"
                autocomplete="current-password"
                required
              />
            </div>
          </div>
          
          <button 
            type="submit" 
            class="submit-btn" 
            :disabled="loading || !username || !password"
          >
            <span v-if="!loading">Sign In</span>
            <span v-else class="loading-text">
              <span class="spinner"></span>
              Signing in...
            </span>
          </button>
        </form>
      </div>
      
      <div class="modal-footer">
        <p class="switch-text">
          Don't have an account?
          <button @click="$emit('switch-to-register')" class="switch-link">Create one</button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits(['close', 'login-success', 'switch-to-register'])

const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref(null)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    error.value = 'Please enter username and password'
    return
  }

  loading.value = true
  error.value = null

  try {
    const result = await authStore.login(username.value, password.value)
    if (result.success) {
      emit('login-success')
    } else {
      error.value = result.error || 'Login failed'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: rgba(26, 26, 26, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  width: 100%;
  max-width: 440px;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 32px 32px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.modal-header-content {
  flex: 1;
}

.modal-title {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 6px 0;
  letter-spacing: -0.5px;
}

.modal-subtitle {
  font-size: 14px;
  color: #9ca3af;
  margin: 0;
  font-weight: 400;
}

.close-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #9ca3af;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.15);
}

.modal-body {
  padding: 32px;
  flex: 1;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 24px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #d1d5db;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #ffffff;
  font-size: 15px;
  font-weight: 400;
  transition: all 0.2s;
  font-family: inherit;
}

.input-wrapper input::placeholder {
  color: #6b7280;
}

.input-wrapper input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.08);
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.input-wrapper input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn {
  width: 100%;
  padding: 14px 24px;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
  letter-spacing: 0.3px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(66, 153, 225, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.modal-footer {
  padding: 24px 32px 32px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.switch-text {
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
  margin: 0;
}

.switch-link {
  background: none;
  border: none;
  color: #4299e1;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  padding: 0;
  margin-left: 4px;
  text-decoration: none;
  transition: color 0.2s;
}

.switch-link:hover {
  color: #3182ce;
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 480px) {
  .modal-content {
    max-width: 100%;
    margin: 20px;
    border-radius: 20px;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 24px;
  }
}
</style>
