<template>
  <Transition name="modal">
    <div v-if="show" class="modal-mask">
      <div class="modal-wrapper" @click.self="$emit('close')">
        <div class="modal-container">
          <div class="modal-header">
            <h3>Reset Password</h3>
            <button class="close-btn" @click="$emit('close')">×</button>
          </div>

          <div class="modal-body">
            <div v-if="successMessage" class="success-message">
              {{ successMessage }}
            </div>
            <form v-else @submit.prevent="handleSubmit">
              <p class="instruction-text">
                Enter your email address and we will send you a link to reset your password.
              </p>
              
              <div class="form-group">
                <label for="reset-email">Email</label>
                <input 
                  type="email" 
                  id="reset-email" 
                  v-model="email" 
                  required 
                  placeholder="your.email@example.com"
                  :disabled="isLoading"
                >
              </div>

              <div v-if="error" class="error-message">
                {{ error }}
              </div>

              <button type="submit" class="submit-btn" :disabled="isLoading || !email">
                <span v-if="isLoading" class="loader"></span>
                <span v-else>Send Reset Link</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/services/api'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['close'])

const email = ref('')
const isLoading = ref(false)
const error = ref('')
const successMessage = ref('')

const handleSubmit = async () => {
  if (!email.value) return
  
  isLoading.value = true
  error.value = ''
  
  try {
    const response = await api.forgotPassword(email.value)
    successMessage.value = response.data.message || 'If an account with that email exists, a password reset link has been sent.'
  } catch (err) {
    error.value = err.response?.data?.detail || 'An error occurred. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.modal-mask {
  position: fixed;
  z-index: 9999;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  transition: opacity 0.3s ease;
}

.modal-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}

.modal-container {
  width: 400px;
  margin: 0px auto;
  padding: 20px 30px;
  background-color: #242424;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  transition: all 0.3s ease;
  border: 1px solid #333;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.instruction-text {
  color: #ccc;
  margin-bottom: 20px;
  font-size: 0.95rem;
  line-height: 1.5;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #ddd;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #444;
  background-color: #1a1a1a;
  color: #fff;
  border-radius: 4px;
  font-size: 1rem;
}

.form-group input:focus {
  outline: none;
  border-color: #646cff;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background-color: #646cff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 44px;
}

.submit-btn:hover:not(:disabled) {
  background-color: #535bf2;
}

.submit-btn:disabled {
  background-color: #444;
  cursor: not-allowed;
  opacity: 0.7;
}

.error-message {
  color: #ff6b6b;
  margin-bottom: 15px;
  font-size: 0.9rem;
}

.success-message {
  color: #51cf66;
  text-align: center;
  padding: 20px 0;
  font-size: 1.1rem;
  line-height: 1.5;
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

/* Modal transitions */
.modal-enter-from {
  opacity: 0;
}
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
