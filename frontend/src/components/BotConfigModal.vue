<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Configure {{ bot?.name }}</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>
      
      <div class="modal-body">
        <div class="config-section">
          <h3>Broker Selection</h3>
          <div class="form-group">
            <label for="broker-select">
              Select Broker *
              <span v-if="isFieldSaved('broker') || config.broker" class="filled-dot" title="Saved">●</span>
            </label>
            <select
              id="broker-select"
              v-model="config.broker"
              class="form-input"
              required
            >
              <option value="IG">IG Markets (CFD Trading)</option>
              <option value="Alpaca">Alpaca (Stock Trading)</option>
            </select>
          </div>

          <div v-if="config.broker === 'IG'">
            <h3>IG Markets Trading Account</h3>
          <p class="help-text">
            Configure your IG Markets account credentials for trading. We use perpetual money (perp) trading through IG Markets.
            Each bot can have its own IG account.
            <strong>These credentials are stored securely and only accessible by this bot.</strong>
          </p>
          
          <div class="form-group">
            <label for="ig-username">
              IG Username *

              <span v-if="isFieldSaved('ig_username') || config.ig_username" class="filled-dot" title="Saved">●</span>
            </label>
            <input
              id="ig-username"
              v-model="config.ig_username"
              type="text"
              :placeholder="isFieldSaved('ig_username') ? '••••••••' : 'Enter your IG Markets username'"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group">
            <label for="ig-password">
              IG Password *

              <span v-if="isFieldSaved('ig_password') || config.ig_password" class="filled-dot" title="Saved">●</span>
            </label>
            <input
              id="ig-password"
              v-model="config.ig_password"
              type="password"
              :placeholder="isFieldSaved('ig_password') ? '••••••••' : 'Enter your IG Markets password'"
              class="form-input"
              required
            />
          </div>
          
          <div class="form-group">
            <label for="ig-api-key">
              IG API Key *

              <span v-if="isFieldSaved('ig_api_key') || config.ig_api_key" class="filled-dot" title="Saved">●</span>
            </label>
            <input
              id="ig-api-key"
              v-model="config.ig_api_key"
              type="password"
              :placeholder="isFieldSaved('ig_api_key') ? '••••••••' : 'Enter your IG Markets API Key'"
              class="form-input"
              required
            />
            <p class="field-help">Get your API key from IG Markets platform settings</p>
          </div>
          
          <div class="form-group">
            <label for="ig-acc-type">
              Account Type *

              <span v-if="isFieldSaved('ig_acc_type') || config.ig_acc_type" class="filled-dot" title="Saved">●</span>
            </label>
            <select
              id="ig-acc-type"
              v-model="config.ig_acc_type"
              class="form-input"
              required
            >
              <option value="DEMO">DEMO (Paper Trading)</option>
              <option value="LIVE">LIVE (Real Trading)</option>
            </select>
            <p class="field-help">Start with DEMO account for testing</p>
          </div>
          </div>

          <div v-if="config.broker === 'Alpaca'">
            <h3>Alpaca Trading Account</h3>
            <p class="help-text">
              Configure your Alpaca account credentials.
              <strong>These credentials are stored securely and only accessible by this bot.</strong>
            </p>

            <div class="form-group">
              <label for="alpaca-api-key">
                Alpaca API Key *
                <span v-if="isFieldSaved('alpaca_api_key') || config.alpaca_api_key" class="filled-dot" title="Saved">●</span>
              </label>
              <input
                id="alpaca-api-key"
                v-model="config.alpaca_api_key"
                type="password"
                :placeholder="isFieldSaved('alpaca_api_key') ? '••••••••' : 'Enter your Alpaca API Key'"
                class="form-input"
                required
              />
            </div>

            <div class="form-group">
              <label for="alpaca-api-secret">
                Alpaca Secret Key *
                <span v-if="isFieldSaved('alpaca_api_secret') || config.alpaca_api_secret" class="filled-dot" title="Saved">●</span>
              </label>
              <input
                id="alpaca-api-secret"
                v-model="config.alpaca_api_secret"
                type="password"
                :placeholder="isFieldSaved('alpaca_api_secret') ? '••••••••' : 'Enter your Alpaca Secret Key'"
                class="form-input"
                required
              />
            </div>

            <div class="form-group">
              <label for="alpaca-paper">
                Account Type *
                <span v-if="isFieldSaved('alpaca_paper') || config.alpaca_paper !== undefined" class="filled-dot" title="Saved">●</span>
              </label>
              <select
                id="alpaca-paper"
                v-model="config.alpaca_paper"
                class="form-input"
                required
              >
                <option :value="true">Paper Trading (Demo)</option>
                <option :value="false">Live Trading</option>
              </select>
            </div>
          </div>
        </div>
        
        <div class="config-section">
          <h3>AI Analysis (Google Gemini)</h3>
          <p class="help-text">
            Gemini AI is used to analyze earnings safety and recommend capital allocation for trading decisions.
            <strong>Required</strong> for the bot to function properly.
          </p>
          
          <div class="form-group">
            <label for="gemini-api-key">
              Google Gemini API Key *

              <span v-if="isFieldSaved('gemini_api_key') || config.gemini_api_key" class="filled-dot" title="Saved">●</span>
            </label>
            <input
              id="gemini-api-key"
              v-model="config.gemini_api_key"
              type="password"
              :placeholder="isFieldSaved('gemini_api_key') ? '••••••••' : 'Enter your Google Gemini API Key'"
              class="form-input"
              required
            />
            <p class="field-help">Get your API key from <a href="https://ai.google.dev/" target="_blank" rel="noopener noreferrer">Google AI Studio</a></p>
          </div>
        </div>
        
        <div class="config-section">
          <h3>Earnings Reports</h3>
          <p class="help-text">
            Earnings data is provided free via Nasdaq API (no API key needed, cached for 12 hours)
          </p>
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-if="success" class="success-message">
          Configuration saved successfully!
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="close">Cancel</button>
        <button class="btn btn-primary" @click="saveConfig" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Configuration' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  bot: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'saved'])

const config = ref({
  broker: 'IG',
  ig_username: '',
  ig_password: '',
  ig_api_key: '',
  ig_acc_type: 'DEMO',
  gemini_api_key: '',
  alpaca_api_key: '',
  alpaca_api_secret: '',
  alpaca_paper: true
})

const saving = ref(false)
const error = ref(null)
const success = ref(false)

watch(() => props.show, (newVal) => {
  if (newVal && props.bot) {
    // Load existing config if any
    if (props.bot.config) {
      try {
        const existingConfig = typeof props.bot.config === 'string' 
          ? JSON.parse(props.bot.config) 
          : props.bot.config
        config.value = {
          broker: existingConfig.broker || 'IG',
          ig_username: existingConfig.ig_username || '',
          ig_password: existingConfig.ig_password || '',
          ig_api_key: existingConfig.ig_api_key || '',
          ig_acc_type: existingConfig.ig_acc_type || 'DEMO',
          gemini_api_key: existingConfig.gemini_api_key || '',
          alpaca_api_key: existingConfig.alpaca_api_key || '',
          alpaca_api_secret: existingConfig.alpaca_api_secret || '',
          alpaca_paper: existingConfig.alpaca_paper !== undefined ? existingConfig.alpaca_paper : true
        }
      } catch (e) {
        console.error('Error parsing bot config:', e)
      }
      } else {
        config.value = {
          broker: 'IG',
          ig_username: '',
          ig_password: '',
          ig_api_key: '',
          ig_acc_type: 'DEMO',
          gemini_api_key: '',
          alpaca_api_key: '',
          alpaca_api_secret: '',
          alpaca_paper: true
        }
      }
    error.value = null
    success.value = false
  }
})

const close = () => {
  emit('close')
}

const isFieldSaved = (fieldName) => {
  if (!props.bot || !props.bot.configured_fields) return false
  return props.bot.configured_fields.includes(fieldName)
}

const saveConfig = async () => {
  if (!props.bot) return
  
  // Validate required fields based on broker
  if (config.value.broker === 'IG') {
    if (!config.value.ig_username || !config.value.ig_password || !config.value.ig_api_key) {
      error.value = 'Please fill in all required IG Markets fields (Username, Password, API Key)'
      return
    }
  } else if (config.value.broker === 'Alpaca') {
    if (!config.value.alpaca_api_key || !config.value.alpaca_api_secret) {
      error.value = 'Please fill in all required Alpaca fields (API Key, Secret Key)'
      return
    }
  }
  
  if (!config.value.gemini_api_key) {
    error.value = 'Please fill in the Google Gemini API Key (required for AI analysis)'
    return
  }
  
  saving.value = true
  error.value = null
  success.value = false
  
  try {
    await api.updateBotConfig(props.bot.id, {
      broker: config.value.broker,
      ig_username: config.value.ig_username,
      ig_password: config.value.ig_password,
      ig_api_key: config.value.ig_api_key,
      ig_acc_type: config.value.ig_acc_type || 'DEMO',
      gemini_api_key: config.value.gemini_api_key || undefined,
      alpaca_api_key: config.value.alpaca_api_key || undefined,
      alpaca_api_secret: config.value.alpaca_api_secret || undefined,
      alpaca_paper: config.value.alpaca_paper
    })
    
    success.value = true
    setTimeout(() => {
      emit('saved')
      close()
    }, 1000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save configuration'
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
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #2d3748;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #4a5568;
}

.modal-header h2 {
  margin: 0;
  color: #e2e8f0;
  font-size: 24px;
}

.close-btn {
  background: none;
  border: none;
  color: #a0aec0;
  font-size: 32px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #e2e8f0;
}

.modal-body {
  padding: 24px;
}

.config-section {
  margin-bottom: 32px;
}

.config-section h3 {
  color: #e2e8f0;
  margin: 0 0 12px 0;
  font-size: 18px;
}

.help-text {
  color: #a0aec0;
  font-size: 14px;
  margin-bottom: 16px;
  line-height: 1.5;
}

.help-text a {
  color: #4299e1;
  text-decoration: none;
}

.help-text a:hover {
  text-decoration: underline;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  color: #cbd5e0;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filled-dot {
  color: #68d391;
  font-size: 12px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.6; }
  100% { opacity: 1; }
}

.form-input {
  width: 100%;
  padding: 12px;
  background: #1a202c;
  border: 1px solid #4a5568;
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #4299e1;
}

.form-input[type="password"],
.form-input[type="text"] {
  font-family: monospace;
}

select.form-input {
  cursor: pointer;
}

.field-help {
  margin-top: 4px;
  font-size: 12px;
  color: #718096;
  font-style: italic;
}

.field-help a {
  color: #4299e1;
  text-decoration: none;
}

.field-help a:hover {
  text-decoration: underline;
}

.error-message {
  background: #4a2a2a;
  border: 1px solid #fc8181;
  color: #fc8181;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.success-message {
  background: #2d5016;
  border: 1px solid #68d391;
  color: #68d391;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid #4a5568;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #4a5568;
  color: #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #718096;
}

.btn-primary {
  background: #4299e1;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #3182ce;
}
</style>


