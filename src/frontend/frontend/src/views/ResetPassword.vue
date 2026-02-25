<template>
  <div class="reset-page">
    <div class="reset-card">
      <div class="card-header">
        <h2>Reset Password</h2>
        <p>Enter your new password below.</p>
      </div>
      
      <div v-if="success" class="success-message">
        <p>Password successfully reset!</p>
        <router-link to="/?login=true" class="login-link">Sign in with your new password</router-link>
      </div>

      <div v-else-if="!token" class="error-message">
        <p>Invalid or missing reset token.</p>
        <router-link to="/?login=true" class="login-link">Back to Login</router-link>
      </div>

      <form v-else @submit.prevent="handleReset" class="reset-form">
        <div class="form-group">
          <label for="new-password">New Password</label>
          <input 
            type="password" 
            id="new-password" 
            v-model="newPassword" 
            placeholder="Enter new password"
            required
            :disabled="isLoading"
            minlength="8"
          />
        </div>

        <div class="form-group">
          <label for="confirm-password">Confirm Password</label>
          <input 
            type="password" 
            id="confirm-password" 
            v-model="confirmPassword" 
            placeholder="Confirm new password"
            required
            :disabled="isLoading"
            minlength="8"
          />
        </div>

        <div v-if="error" class="error-message form-error">
          {{ error }}
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading || !isFormValid">
          <span v-if="isLoading" class="loader"></span>
          <span v-else>Reset Password</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()

const token = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const error = ref('')
const success = ref(false)

onMounted(() => {
  token.value = route.query.token || ''
})

const isFormValid = computed(() => {
  return newPassword.value.length >= 8 && newPassword.value === confirmPassword.value
})

const handleReset = async () => {
  if (!isFormValid.value) {
    error.value = "Passwords do not match or are too short."
    return
  }
  
  isLoading.value = true
  error.value = ''
  
  try {
    const response = await api.resetPassword(token.value, newPassword.value)
    success.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'An error occurred while resetting the password. The token may be expired.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.reset-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #121212;
  padding: 20px;
}

.reset-card {
  background: rgba(26, 26, 26, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  width: 100%;
  max-width: 440px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
}

.card-header h2 {
  color: #fff;
  font-size: 28px;
  margin: 0 0 10px 0;
}

.card-header p {
  color: #9ca3af;
  margin: 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #d1d5db;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.form-group input {
  width: 100%;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  transition: all 0.2s;
  box-sizing: border-box;
}

.form-group input:focus {
  outline: none;
  border-color: #4299e1;
  background: rgba(255, 255, 255, 0.08);
}

.submit-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 10px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(66, 153, 225, 0.3);
}

.submit-btn:disabled {
  background: #444;
  cursor: not-allowed;
  opacity: 0.7;
}

.error-message {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.1);
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.success-message {
  color: #51cf66;
  text-align: center;
  padding: 20px;
  background: rgba(81, 207, 102, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(81, 207, 102, 0.2);
}

.form-error {
  font-size: 14px;
}

.login-link {
  display: inline-block;
  margin-top: 15px;
  color: #4299e1;
  text-decoration: none;
  font-weight: 600;
}

.login-link:hover {
  text-decoration: underline;
}

.loader {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
