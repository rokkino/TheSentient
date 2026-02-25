<template>
  <div class="earnings-list-container">
    <div class="earnings-header-glass">
      <div class="header-content">
        <h2>Earnings giornalieri</h2>
        <div class="earnings-controls">
          <div class="search-wrapper">
            <span class="search-icon">🔍</span>
            <input 
              v-model="searchQuery" 
              type="text" 
              placeholder="Search symbol or company..." 
              class="search-input"
            />
            <span v-if="searchQuery" class="clear-search" @click="searchQuery = ''">×</span>
          </div>
          <button
            @click="loadEarnings"
            class="refresh-btn"
            :disabled="loading"
            title="Aggiorna earnings"
          >
            <span class="refresh-icon" :class="{ spinning: loading }">↻</span>
          </button>
        </div>
      </div>
    </div>

    <div class="scroll-container" ref="scrollRef">
    <div v-if="loading && earnings.length === 0" class="loading-state">
      <div class="spinner"></div>
      <p>Loading earnings data...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
      <button @click="loadEarnings" class="retry-btn">Retry</button>
    </div>
    
    <div v-else class="earnings-content">
      <!-- Search Results -->
      <div v-if="searchQuery" class="earnings-section">
        <h3 class="section-title">
          🔍 Search Results
        </h3>
        <div v-if="filteredEarnings.length === 0" class="no-earnings">
          <p>No earnings found for "{{ searchQuery }}"</p>
        </div>
        <div v-else class="earnings-list">
          <div 
            v-for="earning in filteredEarnings" 
            :key="`search-${earning.symbol}-${earning.date}`"
            class="earning-item"
          >
            <div class="earning-header">
              <div class="earning-symbol">{{ earning.symbol || earning.ticker || 'N/A' }}</div>
              <div class="earning-company">{{ earning.company || earning.companymearningsshortname || earning.companyshortname || earning.symbol || 'N/A' }}</div>
              <div class="earning-date">{{ formatDate(earning.date) }}</div>
              <div class="earning-time" :class="getTimeClass(earning.time)">
                {{ formatTime(earning.time) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Vista giornaliera: una sezione per giorno. Scroll in fondo = carica altro. -->
      <template v-else>
        <div class="earnings-section week-intro">
          <p class="week-summary">
            Earnings per giorno. Scorri in fondo per caricare più date (oltre ~3 settimane).
          </p>
        </div>
        <div
          v-for="day in earningsByDay"
          :key="day.dateStr"
          class="earnings-section"
        >
          <h3 class="section-title">
            📅 {{ day.label }}
          </h3>
          <div class="earnings-list">
            <div 
              v-for="earning in day.earnings" 
              :key="`${day.dateStr}-${earning.symbol}-${earning.date}`"
              class="earning-item"
            >
              <div class="earning-header">
                <div class="earning-symbol">{{ earning.symbol || earning.ticker || 'N/A' }}</div>
                <div class="earning-company">{{ earning.company || earning.companymearningsshortname || earning.companyshortname || earning.symbol || 'N/A' }}</div>
                <div class="earning-time" :class="getTimeClass(earning.time)">
                  {{ formatTime(earning.time) }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- Sentinel: quando entra in vista, carica altro -->
        <div
          v-if="!searchQuery && hasMore && earningsByDay.length > 0"
          ref="loadMoreRef"
          class="load-more-sentinel"
        >
          <p v-if="loadingMore">Caricamento...</p>
          <p v-else>Scorri per caricare altre date</p>
        </div>
      </template>
      
      <div class="summary">
        <p v-if="searchQuery">
          Trovati {{ filteredEarnings.length }} earnings per "{{ searchQuery }}"
        </p>
        <p v-else>
          <strong>{{ earningsByDay.length }}</strong> giorni · <strong>{{ earnings.length }}</strong> earnings. {{ hasMore ? 'Scorri in fondo per caricare altro.' : 'Tutti i dati caricati.' }}
        </p>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import api from '../services/api'

const loading = ref(false)
const error = ref(null)
const earnings = ref([])
const searchQuery = ref('')
const scrollRef = ref(null)
const loadMoreRef = ref(null)
const loadingMore = ref(false)
const offsetMonths = ref(0)
const hasMore = ref(true)
const MONTHS_CHUNK = 1
const MAX_MONTHS = 12

// Data locale YYYY-MM-DD (evita errori timezone)
const toLocalDateStr = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function normalizeEarnings(data) {
  return (data || []).map(earning => {
    let symbol = (earning.symbol || earning.ticker || '').toString().trim().toUpperCase()
    let company = (earning.company || earning.companymearningsshortname || earning.companyshortname || symbol).toString().trim()
    return {
      ...earning,
      symbol: symbol || 'N/A',
      company: company || symbol,
      ticker: symbol,
      date: earning.date || '',
      time: earning.time || 'TBD'
    }
  })
}

function parseResponse(response) {
  if (!response?.data) return []
  if (Array.isArray(response.data)) return response.data
  if (response.data.earnings && Array.isArray(response.data.earnings)) return response.data.earnings
  if (response.data.data && Array.isArray(response.data.data)) return response.data.data
  return []
}

const filteredEarnings = computed(() => {
  if (!searchQuery.value) return []
  const query = searchQuery.value.toLowerCase().trim()
  return earnings.value.filter(e => {
    const symbol = (e.symbol || e.ticker || '').toLowerCase()
    const company = (e.company || e.companymearningsshortname || e.companyshortname || '').toLowerCase()
    return symbol.includes(query) || company.includes(query)
  }).slice(0, 50)
})

// Raggruppa per giorno (giornalmente). Ordine cronologico.
const earningsByDay = computed(() => {
  if (!earnings.value || earnings.value.length === 0) return []
  const byDay = {}
  for (const e of earnings.value) {
    if (!e.date) continue
    try {
      const dateStr = typeof e.date === 'string' ? e.date.split('T')[0] : toLocalDateStr(new Date(e.date))
      if (!byDay[dateStr]) byDay[dateStr] = []
      byDay[dateStr].push(e)
    } catch (_) {}
  }
  const keys = Object.keys(byDay).sort()
  return keys.map(dateStr => {
    const list = byDay[dateStr]
    const d = new Date(dateStr + 'T12:00:00')
    const label = d.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' })
    return { dateStr, label, earnings: list }
  })
})

const loadEarnings = async () => {
  loading.value = true
  error.value = null
  offsetMonths.value = 0
  hasMore.value = true
  try {
    const response = await api.getEarnings(null, MONTHS_CHUNK, 0)
    const raw = parseResponse(response)
    const data = normalizeEarnings(raw)
    earnings.value = data
    offsetMonths.value = 1
    if (raw.length === 0 || offsetMonths.value >= MAX_MONTHS) hasMore.value = false
    await nextTick()
    scrollRef.value?.scrollTo(0, 0)
  } catch (err) {
    console.error('Error loading earnings:', err)
    error.value = err.response?.data?.detail || err.message || 'Impossibile caricare i dati degli earnings. Riprova più tardi.'
    earnings.value = []
  } finally {
    loading.value = false
  }
}

const loadMoreEarnings = async () => {
  if (loadingMore.value || !hasMore.value || offsetMonths.value >= MAX_MONTHS) return
  loadingMore.value = true
  try {
    const response = await api.getEarnings(null, MONTHS_CHUNK, offsetMonths.value)
    const raw = parseResponse(response)
    if (raw.length === 0) {
      hasMore.value = false
      return
    }
    const data = normalizeEarnings(raw)
    const existing = new Set(earnings.value.map(e => `${e.symbol}-${e.date}`))
    const newOnes = data.filter(e => !existing.has(`${e.symbol}-${e.date}`))
    earnings.value = [...earnings.value, ...newOnes]
    offsetMonths.value += 1
    if (offsetMonths.value >= MAX_MONTHS) hasMore.value = false
  } catch (err) {
    console.error('Error loading more earnings:', err)
  } finally {
    loadingMore.value = false
  }
}

let observer = null
function setupLoadMoreObserver() {
  if (!loadMoreRef.value || !scrollRef.value) return
  observer?.disconnect()
  observer = new IntersectionObserver(
    (entries) => {
      if (!entries[0]?.isIntersecting) return
      loadMoreEarnings()
    },
    { root: scrollRef.value, rootMargin: '200px', threshold: 0 }
  )
  observer.observe(loadMoreRef.value)
}

onMounted(() => {
  loadEarnings()
})
watch(loadMoreRef, (el) => {
  if (el && scrollRef.value) nextTick(setupLoadMoreObserver)
}, { flush: 'post' })
onUnmounted(() => {
  observer?.disconnect()
})

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  } catch (err) {
    return dateString
  }
}

const formatTime = (time) => {
  if (!time || time === 'TBD') return 'TBD'
  
  const timeLower = time.toLowerCase()
  if (timeLower.includes('before') || timeLower.includes('pre') || timeLower.includes('bmo')) {
    return 'Pre-Market'
  } else if (timeLower.includes('after') || timeLower.includes('post') || timeLower.includes('amc')) {
    return 'Post-Market'
  } else if (timeLower.includes('during') || timeLower.includes('market')) {
    return 'During Market'
  }
  
  return time
}

const getTimeClass = (time) => {
  if (!time || time === 'TBD') return 'time-tbd'
  
  const timeLower = time.toLowerCase()
  if (timeLower.includes('before') || timeLower.includes('pre') || timeLower.includes('bmo')) {
    return 'time-premarket'
  } else if (timeLower.includes('after') || timeLower.includes('post') || timeLower.includes('amc')) {
    return 'time-postmarket'
  }
  
  return 'time-tbd'
}

onMounted(() => {
  loadEarnings()
})
</script>

<style scoped>
.earnings-list-container {
  width: 100%;
  height: 100%;
  min-height: 0; /* per catena flex (Dashboard) e scroll corretto */
  display: flex;
  flex-direction: column;
  background-color: #050505;
  color: #fff;
}

.earnings-header-glass {
  padding: 20px 30px;
  background: rgba(20, 20, 20, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  z-index: 10;
  flex-shrink: 0;
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.header-content h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 300;
  letter-spacing: 2px;
  background: linear-gradient(90deg, #fff, #888);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.earnings-controls {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.week-intro .week-summary {
  margin: 0;
  color: #a0aec0;
  font-size: 14px;
}

.load-more-sentinel {
  padding: 24px;
  text-align: center;
  color: #888;
  font-size: 13px;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  font-size: 14px;
  opacity: 0.5;
}

.search-input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 30px;
  padding: 10px 35px 10px 35px;
  color: #fff;
  font-size: 14px;
  width: 250px;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  width: 300px;
}

.clear-search {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #666;
  font-size: 18px;
  font-weight: bold;
}

.clear-search:hover {
  color: #fff;
}

.refresh-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(66, 153, 225, 0.1);
  border: 1px solid rgba(66, 153, 225, 0.2);
  color: #4299e1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(66, 153, 225, 0.2);
  transform: rotate(180deg);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.scroll-container {
  flex: 1;
  min-height: 0; /* necessario in flex per far funzionare overflow-y */
  overflow-y: auto;
  padding: 30px;
  scroll-behavior: smooth;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 20px;
  color: #888;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #333;
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: #f44336;
  text-align: center;
  padding: 20px;
}

.retry-btn {
  padding: 10px 20px;
  background-color: #4299e1;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.retry-btn:hover {
  background-color: #3182ce;
}

.earnings-content {
  max-width: 1200px;
  margin: 0 auto;
  min-height: min-content; /* il contenuto (Oggi, Domani, ecc.) occupa spazio e scrolla */
}

.earnings-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #fff;
  padding-bottom: 10px;
  border-bottom: 1px solid #333;
}

.no-earnings {
  padding: 20px;
  text-align: center;
  color: #888;
  background-color: #111;
  border-radius: 4px;
}

.earnings-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.earning-item {
  background-color: #111;
  border: 1px solid #333;
  border-radius: 4px;
  padding: 15px;
  transition: all 0.2s;
}

.earning-item:hover {
  background-color: #1a1a1a;
  border-color: #555;
}

.earning-header {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.earning-symbol {
  font-weight: 700;
  font-size: 16px;
  color: #4299e1;
  min-width: 80px;
}

.earning-company {
  flex: 1;
  color: #ccc;
  font-size: 14px;
}

.earning-date {
  color: #888;
  font-size: 12px;
  min-width: 200px;
}

.earning-time {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  white-space: nowrap;
}

.time-premarket {
  background-color: #4299e1;
  color: #fff;
}

.time-postmarket {
  background-color: #ed8936;
  color: #fff;
}

.time-tbd {
  background-color: #666;
  color: #fff;
}

.summary {
  margin-top: 30px;
  padding: 20px;
  background-color: #111;
  border-radius: 4px;
  text-align: center;
  color: #a0aec0;
}

/* Scrollbar Styling */
.scroll-container::-webkit-scrollbar {
  width: 8px;
}

.scroll-container::-webkit-scrollbar-track {
  background: #050505;
}

.scroll-container::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 4px;
}

.scroll-container::-webkit-scrollbar-thumb:hover {
  background: #555;
}

@media (max-width: 800px) {
  .earnings-header-glass {
    padding: 16px 18px;
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
  }

  .earnings-controls {
    width: 100%;
    gap: 10px;
  }

  .search-wrapper {
    flex: 1 1 100%;
  }

  .refresh-btn {
    width: 44px;
    height: 44px;
    border-radius: 12px;
  }

  .search-input {
    width: 100%;
  }

  .search-input:focus {
    width: 100%;
  }

  .scroll-container {
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .earnings-list-container {
    padding: 12px;
    padding-bottom: max(12px, env(safe-area-inset-bottom));
  }

  .earnings-header-glass {
    padding: 14px 16px;
  }

  .header-content {
    gap: 12px;
  }

  .header-content h2 {
    font-size: 20px;
    letter-spacing: 1px;
  }

  .search-input {
    min-height: 44px;
    font-size: 16px;
  }

  .scroll-container {
    padding: 16px;
  }

  .section-title {
    font-size: 16px;
  }

  .earning-item {
    padding: 12px;
    border-radius: 12px;
  }

  .earning-header {
    gap: 12px;
  }
}
</style>
