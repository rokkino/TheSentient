<template>
  <div class="backtesting-panel">
    <!-- Grey sidebar with settings -->
    <aside class="bt-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? 'Apri configurazione' : 'Chiudi configurazione'">
        {{ sidebarCollapsed ? '»' : '«' }}
      </button>

      <template v-if="!sidebarCollapsed">
        <div class="sidebar-header">
          <span class="sidebar-icon">⚙️</span>
          <h3>Configurazione</h3>
        </div>

        <div class="sidebar-field">
          <label class="sidebar-label">Bot</label>
          <select v-model="selectedBotId" class="sidebar-select" :disabled="readOnly">
            <option :value="null">-- Seleziona un bot --</option>
            <option v-for="b in bots" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </div>

        <div class="sidebar-field">
          <label class="sidebar-label">Data backtest</label>
          <input
            v-model="selectedDate"
            type="date"
            class="sidebar-input"

            :disabled="readOnly"
          />
        </div>

        <div class="sidebar-divider"></div>

        <div class="sidebar-field">
          <label class="sidebar-label">Universo ticker</label>
          <select v-model="universe" class="sidebar-select" :disabled="readOnly">
            <option value="S&P 500">S&P 500</option>
            <option value="Nasdaq 100">Nasdaq 100</option>
          </select>
        </div>

        <div class="sidebar-field">
          <label class="sidebar-label">Anno inizio</label>
          <div class="sidebar-number-row">
            <button class="sidebar-num-btn" @click="startYear = Math.max(2015, startYear - 1)" :disabled="readOnly">–</button>
            <input v-model.number="startYear" type="number" min="2015" max="2026" class="sidebar-input sidebar-num-input" :disabled="readOnly" />
            <button class="sidebar-num-btn" @click="startYear = Math.min(2026, startYear + 1)" :disabled="readOnly">+</button>
          </div>
        </div>

        <div class="sidebar-field">
          <label class="sidebar-label">Anno fine</label>
          <div class="sidebar-number-row">
            <button class="sidebar-num-btn" @click="endYear = Math.max(2015, endYear - 1)" :disabled="readOnly">–</button>
            <input v-model.number="endYear" type="number" min="2015" max="2026" class="sidebar-input sidebar-num-input" :disabled="readOnly" />
            <button class="sidebar-num-btn" @click="endYear = Math.min(2026, endYear + 1)" :disabled="readOnly">+</button>
          </div>
        </div>

        <div class="sidebar-field">
          <label class="sidebar-label">Capitale per trade ($)</label>
          <div class="sidebar-number-row">
            <button class="sidebar-num-btn" @click="capitalPerTrade = Math.max(100, capitalPerTrade - 100)" :disabled="readOnly">–</button>
            <input v-model.number="capitalPerTrade" type="number" min="100" max="10000" class="sidebar-input sidebar-num-input" :disabled="readOnly" />
            <button class="sidebar-num-btn" @click="capitalPerTrade = Math.min(10000, capitalPerTrade + 100)" :disabled="readOnly">+</button>
          </div>
        </div>

        <div class="sidebar-field">
          <label class="sidebar-label">Confidence minima bot (%)</label>
          <div class="sidebar-slider-value">{{ minConfidence }}</div>
          <input v-model.number="minConfidence" type="range" min="0" max="80" class="sidebar-slider" :disabled="readOnly" />
        </div>

        <div class="sidebar-field">
          <label class="sidebar-label">Limite Tickers (0 = tutti)</label>
          <div class="sidebar-number-row">
            <button class="sidebar-num-btn" @click="limitTickers = Math.max(0, limitTickers - 10)" :disabled="readOnly">–</button>
            <input v-model.number="limitTickers" type="number" min="0" max="500" class="sidebar-input sidebar-num-input" :disabled="readOnly" />
            <button class="sidebar-num-btn" @click="limitTickers = Math.min(500, limitTickers + 10)" :disabled="readOnly">+</button>
          </div>
        </div>



        <div class="sidebar-strategy-hint">
          Strategy: Buy day before earnings (Pre-market) or day of earnings (Post-market). Sell next open.
        </div>
      </template>
    </aside>

    <!-- Main content area -->
    <div class="backtesting-main">
      <!-- Fallback quando Streamlit non è raggiungibile -->
      <div v-if="!streamlitReady" class="embed-container fallback">
        <div class="fallback-content">
          <div class="fallback-icon">📊</div>
          <h3>Dashboard di backtesting non raggiungibile</h3>
          <p>Avvia la dashboard Streamlit per visualizzare la simulazione.</p>
          <code>cd streamlit_app && streamlit run app.py</code>
          <p class="fallback-hint">Oppure usa <strong>start-dev.bat</strong> per avviare tutti i servizi.</p>
          <div class="fallback-buttons">
            <button class="retry-btn" @click="verifyAndRetry" :disabled="checking">
              {{ checking ? 'Verifica...' : 'Verifica' }}
            </button>
            <button type="button" class="show-anyway-btn" @click="showAnyway">
              Mostra dashboard comunque
            </button>
          </div>
          <p v-if="autoRetryActive" class="auto-retry-hint">Riprovo automaticamente ogni 5 secondi…</p>
        </div>
      </div>
      <!-- Iframe quando Streamlit è attivo -->
      <div v-else class="embed-container">
        <iframe
          ref="btIframe"
          :key="streamlitEmbedUrl"
          :src="streamlitEmbedUrl"
          class="backtesting-iframe"
          title="Backtesting Dashboard"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { getApiBase } from '../utils/env.js'
import api from '../services/api'

const props = defineProps({
  sharedState: {
    type: Object,
    default: null
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['state-change'])

const streamlitBaseUrl = ref(import.meta.env.VITE_STREAMLIT_URL || 'http://localhost:8501')
const streamlitEmbedUrl = ref('')
const streamlitReady = ref(false)
const checking = ref(false)
const autoRetryActive = ref(false)
let retryTimer = null
const bots = ref([])
const selectedBotId = ref(null)
const selectedDate = ref('')
const sidebarCollapsed = ref(false)
const btIframe = ref(null)

// Backtest config (mirrored from Streamlit sidebar)
const universe = ref('S&P 500')
const startYear = ref(2024)
const endYear = ref(2024)
const capitalPerTrade = ref(1000)
const minConfidence = ref(30)
const limitTickers = ref(50)

const applyingSharedState = ref(false)
let stateEmitTimer = null

const queueStateChange = () => {
  if (applyingSharedState.value) return
  if (stateEmitTimer) clearTimeout(stateEmitTimer)
  stateEmitTimer = setTimeout(() => {
    emit('state-change', {
      selectedBotId: selectedBotId.value,
      selectedDate: selectedDate.value
    })
  }, 150)
}

const applySharedState = (state) => {
  if (!state) return
  applyingSharedState.value = true
  if ('selectedBotId' in state) selectedBotId.value = state.selectedBotId
  if ('selectedDate' in state) selectedDate.value = state.selectedDate || ''
  updateEmbedUrl()
  nextTick(() => {
    applyingSharedState.value = false
  })
}

function getEmbedUrl() {
  const base = streamlitBaseUrl.value.replace(/\/$/, '')
  const params = new URLSearchParams()
  params.set('embed', 'true')
  if (selectedBotId.value != null && selectedBotId.value !== '') {
    params.set('bot_id', String(selectedBotId.value))
  }
  if (selectedDate.value) {
    params.set('date', selectedDate.value)
  }
  // Pass all backtest config to Streamlit
  params.set('universe', universe.value)
  params.set('start_year', String(startYear.value))
  params.set('end_year', String(endYear.value))
  params.set('capital', String(capitalPerTrade.value))
  params.set('min_confidence', String(minConfidence.value))
  params.set('limit', String(limitTickers.value))
  return `${base}/?${params.toString()}`
}

function updateEmbedUrl() {
  streamlitEmbedUrl.value = getEmbedUrl()
  queueStateChange()
}

function sendConfigToIframe() {
  const iframe = btIframe.value
  if (!iframe || !iframe.contentWindow) return
  iframe.contentWindow.postMessage({
    type: 'updateBacktestConfig',
    config: {
      universe: universe.value,
      start_year: startYear.value,
      end_year: endYear.value,
      capital: capitalPerTrade.value,
      min_confidence: minConfidence.value,
      limit: limitTickers.value,
      bot_id: selectedBotId.value,
      date: selectedDate.value
    }
  }, '*')
}

let configDebounceTimer = null
const configSnapshot = computed(() => JSON.stringify([
  universe.value, startYear.value, endYear.value,
  capitalPerTrade.value, minConfidence.value, limitTickers.value,
  selectedBotId.value, selectedDate.value
]))

watch(configSnapshot, () => {
  if (applyingSharedState.value) return
  if (configDebounceTimer) clearTimeout(configDebounceTimer)
  configDebounceTimer = setTimeout(() => {
    sendConfigToIframe()
    queueStateChange()
  }, 600)
})

function showAnyway() {
  streamlitReady.value = true
  updateEmbedUrl()
  if (retryTimer) {
    clearInterval(retryTimer)
    retryTimer = null
    autoRetryActive.value = false
  }
}

async function loadBots() {
  try {
    const res = await api.getBots()
    bots.value = res.data?.bots ?? []
  } catch {
    bots.value = []
  }
}

async function startStreamlit() {
  const apiBase = getApiBase()
  const url = apiBase.replace(/\/$/, '') + '/streamlit-start'
  try {
    const res = await fetch(url, { method: 'POST' })
    const data = await res.json()
    return data?.started === true || data?.already_running === true
  } catch {
    return false
  }
}

async function verifyAndRetry() {
  await startStreamlit()
  await checkStreamlit()
  if (!streamlitReady.value) startAutoRetry()
}

async function checkStreamlit(resetBefore = true) {
  checking.value = true
  if (resetBefore) streamlitReady.value = false
  try {
    const apiBase = getApiBase()
    const url = (apiBase.replace(/\/$/, '') + '/streamlit-health')
    const res = await fetch(url)
    const data = await res.json()
    const running = data?.running === true
    if (running) {
      streamlitReady.value = true
      if (data?.url) streamlitBaseUrl.value = data.url
      updateEmbedUrl()
      if (retryTimer) {
        clearInterval(retryTimer)
        retryTimer = null
        autoRetryActive.value = false
      }
    } else if (resetBefore) {
      streamlitReady.value = false
    }
  } catch {
    if (resetBefore) streamlitReady.value = false
  }
  checking.value = false
}

function startAutoRetry() {
  if (retryTimer) return
  autoRetryActive.value = true
  retryTimer = setInterval(() => {
    if (streamlitReady.value) return
    checkStreamlit(false)
  }, 5000)
}

onMounted(() => {
  const d = new Date()
  d.setMonth(d.getMonth() - 1)
  selectedDate.value = d.toISOString().slice(0, 10)
  streamlitEmbedUrl.value = getEmbedUrl()
  loadBots()
  checkStreamlit().then(async () => {
    if (!streamlitReady.value) {
      await startStreamlit()
      startAutoRetry()
    }
  })
  queueStateChange()
})

watch(() => props.sharedState, (newState) => {
  if (newState) applySharedState(newState)
}, { deep: true })

onUnmounted(() => {
  if (retryTimer) {
    clearInterval(retryTimer)
    retryTimer = null
  }
})
</script>

<style scoped>
.backtesting-panel {
  height: 100%;
  display: flex;
  flex-direction: row;
  background: var(--surface-0, #0b0e14);
}

/* ── Sidebar (Glass) ── */
.bt-sidebar {
  width: 280px;
  min-width: 280px;
  background: var(--glass-bg-strong, rgba(15, 23, 42, 0.8));
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  border-right: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: relative;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              min-width 0.3s cubic-bezier(0.4, 0, 0.2, 1),
              padding 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-y: auto;
}

.bt-sidebar.collapsed {
  width: 44px;
  min-width: 44px;
  padding: 24px 8px;
}

.sidebar-toggle {
  position: absolute;
  top: 14px;
  right: 14px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  font-size: 16px;
  color: var(--text-secondary, #94a3b8);
  cursor: pointer;
  z-index: 2;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm, 8px);
  transition: all var(--transition-normal, 0.3s ease);
}

.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary, #e2e8f0);
  border-color: var(--glass-border-hover, rgba(255, 255, 255, 0.2));
}

.bt-sidebar.collapsed .sidebar-toggle {
  position: static;
  margin: 0 auto;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
}

.sidebar-icon {
  font-size: 20px;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #e2e8f0);
  letter-spacing: -0.02em;
}

.sidebar-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.sidebar-select,
.sidebar-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm, 8px);
  font-size: 13px;
  font-family: 'Inter', sans-serif;
  color: var(--text-primary, #e2e8f0);
  background: rgba(255, 255, 255, 0.05);
  outline: none;
  transition: all var(--transition-normal, 0.3s ease);
}

.sidebar-select:focus,
.sidebar-input:focus {
  border-color: var(--accent-gain, #34d399);
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.1);
}

.sidebar-select option {
  background: #1e293b;
  color: var(--text-primary, #e2e8f0);
}

.sidebar-apply-btn {
  width: 100%;
  padding: 12px 16px;
  background: linear-gradient(135deg, var(--accent-gain, #34d399) 0%, #10b981 100%);
  color: #0f172a;
  border: none;
  border-radius: var(--radius-sm, 8px);
  font-size: 13px;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  transition: all var(--transition-normal, 0.3s ease);
  margin-top: 8px;
  letter-spacing: -0.01em;
}

.sidebar-apply-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(52, 211, 153, 0.25);
}

.sidebar-apply-btn:active:not(:disabled) {
  transform: translateY(0);
}

.sidebar-apply-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.sidebar-divider {
  height: 1px;
  background: var(--glass-border, rgba(255, 255, 255, 0.1));
  margin: 4px 0;
}

.sidebar-number-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sidebar-num-input {
  flex: 1;
  text-align: center;
  -moz-appearance: textfield;
}

.sidebar-num-input::-webkit-inner-spin-button,
.sidebar-num-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.sidebar-num-btn {
  width: 34px;
  height: 34px;
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm, 8px);
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary, #94a3b8);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast, 0.15s ease);
  flex-shrink: 0;
}

.sidebar-num-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary, #e2e8f0);
  border-color: var(--glass-border-hover, rgba(255, 255, 255, 0.2));
}

.sidebar-num-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.sidebar-slider {
  width: 100%;
  accent-color: var(--accent-gain, #34d399);
  cursor: pointer;
}

.sidebar-slider-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--accent-gain, #34d399);
  text-align: center;
  font-family: 'Inter', sans-serif;
}

.sidebar-strategy-hint {
  margin-top: auto;
  font-size: 11px;
  line-height: 1.6;
  color: var(--text-muted, #64748b);
  padding-top: 16px;
  border-top: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
}

/* ── Main content ── */
.backtesting-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.embed-container {
  flex: 1;
  min-height: 500px;
  background: var(--surface-0, #0b0e14);
  overflow: hidden;
}

.backtesting-iframe {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border: none;
}

/* Fallback — Glass Card */
.embed-container.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
}

.fallback-content {
  text-align: center;
  padding: 48px;
  max-width: 460px;
  background: var(--glass-bg, rgba(30, 41, 59, 0.5));
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-lg, 24px);
  box-shadow: var(--shadow-glass, 0 25px 50px -12px rgba(0, 0, 0, 0.5));
}

.fallback-icon {
  font-size: 48px;
  margin-bottom: 20px;
  opacity: 0.7;
}

.fallback-content h3 {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #e2e8f0);
  letter-spacing: -0.02em;
}

.fallback-content p {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--text-secondary, #94a3b8);
  line-height: 1.6;
}

.fallback-content code {
  display: block;
  background: rgba(255, 255, 255, 0.05);
  padding: 14px 18px;
  border-radius: var(--radius-sm, 8px);
  font-size: 13px;
  color: var(--accent-gain, #34d399);
  margin: 16px 0;
  text-align: left;
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
}

.fallback-hint {
  font-size: 12px !important;
  color: var(--text-muted, #64748b) !important;
}

.fallback-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}

.retry-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--accent-gain, #34d399) 0%, #10b981 100%);
  color: #0f172a;
  border: none;
  border-radius: var(--radius-sm, 8px);
  font-size: 13px;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  transition: all var(--transition-normal, 0.3s ease);
}

.retry-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(52, 211, 153, 0.25);
}

.retry-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.show-anyway-btn {
  padding: 10px 20px;
  background: transparent;
  color: var(--accent-gain, #34d399);
  border: 1px solid rgba(52, 211, 153, 0.3);
  border-radius: var(--radius-sm, 8px);
  font-size: 13px;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  transition: all var(--transition-normal, 0.3s ease);
}

.show-anyway-btn:hover {
  background: rgba(52, 211, 153, 0.1);
  border-color: rgba(52, 211, 153, 0.5);
}

.auto-retry-hint {
  margin-top: 16px;
  font-size: 12px;
  color: var(--text-muted, #64748b);
}

.auto-retry-hint:empty {
  display: none;
}
</style>
