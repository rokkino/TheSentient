<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Settings</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <div class="settings-form">
          <div class="form-group">
            <label>AI Provider</label>
            <select v-model="settings.ai_provider" class="form-select">
              <option value="gemini">Google Gemini (Flash/Free)</option>
              <option value="gemini_pro">Google Gemini Pro (Paid)</option>
              <option value="openai">ChatGPT (OpenAI)</option>
              <option value="anthropic">Claude (Anthropic)</option>
              <option value="deepseek">Deepseek</option>
              <option value="local">Local Llama (Ollama)</option>
            </select>
          </div>

          <!-- Gemini Free -->
          <div v-if="settings.ai_provider === 'gemini'" class="form-group">
            <label>Gemini API Key (Free)</label>
            <input type="password" v-model="settings.gemini_api_key" placeholder="Enter Gemini Flash Key" />
            <small>Get it from Google AI Studio</small>
          </div>

          <!-- Gemini Pro -->
          <div v-if="settings.ai_provider === 'gemini_pro'" class="form-group">
            <label>Gemini Pro API Key</label>
            <input type="password" v-model="settings.gemini_pro_api_key" placeholder="Enter Gemini Pro Key" />
          </div>

          <!-- OpenAI -->
          <div v-if="settings.ai_provider === 'openai'" class="form-group">
            <label>OpenAI API Key</label>
            <input type="password" v-model="settings.openai_api_key" placeholder="sk-..." />
          </div>

          <!-- Anthropic -->
          <div v-if="settings.ai_provider === 'anthropic'" class="form-group">
            <label>Anthropic API Key</label>
            <input type="password" v-model="settings.anthropic_api_key" placeholder="sk-ant-..." />
          </div>

          <!-- Deepseek -->
          <div v-if="settings.ai_provider === 'deepseek'" class="form-group">
            <label>Deepseek API Key</label>
            <input type="password" v-model="settings.deepseek_api_key" placeholder="Enter Deepseek Key" />
          </div>

          <!-- Local Llama -->
          <div v-if="settings.ai_provider === 'local'" class="form-group">
            <div class="info-box">
              <p>Using local Ollama instance at http://localhost:11434</p>
              <p>Model: llama3.2:1b (default)</p>
            </div>
          </div>

          <div class="form-group toggle-group">
             <label class="switch">
                <input type="checkbox" v-model="settings.use_local_llama">
                <span class="slider round"></span>
             </label>
             <span>Use Local Llama for Background Tasks</span>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="saveSettings" class="save-button" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['close'])
const saving = ref(false)
const settings = ref({
  ai_provider: 'gemini',
  gemini_api_key: '',
  gemini_pro_api_key: '',
  openai_api_key: '',
  anthropic_api_key: '',
  deepseek_api_key: '',
  use_local_llama: false
})

onMounted(async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return

    const response = await fetch('http://localhost:8000/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      settings.value = {
        ai_provider: data.ai_provider || 'gemini',
        gemini_api_key: data.gemini_api_key || '',
        gemini_pro_api_key: data.gemini_pro_api_key || '',
        openai_api_key: data.openai_api_key || '',
        anthropic_api_key: data.anthropic_api_key || '',
        deepseek_api_key: data.deepseek_api_key || '',
        use_local_llama: data.use_local_llama || false
      }
    }
  } catch (e) {
    console.error('Failed to load settings:', e)
  }
})

const saveSettings = async () => {
  saving.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('http://localhost:8000/api/auth/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(settings.value)
    })

    if (response.ok) {
      emit('close')
    } else {
      alert('Failed to save settings')
    }
  } catch (e) {
    console.error('Error saving settings:', e)
    alert('Error saving settings')
  } finally {
    saving.value = false
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
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background-color: #1a1a1a;
  border-radius: 12px;
  width: 500px;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  border: 1px solid #333;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #333;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5px;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
  background-color: #333;
}

.modal-body {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.settings-form {
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
  color: #ccc;
  font-size: 14px;
  font-weight: 500;
}

.form-select, input[type="text"], input[type="password"] {
  background-color: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 10px 12px;
  color: #fff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.form-select:focus, input:focus {
  border-color: #2196F3;
}

.form-group small {
  color: #666;
  font-size: 12px;
}

.info-box {
  background-color: #2a2a2a;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 12px;
}

.info-box p {
  margin: 0;
  color: #888;
  font-size: 13px;
}

.toggle-group {
  flex-direction: row;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

/* Switch Toggle */
.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #444;
  transition: .4s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
}

input:checked + .slider {
  background-color: #2196F3;
}

input:checked + .slider:before {
  transform: translateX(16px);
}

.slider.round {
  border-radius: 34px;
}

.slider.round:before {
  border-radius: 50%;
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid #333;
  display: flex;
  justify-content: flex-end;
}

.save-button {
  padding: 10px 24px;
  border-radius: 6px;
  border: none;
  background-color: #2196F3;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.save-button:hover {
  background-color: #1976D2;
}

.save-button:disabled {
  background-color: #444;
  cursor: not-allowed;
}
</style>
