<template>
  <div class="backtesting-panel">
    <div class="backtesting-header">
      <h2>Backtesting</h2>
      <p class="subtitle">Simulazione storica su dati earnings. Scegli il bot e la data (S&P 500 / Nasdaq).</p>
      <div class="backtesting-filters" v-if="streamlitReady">
        <label class="filter-label">
          <span>Bot</span>
          <select v-model="selectedBotId" class="filter-select" @change="updateEmbedUrl" :disabled="readOnly">
            <option :value="null">Placeholder (logica built-in)</option>
            <option v-for="b in bots" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </label>
        <label class="filter-label">
          <span>Data backtest</span>
          <input
            v-model="selectedDate"
            type="date"
            class="filter-input"
            @change="updateEmbedUrl"
            :disabled="readOnly"
          />
        </label>
        <button type="button" class="apply-btn" @click="reloadIframe" :disabled="readOnly">Applica e ricarica dashboard</button>
      </div>
    </div>

    <div class="backtesting-content">
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
    bots.value = res?.bots ?? []
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
  flex-direction: column;
  background: #0a0a0a;
}

.backtesting-header {
  padding: 20px 24px;
  border-bottom: 1px solid #222;
  background: #0f0f0f;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.backtesting-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #888;
  flex: 1;
}

.backtesting-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  width: 100%;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #222;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #aaa;
}

.filter-label span {
  white-space: nowrap;
}

.filter-select,
.filter-input {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #fff;
  padding: 8px 12px;
  font-size: 13px;
  min-width: 180px;
}

.filter-input {
  min-width: 140px;
}

.apply-btn {
  padding: 8px 16px;
  background: #2a4;
  color: #111;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.apply-btn:hover {
  opacity: 0.9;
}

.backtesting-content {
  flex: 1;
  min-height: 0;
  padding: 16px;
}

.embed-container {
  height: 100%;
  min-height: 500px;
  background: #111;
  border: 1px solid #222;
  border-radius: 4px;
  overflow: hidden;
}

.backtesting-iframe {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border: none;
}

/* Fallback quando Streamlit non è attivo */
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
