<template>
  <div v-if="show" class="modal-overlay">
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
              <span v-if="isFieldSaved('broker')" class="saved-badge" title="Saved">✓ Saved</span>
            </label>
            <select
              id="broker-select"
              v-model="config.broker"
              class="form-input"
              required
            >
              <option value="Alpaca">Alpaca (Stock Trading)</option>
              <option value="InteractiveBrokers">Interactive Brokers (TWS/Gateway)</option>
              <option value="Plus500">Plus500 (Coming Soon)</option>
              <option value="Binance">Binance (Crypto - Coming Soon)</option>
              <option value="XTB">XTB (Coming Soon)</option>
              <option value="Pepperstone">Pepperstone (Coming Soon)</option>
            </select>
          </div>

          <!-- Account Selection (Global) -->
           <div class="form-group" v-if="filteredAccounts.length > 0">
            <label>
              Use Saved Account
              <span v-if="config.account_id" class="saved-badge">Linked</span>
            </label>
            <select v-model="config.account_id" class="form-input">
              <option :value="null">-- Manual Configuration --</option>
              <option v-for="acc in filteredAccounts" :key="acc.id" :value="acc.id">
                {{ acc.name }} ({{ acc.platform }})
              </option>
            </select>
            <p class="field-help" v-if="config.account_id">
              Using credentials from your saved account. Manual fields below are hidden.
            </p>
          </div>

          <div v-if="['Plus500', 'Binance', 'XTB', 'Pepperstone'].includes(config.broker)" class="info-message">
            <p><strong>{{ config.broker }} integration is coming soon!</strong></p>
            <p>You can save this selection, but trading features are not yet available for this broker.</p>
          </div>

          <div v-if="config.broker === 'InteractiveBrokers' && !config.account_id" class="info-message">
            <p><strong>Interactive Brokers Configuration</strong></p>
            <p>Per usare Interactive Brokers, devi avere TWS (Trader Workstation) o IB Gateway in esecuzione sul tuo computer.</p>
            <p>Aggiungi un account IB nel tuo Profilo > Accounts per configurare host, porta e altre impostazioni.</p>
          </div>


          <div v-if="!config.account_id && config.broker === 'Alpaca'" class="info-message">
            <p><strong>Please select a linked account</strong></p>
            <p>Manual credential entry has been deprecated. Please add an account in your Profile > Accounts tab and select it above.</p>
          </div>
        </div>

        <div class="config-section">
          <h3>Risk Management</h3>
          <div class="form-group">
            <label>
              Daily Budget Allocation (%)
              <span class="saved-badge" v-if="isFieldSaved('daily_budget_pct')">✓ Saved</span>
            </label>
            <div style="display: flex; align-items: center; gap: 12px;">
              <input 
                type="range" 
                v-model.number="config.daily_budget_pct" 
                min="1" 
                max="100" 
                step="1"
                style="flex: 1;"
              >
              <span style="color: #e2e8f0; font-family: monospace; min-width: 40px;">{{ config.daily_budget_pct }}%</span>
            </div>
            <p class="field-help">Percentage of total account balance to use for daily trades.</p>
          </div>

          <div class="form-group">
             <label style="flex-direction: row; cursor: pointer;">
                <input type="checkbox" v-model="config.use_confidence_sizing">
                <span>Use Confidence-Based Sizing</span>
             </label>
             <p class="field-help">If enabled, allocates more capital to trades with higher AI confidence scores.</p>
          </div>
        </div>
        
        <div class="config-section">
          <h3>Earnings Reports</h3>
          <p class="help-text">
            Earnings data is provided free via Nasdaq API (no API key needed, cached for 12 hours)
          </p>
        </div>
        
        <div v-if="testResult" :class="['test-result', testResult.success ? 'success' : 'error']">
          <strong>{{ testResult.success ? '✓ Connection Successful' : '✗ Connection Failed' }}</strong>
          <p>{{ testResult.message }}</p>
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
        <button 
          class="btn btn-info" 
          @click="testConnection" 
          :disabled="testing || saving"
          style="margin-right: auto;"
        >
          {{ testing ? 'Testing...' : 'Test Connection' }}
        </button>
        <button class="btn btn-primary" @click="saveConfig" :disabled="saving || testing">
          {{ saving ? 'Saving...' : 'Save Configuration' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
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
  account_id: null,
  ig_username: '',
  ig_password: '',
  ig_api_key: '',
  ig_acc_type: 'DEMO',
  alpaca_api_key: '',
  alpaca_api_secret: '',
  alpaca_paper: true
})

const accounts = ref([])
const loadingAccounts = ref(false)

const loadAccounts = async () => {
  try {
    const res = await api.getAccounts()
    accounts.value = res.data.accounts
  } catch (e) {
    console.error("Failed to load accounts", e)
  }
}

onMounted(() => {
  loadAccounts()
})

const filteredAccounts = computed(() => {
  return accounts.value.filter(acc => acc.platform === config.value.broker && acc.is_active)
})

const saving = ref(false)
const testing = ref(false)
const error = ref(null)
const success = ref(false)
const testResult = ref(null)

watch(() => props.show, (newVal) => {
  if (newVal && props.bot) {
    // Refresh accounts every time modal opens
    loadAccounts()

    // Load existing config if any
    if (props.bot.config) {
      try {
        const existingConfig = typeof props.bot.config === 'string' 
          ? JSON.parse(props.bot.config) 
          : props.bot.config
        config.value = {
          broker: existingConfig.broker || 'IG',
          account_id: existingConfig.account_id || null,
          ig_username: existingConfig.ig_username || '',
          ig_password: existingConfig.ig_password || '',
          ig_api_key: existingConfig.ig_api_key || '',
          ig_acc_type: existingConfig.ig_acc_type || 'DEMO',
          alpaca_api_key: existingConfig.alpaca_api_key || '',
          alpaca_api_secret: existingConfig.alpaca_api_secret || '',
          alpaca_paper: existingConfig.alpaca_paper !== undefined ? existingConfig.alpaca_paper : true,
          daily_budget_pct: existingConfig.daily_budget_pct || 50,
          use_confidence_sizing: existingConfig.use_confidence_sizing !== undefined ? existingConfig.use_confidence_sizing : true
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
          alpaca_api_key: '',
          alpaca_api_secret: '',
          alpaca_paper: true,
          daily_budget_pct: 50,
          use_confidence_sizing: true
        }
      }
    error.value = null
    success.value = false
    testResult.value = null
  }
})

const close = () => {
  emit('close')
}

const isFieldSaved = (fieldName) => {
  if (!props.bot || !props.bot.configured_fields) return false
  // Check if field is in configured_fields AND has a non-empty value
  if (!props.bot.configured_fields.includes(fieldName)) return false
  
  // Also verify that the value exists and is not empty in the saved config
  if (props.bot.config && props.bot.config[fieldName]) {
    const value = props.bot.config[fieldName]
    return value !== null && value !== undefined && value !== ''
  }
  
  // If config is not loaded but field is in configured_fields, assume it's saved
  return true
}

const testConnection = async () => {
  testing.value = true
  testResult.value = null
  error.value = null
  
  try {
    // Merge form values with saved config values
    // Use saved values if form values are empty
    const testConfig = { ...config.value }
    // Legacy support logic removed - relies on backend resolving account_id
    
    const res = await api.testBotConnection({
      broker: testConfig.broker,
      config: testConfig
    })
    
    testResult.value = {
      success: res.data.success,
      message: res.data.message
    }
  } catch (err) {
    testResult.value = {
      success: false,
      message: err.response?.data?.message || err.message || 'Connection test failed'
    }
  } finally {
    testing.value = false
  }
}

const saveConfig = async () => {
  if (!props.bot) return
  
  // Validate required fields based on broker (only if no global account used)
  // Validate required fields based on broker
  if ((config.value.broker === 'IG' || config.value.broker === 'Alpaca' || config.value.broker === 'InteractiveBrokers') && !config.value.account_id) {
    error.value = 'Please select a linked account.'
    return
  }
  

  
  saving.value = true
  error.value = null
  success.value = false
  
  try {
    await api.updateBotConfig(props.bot.id, {
      broker: config.value.broker,
      account_id: config.value.account_id,
      ig_username: config.value.ig_username,
      ig_password: config.value.ig_password,
      ig_api_key: config.value.ig_api_key,
      ig_acc_type: config.value.ig_acc_type || 'DEMO',
      alpaca_api_key: config.value.alpaca_api_key || undefined,
      alpaca_api_secret: config.value.alpaca_api_secret || undefined,
      alpaca_paper: config.value.alpaca_paper,
      daily_budget_pct: config.value.daily_budget_pct,
      use_confidence_sizing: config.value.use_confidence_sizing
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
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--glass-bg, rgba(30, 41, 59, 0.5));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-lg, 24px);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-glass, 0 25px 50px -12px rgba(0, 0, 0, 0.5));
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  background: transparent;
}

.modal-header h2 {
  margin: 0;
  color: #e2e8f0;
  font-size: 24px;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary, #94a3b8);
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
  color: var(--text-primary, #e2e8f0);
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

.saved-badge {
  color: #68d391;
  font-size: 11px;
  background: rgba(104, 211, 145, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(104, 211, 145, 0.2);
  display: inline-flex;
  align-items: center;
  font-weight: 600;
}

.form-input {
  width: 100%;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm, 12px);
  color: var(--text-primary, #e2e8f0);
  font-size: 14px;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--accent-primary, #3b82f6);
  box-shadow: 0 0 0 3px var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
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
  border-top: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  background: transparent;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-sm, 12px);
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
  background: transparent;
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  color: var(--text-secondary, #94a3b8);
}

.btn-secondary:hover:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.2);
  color: var(--text-primary, #e2e8f0);
}

.btn-primary {
  background: var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}

.btn-primary:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.25);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.2);
  transform: translateY(-1px);
}

.btn-info {
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.btn-info:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
  transform: translateY(-1px);
}

.info-message {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  padding: 16px;
  border-radius: var(--radius-md, 16px);
  margin-bottom: 24px;
  font-size: 14px;
}

.test-result {
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.test-result.success {
  background: #2d5016;
  border: 1px solid #68d391;
  color: #68d391;
}

.test-result.error {
  background: #4a2a2a;
  border: 1px solid #fc8181;
  color: #fc8181;
}
</style>


