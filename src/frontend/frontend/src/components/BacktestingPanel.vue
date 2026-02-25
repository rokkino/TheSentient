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
          <select v-model="selectedBotId" class="sidebar-select" @change="updateEmbedUrl" :disabled="readOnly">
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
            @change="updateEmbedUrl"
            :disabled="readOnly"
          />
        </div>

        <button type="button" class="sidebar-apply-btn" @click="reloadIframe" :disabled="readOnly">
          ▶ Applica e ricarica
        </button>

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
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
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
  const qs = params.toString()
  return qs ? `${base}/?${qs}` : `${base}/?embed=true`
}

function updateEmbedUrl() {
  streamlitEmbedUrl.value = getEmbedUrl()
  queueStateChange()
}

function reloadIframe() {
  updateEmbedUrl()
  streamlitEmbedUrl.value = ''
  setTimeout(() => { streamlitEmbedUrl.value = getEmbedUrl() }, 0)
}

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
  background: #0a0a0a;
}

/* ── Sidebar ── */
.bt-sidebar {
  width: 260px;
  min-width: 260px;
  background: #f5f5f9;
  border-right: 1px solid #ddd;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  position: relative;
  transition: width 0.25s ease, min-width 0.25s ease, padding 0.25s ease;
  overflow: hidden;
}

.bt-sidebar.collapsed {
  width: 40px;
  min-width: 40px;
  padding: 20px 6px;
}

.sidebar-toggle {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  font-size: 18px;
  color: #666;
  cursor: pointer;
  z-index: 2;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.15s;
}

.sidebar-toggle:hover {
  background: #e0e0e6;
}

.bt-sidebar.collapsed .sidebar-toggle {
  position: static;
  margin: 0 auto;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ddd;
}

.sidebar-icon {
  font-size: 20px;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.sidebar-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sidebar-label {
  font-size: 13px;
  font-weight: 500;
  color: #555;
}

.sidebar-select,
.sidebar-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 13px;
  color: #333;
  background: #fff;
  outline: none;
  transition: border-color 0.2s;
}

.sidebar-select:focus,
.sidebar-input:focus {
  border-color: #e74c4c;
}

.sidebar-apply-btn {
  width: 100%;
  padding: 10px 14px;
  background: #e74c4c;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 4px;
}

.sidebar-apply-btn:hover:not(:disabled) {
  background: #d43c3c;
}

.sidebar-apply-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sidebar-strategy-hint {
  margin-top: auto;
  font-size: 12px;
  line-height: 1.5;
  color: #888;
  padding-top: 16px;
  border-top: 1px solid #ddd;
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
  background: #111;
  overflow: hidden;
}

.backtesting-iframe {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border: none;
}

/* Fallback */
.embed-container.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
}

.fallback-content {
  text-align: center;
  padding: 40px;
  max-width: 420px;
}

.fallback-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.7;
}

.fallback-content h3 {
  margin: 0 0 12px;
  font-size: 18px;
  color: #ccc;
}

.fallback-content p {
  margin: 0 0 12px;
  font-size: 14px;
  color: #888;
}

.fallback-content code {
  display: block;
  background: #1a1a1a;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 13px;
  color: #9c9;
  margin: 12px 0;
  text-align: left;
  border: 1px solid #333;
}

.fallback-hint {
  font-size: 12px !important;
  color: #666 !important;
}

.fallback-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}

.retry-btn {
  padding: 10px 24px;
  background: #2a4;
  color: #111;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.retry-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.retry-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.show-anyway-btn {
  padding: 10px 20px;
  background: transparent;
  color: #9c9;
  border: 1px solid #3a5;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.show-anyway-btn:hover {
  background: #1a3a1a;
  color: #bfb;
}

.auto-retry-hint {
  margin-top: 16px;
  font-size: 12px;
  color: #666;
}

.auto-retry-hint:empty {
  display: none;
}
</style>
