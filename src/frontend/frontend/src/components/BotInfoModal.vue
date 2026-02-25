<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ bot?.name }} - Earnings Info</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>
      
      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <p>Loading earnings data...</p>
        </div>
        
        <div v-else-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-else>
          <!-- Tabs -->
          <div class="tabs">
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'earnings' }"
              @click="activeTab = 'earnings'"
            >
              Earnings Calendar
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'financials' }"
              @click="activeTab = 'financials'"
            >
              Financials & Charts
            </button>
          </div>

          <!-- Financials Tab -->
          <div v-if="activeTab === 'financials'" class="financials-tab">
            <div v-if="loadingFinancials" class="loading-state">
              <div class="spinner"></div>
              <p>Loading financial charts...</p>
            </div>
            <div v-else-if="!financialsData" class="no-data">
              <p>No financial data available for {{ bot?.name }}</p>
            </div>
            <div v-else class="charts-grid">
              <div class="chart-card">
                <h3>Revenue vs Earnings (Quarterly)</h3>
                <RevenueEarningsChart :financials="financialsData.quarterly_financials" />
              </div>
              <div class="chart-card">
                <h3>EPS History (Estimates vs Actual)</h3>
                <EpsHistoryChart :history="financialsData.earnings_history" />
              </div>
            </div>
          </div>

          <!-- Earnings Calendar Tab -->
          <div v-else class="earnings-calendar-tab">
          <!-- Debug info -->
          <div v-if="earnings.length > 0" class="debug-info" style="margin-bottom: 16px; padding: 12px; background: #1a202c; border-radius: 8px; font-size: 12px; color: #a0aec0;">
            <p>Total earnings loaded: {{ earnings.length }}</p>
            <p>Today: {{ today }}, Tomorrow: {{ tomorrow }}</p>
            <p>Sample dates: {{ earnings.slice(0, 3).map(e => e.date).join(', ') }}</p>
          </div>
          
          <!-- Today's Earnings -->
          <div class="earnings-section">
            <h3 class="section-title">
              📅 Today's Earnings ({{ formatDate(today) }})
            </h3>
            <div v-if="todayEarnings.length === 0" class="no-earnings">
              <p>No earnings scheduled for today</p>
              <p style="font-size: 12px; margin-top: 8px; color: #718096;">
                Total earnings in response: {{ earnings.length }}
              </p>
              <p v-if="earnings.length > 0" style="font-size: 11px; margin-top: 4px; color: #718096;">
                (Check console for date format details)
              </p>
            </div>
            <div v-else class="earnings-list">
              <div 
                v-for="earning in todayEarnings" 
                :key="`today-${earning.symbol}-${earning.date}`"
                class="earning-item"
              >
                <div class="earning-header" @click="toggleEpsHistory(earning.symbol)">
                  <div class="earning-symbol">{{ earning.symbol || earning.ticker || 'N/A' }}</div>
                  <div class="earning-company">{{ earning.company || earning.companymearningsshortname || earning.companyshortname || earning.symbol || 'N/A' }}</div>
                  <div class="earning-time" :class="getTimeClass(earning.time)">
                    {{ formatTime(earning.time) }}
                  </div>
                  <div v-if="reliabilityScores[earning.symbol]" class="reliability-badge" :class="getReliabilityClass(reliabilityScores[earning.symbol].beat_rate)">
                    {{ reliabilityScores[earning.symbol].beat_rate }}% Beat
                  </div>
                  <button class="expand-btn" :class="{ expanded: expandedEarnings[earning.symbol] }" @click.stop>
                    {{ expandedEarnings[earning.symbol] ? '▼' : '▶' }}
                  </button>
                </div>
                <div v-if="expandedEarnings[earning.symbol]" class="eps-history-section">
                  <div v-if="loadingEps[earning.symbol]" class="loading-eps">
                    Loading EPS history...
                  </div>
                  <div v-else-if="epsHistory[earning.symbol] && epsHistory[earning.symbol].length > 0" class="eps-history-section-content">
                    <div v-if="reliabilityScores[earning.symbol]" class="reliability-summary">
                      <div class="reliability-stats">
                        <div class="stat-item">
                          <span class="stat-label">Beat Rate:</span>
                          <span class="stat-value" :class="getReliabilityClass(reliabilityScores[earning.symbol].beat_rate)">
                            {{ reliabilityScores[earning.symbol].beat_rate }}%
                          </span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Beat:</span>
                          <span class="stat-value beat">{{ reliabilityScores[earning.symbol].beat_count }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Miss:</span>
                          <span class="stat-value miss">{{ reliabilityScores[earning.symbol].miss_count }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Total Quarters:</span>
                          <span class="stat-value">{{ reliabilityScores[earning.symbol].quarters_with_data }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="eps-history-table">
                      <table>
                        <thead>
                          <tr>
                            <th>Quarter</th>
                            <th>Date</th>
                            <th>EPS Estimate</th>
                            <th>EPS Actual</th>
                            <th>Result</th>
                            <th>Surprise %</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="eps in epsHistory[earning.symbol]" :key="eps.date" :class="eps.result">
                            <td>{{ eps.quarter }}</td>
                            <td>{{ formatDate(eps.date) }}</td>
                            <td>{{ formatEps(eps.eps_estimate) }}</td>
                            <td :class="getEpsClass(eps.eps_actual, eps.eps_estimate)">
                              {{ formatEps(eps.eps_actual) }}
                            </td>
                            <td :class="eps.result">
                              <span v-if="eps.result === 'beat'" class="result-badge beat">✓ Beat</span>
                              <span v-else-if="eps.result === 'miss'" class="result-badge miss">✗ Miss</span>
                              <span v-else-if="eps.result === 'meet'" class="result-badge meet">= Meet</span>
                              <span v-else>-</span>
                            </td>
                            <td :class="getSurpriseClass(eps.surprise_percent)">
                              {{ formatSurprise(eps.surprise_percent) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div v-else class="no-eps-history">
                    No EPS history available
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Tomorrow's Earnings -->
          <div class="earnings-section">
            <h3 class="section-title">
              📅 Tomorrow's Earnings ({{ formatDate(tomorrow) }})
            </h3>
            <div v-if="tomorrowEarnings.length === 0" class="no-earnings">
              <p>No earnings scheduled for tomorrow</p>
              <p v-if="earnings.length > 0" style="font-size: 12px; margin-top: 8px; color: #718096;">
                Total earnings in response: {{ earnings.length }}
              </p>
            </div>
            <div v-else class="earnings-list">
              <div 
                v-for="earning in tomorrowEarnings" 
                :key="`tomorrow-${earning.symbol}-${earning.date}`"
                class="earning-item"
              >
                <div class="earning-header" @click="toggleEpsHistory(earning.symbol)">
                  <div class="earning-symbol">{{ earning.symbol || earning.ticker || 'N/A' }}</div>
                  <div class="earning-company">{{ earning.company || earning.companymearningsshortname || earning.companyshortname || earning.symbol || 'N/A' }}</div>
                  <div class="earning-time" :class="getTimeClass(earning.time)">
                    {{ formatTime(earning.time) }}
                  </div>
                  <div v-if="reliabilityScores[earning.symbol]" class="reliability-badge" :class="getReliabilityClass(reliabilityScores[earning.symbol].beat_rate)">
                    {{ reliabilityScores[earning.symbol].beat_rate }}% Beat
                  </div>
                  <button class="expand-btn" :class="{ expanded: expandedEarnings[earning.symbol] }" @click.stop>
                    {{ expandedEarnings[earning.symbol] ? '▼' : '▶' }}
                  </button>
                </div>
                <div v-if="expandedEarnings[earning.symbol]" class="eps-history-section">
                  <div v-if="loadingEps[earning.symbol]" class="loading-eps">
                    Loading EPS history...
                  </div>
                  <div v-else-if="epsHistory[earning.symbol] && epsHistory[earning.symbol].length > 0" class="eps-history-section-content">
                    <div v-if="reliabilityScores[earning.symbol]" class="reliability-summary">
                      <div class="reliability-stats">
                        <div class="stat-item">
                          <span class="stat-label">Beat Rate:</span>
                          <span class="stat-value" :class="getReliabilityClass(reliabilityScores[earning.symbol].beat_rate)">
                            {{ reliabilityScores[earning.symbol].beat_rate }}%
                          </span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Beat:</span>
                          <span class="stat-value beat">{{ reliabilityScores[earning.symbol].beat_count }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Miss:</span>
                          <span class="stat-value miss">{{ reliabilityScores[earning.symbol].miss_count }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Total Quarters:</span>
                          <span class="stat-value">{{ reliabilityScores[earning.symbol].quarters_with_data }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="eps-history-table">
                      <table>
                        <thead>
                          <tr>
                            <th>Quarter</th>
                            <th>Date</th>
                            <th>EPS Estimate</th>
                            <th>EPS Actual</th>
                            <th>Result</th>
                            <th>Surprise %</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="eps in epsHistory[earning.symbol]" :key="eps.date" :class="eps.result">
                            <td>{{ eps.quarter }}</td>
                            <td>{{ formatDate(eps.date) }}</td>
                            <td>{{ formatEps(eps.eps_estimate) }}</td>
                            <td :class="getEpsClass(eps.eps_actual, eps.eps_estimate)">
                              {{ formatEps(eps.eps_actual) }}
                            </td>
                            <td :class="eps.result">
                              <span v-if="eps.result === 'beat'" class="result-badge beat">✓ Beat</span>
                              <span v-else-if="eps.result === 'miss'" class="result-badge miss">✗ Miss</span>
                              <span v-else-if="eps.result === 'meet'" class="result-badge meet">= Meet</span>
                              <span v-else>-</span>
                            </td>
                            <td :class="getSurpriseClass(eps.surprise_percent)">
                              {{ formatSurprise(eps.surprise_percent) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div v-else class="no-eps-history">
                    No EPS history available
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Next Earnings (if no earnings today/tomorrow) -->
          <div v-if="todayEarnings.length === 0 && tomorrowEarnings.length === 0 && nextEarnings.length > 0" class="earnings-section">
            <h3 class="section-title">
              📅 Next Available Earnings (Next 7 Days)
            </h3>
            <div class="earnings-list">
              <div 
                v-for="earning in nextEarnings" 
                :key="`next-${earning.symbol}-${earning.date}`"
                class="earning-item"
              >
                <div class="earning-header" @click="toggleEpsHistory(earning.symbol)">
                  <div class="earning-symbol">{{ earning.symbol || earning.ticker || 'N/A' }}</div>
                  <div class="earning-company">{{ earning.company || earning.companymearningsshortname || earning.companyshortname || earning.symbol || 'N/A' }}</div>
                  <div class="earning-date">{{ formatDate(earning.date) }}</div>
                  <div class="earning-time" :class="getTimeClass(earning.time)">
                    {{ formatTime(earning.time) }}
                  </div>
                  <button class="expand-btn" :class="{ expanded: expandedEarnings[earning.symbol] }" @click.stop>
                    {{ expandedEarnings[earning.symbol] ? '▼' : '▶' }}
                  </button>
                </div>
                <div v-if="expandedEarnings[earning.symbol]" class="eps-history-section">
                  <div v-if="loadingEps[earning.symbol]" class="loading-eps">
                    Loading EPS history...
                  </div>
                  <div v-else-if="epsHistory[earning.symbol] && epsHistory[earning.symbol].length > 0" class="eps-history-section-content">
                    <div v-if="reliabilityScores[earning.symbol]" class="reliability-summary">
                      <div class="reliability-stats">
                        <div class="stat-item">
                          <span class="stat-label">Beat Rate:</span>
                          <span class="stat-value" :class="getReliabilityClass(reliabilityScores[earning.symbol].beat_rate)">
                            {{ reliabilityScores[earning.symbol].beat_rate }}%
                          </span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Beat:</span>
                          <span class="stat-value beat">{{ reliabilityScores[earning.symbol].beat_count }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Miss:</span>
                          <span class="stat-value miss">{{ reliabilityScores[earning.symbol].miss_count }}</span>
                        </div>
                        <div class="stat-item">
                          <span class="stat-label">Total Quarters:</span>
                          <span class="stat-value">{{ reliabilityScores[earning.symbol].quarters_with_data }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="eps-history-table">
                      <table>
                        <thead>
                          <tr>
                            <th>Quarter</th>
                            <th>Date</th>
                            <th>EPS Estimate</th>
                            <th>EPS Actual</th>
                            <th>Result</th>
                            <th>Surprise %</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="eps in epsHistory[earning.symbol]" :key="eps.date" :class="eps.result">
                            <td>{{ eps.quarter }}</td>
                            <td>{{ formatDate(eps.date) }}</td>
                            <td>{{ formatEps(eps.eps_estimate) }}</td>
                            <td :class="getEpsClass(eps.eps_actual, eps.eps_estimate)">
                              {{ formatEps(eps.eps_actual) }}
                            </td>
                            <td :class="eps.result">
                              <span v-if="eps.result === 'beat'" class="result-badge beat">✓ Beat</span>
                              <span v-else-if="eps.result === 'miss'" class="result-badge miss">✗ Miss</span>
                              <span v-else-if="eps.result === 'meet'" class="result-badge meet">= Meet</span>
                              <span v-else>-</span>
                            </td>
                            <td :class="getSurpriseClass(eps.surprise_percent)">
                              {{ formatSurprise(eps.surprise_percent) }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div v-else class="no-eps-history">
                    No EPS history available
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="summary">
            <p>
              <strong>Today:</strong> {{ todayEarnings.length }} earnings | 
              <strong>Tomorrow:</strong> {{ tomorrowEarnings.length }} earnings
            </p>
            <p v-if="todayEarnings.length === 0 && tomorrowEarnings.length === 0 && nextEarnings.length > 0" style="margin-top: 8px; font-size: 12px; color: #a0aec0;">
              Showing next {{ nextEarnings.length }} upcoming earnings
            </p>
            <p v-else style="margin-top: 8px; font-size: 12px; color: #a0aec0;">
              Total earnings available: {{ earnings.length }}
            </p>
          </div>
          </div> <!-- End of Earnings Calendar Tab -->
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn btn-primary" @click="close">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import api from '../services/api'
import RevenueEarningsChart from './RevenueEarningsChart.vue'
import EpsHistoryChart from './EpsHistoryChart.vue'

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

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref(null)
const earnings = ref([])
const expandedEarnings = ref({})
const epsHistory = ref({})
const loadingEps = ref({})
const activeTab = ref('earnings') // 'earnings' or 'financials'
const financialsData = ref(null)
const loadingFinancials = ref(false)

// Helper function to get YYYY-MM-DD in local time
const toLocalDateStr = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

// Helper function to get next business day (skip weekends)
const getNextBusinessDay = (date) => {
  const newDate = new Date(date) // Don't mutate original
  const day = newDate.getDay() // 0=Sunday, 6=Saturday
  if (day === 0) { // Sunday
    newDate.setDate(newDate.getDate() + 1) // Skip to Monday
  } else if (day === 6) { // Saturday
    newDate.setDate(newDate.getDate() + 2) // Skip to Monday
  }
  return newDate
}

const today = computed(() => {
  const now = new Date()
  const businessDay = getNextBusinessDay(now)
  return toLocalDateStr(businessDay)
})

const tomorrow = computed(() => {
  const todayDate = new Date()
  let tomorrowCandidate = new Date(todayDate)
  tomorrowCandidate.setDate(todayDate.getDate() + 1)
  
  // Get next business day after today
  const tomorrowBusinessDay = getNextBusinessDay(tomorrowCandidate)
  
  return toLocalDateStr(tomorrowBusinessDay)
})

const todayEarnings = computed(() => {
  if (!earnings.value || earnings.value.length === 0) return []
  
  const filtered = earnings.value.filter(e => {
    if (!e.date) return false
    try {
      // Normalize dates - handle different formats
      let earningDateStr
      if (typeof e.date === 'string') {
        // Handle ISO format, YYYY-MM-DD, or other formats
        earningDateStr = e.date.split('T')[0] // Remove time if present
      } else {
        earningDateStr = new Date(e.date).toISOString().split('T')[0]
      }
      
      const todayDateStr = today.value
      
      // Compare normalized date strings
      return earningDateStr === todayDateStr
    } catch (err) {
      console.warn('Error parsing date:', e.date, err)
      return false
    }
  })
  
  return filtered
})

const tomorrowEarnings = computed(() => {
  if (!earnings.value || earnings.value.length === 0) return []
  
  const filtered = earnings.value.filter(e => {
    if (!e.date) return false
    try {
      // Normalize dates - handle different formats
      let earningDateStr
      if (typeof e.date === 'string') {
        // Handle ISO format, YYYY-MM-DD, or other formats
        earningDateStr = e.date.split('T')[0] // Remove time if present
      } else {
        earningDateStr = new Date(e.date).toISOString().split('T')[0]
      }
      
      const tomorrowDateStr = tomorrow.value
      
      // Compare normalized date strings
      return earningDateStr === tomorrowDateStr
    } catch (err) {
      console.warn('Error parsing date:', e.date, err)
      return false
    }
  })
  
  return filtered
})

// Get next available earnings (next 7 days)
const nextEarnings = computed(() => {
  if (!earnings.value || earnings.value.length === 0) return []
  
  const todayDate = new Date(today.value)
  const nextWeek = new Date(todayDate)
  nextWeek.setDate(todayDate.getDate() + 7)
  
  const filtered = earnings.value
    .filter(e => {
      if (!e.date) return false
      try {
        const earningDate = new Date(e.date)
        return earningDate >= todayDate && earningDate <= nextWeek
      } catch (err) {
        return false
      }
    })
    .slice(0, 20) // Limit to first 20
  
  return filtered
})

watch(() => props.show, async (newVal) => {
  if (newVal) {
    await loadEarnings()
  } else {
    earnings.value = []
    error.value = null
  }
})

watch(activeTab, async (newTab) => {
  if (newTab === 'financials' && !financialsData.value && props.bot) {
    await loadFinancials()
  }
})

const loadFinancials = async () => {
  if (!props.bot) return
  
  loadingFinancials.value = true
  try {
    // Determine ticker from bot name or config
    // Assuming bot.name is the ticker for now, or we need a way to get it
    // If bot is a "stock" bot, name might be "AAPL"
    let ticker = props.bot.name
    if (props.bot.config && props.bot.config.symbol) {
        ticker = props.bot.config.symbol
    }
    
    // Clean ticker
    ticker = ticker.split(' ')[0].trim()
    
    console.log(`Loading financials for ${ticker}...`)
    const response = await api.getStockFinancials(ticker)
    financialsData.value = response.data
  } catch (err) {
    console.error('Error loading financials:', err)
  } finally {
    loadingFinancials.value = false
  }
}

const loadEarnings = async () => {
  loading.value = true
  error.value = null
  
  try {
    console.log('Loading earnings for bot info modal...')
    console.log(`Today: ${today.value}, Tomorrow: ${tomorrow.value}`)
    
    // Request earnings for today and tomorrow specifically
    // Use weeks=2 to ensure we get today/tomorrow data
    let response
    try {
      response = await api.getEarnings(null, 2, 0)
    } catch (err) {
      console.error('Error with first request:', err)
      // Check if it's a timeout error
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        console.warn('Request timed out, but continuing with available data...')
        // Try to get data from a wider range, but with shorter timeout expectation
        try {
          response = await api.getEarnings(null, 4, 0)
        } catch (retryErr) {
          console.error('Retry also failed:', retryErr)
          throw new Error('La richiesta degli earnings sta impiegando troppo tempo. Yahoo Finance potrebbe essere lento. Riprova più tardi.')
        }
      } else {
        throw err
      }
    }
    
    console.log('Earnings API response:', response)
    console.log('Response data:', response.data)
    
    // Handle different response structures
    let earningsData = []
    if (response.data) {
      if (Array.isArray(response.data)) {
        earningsData = response.data
      } else if (response.data.earnings && Array.isArray(response.data.earnings)) {
        earningsData = response.data.earnings
      } else if (response.data.data && Array.isArray(response.data.data)) {
        earningsData = response.data.data
      }
    }
    
    console.log(`Loaded ${earningsData.length} earnings from API`)
    
    // Log sample earnings to debug date formats
    if (earningsData.length > 0) {
      console.log('Sample earnings (first 5):', earningsData.slice(0, 5).map(e => ({
        symbol: e.symbol,
        date: e.date,
        company: e.company,
        time: e.time
      })))
    }
    
    // Normalize and clean earnings data
    earningsData = earningsData.map(earning => {
      // Ensure symbol is a clean string
      let symbol = earning.symbol || earning.ticker || ''
      if (typeof symbol !== 'string') {
        symbol = String(symbol)
      }
      symbol = symbol.trim().toUpperCase()
      
      // Ensure company is a clean string
      let company = earning.company || earning.companymearningsshortname || earning.companyshortname || symbol
      if (typeof company !== 'string') {
        company = String(company)
      }
      company = company.trim()
      
      // Remove any weird characters or malformed data
      if (symbol.includes('=') || symbol.length > 10 || !/^[A-Z0-9\.\-]+$/.test(symbol)) {
        console.warn('Invalid symbol detected:', symbol, 'from earning:', earning)
        symbol = 'UNKNOWN'
      }
      
      if (company.includes('=') || company.length > 100) {
        console.warn('Invalid company name detected:', company, 'from earning:', earning)
        company = symbol
      }
      
      return {
        ...earning,
        symbol: symbol,
        company: company,
        ticker: symbol, // For compatibility
        date: earning.date || '',
        time: earning.time || 'TBD'
      }
    })
    
    earnings.value = earningsData
    
    // Debug: log today and tomorrow earnings after filtering
    console.log(`Today earnings (${today.value}):`, todayEarnings.value.length)
    console.log(`Tomorrow earnings (${tomorrow.value}):`, tomorrowEarnings.value.length)
    
    if (todayEarnings.value.length > 0) {
      console.log('Today earnings details:', todayEarnings.value.map(e => `${e.symbol} - ${e.date}`))
    }
    if (tomorrowEarnings.value.length > 0) {
      console.log('Tomorrow earnings details:', tomorrowEarnings.value.map(e => `${e.symbol} - ${e.date}`))
    }
    
    // If no earnings found, log all dates to debug
    if (todayEarnings.value.length === 0 && tomorrowEarnings.value.length === 0 && earningsData.length > 0) {
      const uniqueDates = [...new Set(earningsData.map(e => e.date).filter(Boolean))].sort()
      console.warn('No earnings for today/tomorrow, but found dates:', uniqueDates.slice(0, 10))
    }
  } catch (err) {
    console.error('Error loading earnings:', err)
    console.error('Error details:', err.response)
    
    // Show user-friendly error messages in Italian
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      error.value = 'La richiesta sta impiegando troppo tempo. Yahoo Finance potrebbe essere lento. Riprova più tardi o controlla la console per i dettagli.'
    } else {
      error.value = err.response?.data?.detail || err.message || 'Impossibile caricare i dati degli earnings. Riprova più tardi.'
    }
    earnings.value = []
  } finally {
    loading.value = false
    console.log('Loading complete. Earnings count:', earnings.value.length)
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
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

const reliabilityScores = ref({})

const toggleEpsHistory = async (symbol) => {
  const isExpanded = expandedEarnings.value[symbol]
  
  if (isExpanded) {
    // Collapse
    expandedEarnings.value[symbol] = false
  } else {
    // Expand and load EPS history if not already loaded
    expandedEarnings.value[symbol] = true
    
    if (!epsHistory.value[symbol]) {
      loadingEps.value[symbol] = true
      try {
        const response = await api.getTickerEpsHistory(symbol, 2)
        epsHistory.value[symbol] = response.data.eps_history || []
        reliabilityScores.value[symbol] = response.data.reliability || {}
        console.log(`Loaded ${epsHistory.value[symbol].length} quarters of EPS history for ${symbol}`)
        console.log(`Reliability: ${reliabilityScores.value[symbol].beat_rate}% beat rate`)
      } catch (err) {
        console.error(`Error loading EPS history for ${symbol}:`, err)
        epsHistory.value[symbol] = []
        reliabilityScores.value[symbol] = {}
      } finally {
        loadingEps.value[symbol] = false
      }
    }
  }
}

const getReliabilityClass = (beatRate) => {
  if (beatRate >= 75) return 'reliability-excellent'
  if (beatRate >= 50) return 'reliability-good'
  if (beatRate >= 25) return 'reliability-fair'
  return 'reliability-poor'
}

const formatEps = (eps) => {
  if (eps === null || eps === undefined || eps === 'N/A') return 'N/A'
  return `$${parseFloat(eps).toFixed(2)}`
}

const formatSurprise = (surprise) => {
  if (surprise === null || surprise === undefined) return 'N/A'
  const val = parseFloat(surprise)
  return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`
}

const getEpsClass = (actual, estimate) => {
  if (actual === null || estimate === null) return ''
  if (parseFloat(actual) >= parseFloat(estimate)) return 'eps-beat'
  return 'eps-miss'
}

const getSurpriseClass = (surprise) => {
  if (surprise === null || surprise === undefined) return ''
  const val = parseFloat(surprise)
  if (val > 0) return 'surprise-positive'
  if (val < 0) return 'surprise-negative'
  return ''
}

const close = () => {
  // Reset state when closing
  expandedEarnings.value = {}
  epsHistory.value = {}
  loadingEps.value = {}
  reliabilityScores.value = {}
  emit('close')
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
  max-width: 800px;
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
  position: sticky;
  top: 0;
  background: #2d3748;
  z-index: 10;
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

.loading-state {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
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

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid #4a5568;
  padding-bottom: 10px;
}

.tab-btn {
  background: none;
  border: none;
  color: #a0aec0;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  border-radius: 6px;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #e2e8f0;
  background: #4a5568;
}

.tab-btn.active {
  color: #4299e1;
  background: rgba(66, 153, 225, 0.1);
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

@media (min-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.chart-card {
  background: #1a202c;
  border-radius: 8px;
  padding: 16px;
}

.chart-card h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #e2e8f0;
}

.earnings-section {
  margin-bottom: 32px;
}

.section-title {
  color: #e2e8f0;
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 2px solid #4a5568;
}

.no-earnings {
  text-align: center;
  padding: 20px;
  color: #a0aec0;
  font-style: italic;
}

.earnings-list {
  display: grid;
  gap: 12px;
}

.earning-item {
  margin-bottom: 8px;
}

.earning-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  flex-wrap: wrap;
}

.earning-header:hover {
  background: #374151;
}

.earning-date {
  color: #a0aec0;
  font-size: 12px;
  white-space: nowrap;
}

.earning-item:hover {
  border-color: #718096;
  transform: translateX(4px);
}

.earning-symbol {
  font-size: 18px;
  font-weight: 700;
  color: #4299e1;
}

.earning-company {
  color: #cbd5e0;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.earning-time {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  min-width: 100px;
}

.time-premarket {
  background: #2d5016;
  color: #68d391;
}

.time-postmarket {
  background: #2d3748;
  color: #90cdf4;
}

.time-tbd {
  background: #4a3a2a;
  color: #f6ad55;
}

.summary {
  margin-top: 24px;
  padding: 16px;
  background: #1a202c;
  border-radius: 8px;
  border-left: 3px solid #4299e1;
}

.summary p {
  margin: 0;
  color: #cbd5e0;
  font-size: 14px;
}

.summary strong {
  color: #e2e8f0;
}

.expand-btn {
  background: none;
  border: none;
  color: #cbd5e0;
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  transition: transform 0.2s;
  margin-left: auto;
}

.expand-btn:hover {
  color: #e2e8f0;
}

.expand-btn.expanded {
  transform: rotate(0deg);
}

.eps-history-section {
  padding: 16px;
  background: #1a202c;
  border-top: 1px solid #4a5568;
}

.loading-eps {
  text-align: center;
  color: #a0aec0;
  padding: 20px;
  font-size: 14px;
}

.no-eps-history {
  text-align: center;
  color: #718096;
  padding: 20px;
  font-size: 14px;
}

.eps-history-table {
  overflow-x: auto;
}

.eps-history-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.eps-history-table th {
  background: #2d3748;
  color: #e2e8f0;
  padding: 10px 8px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #4a5568;
  position: sticky;
  top: 0;
}

.eps-history-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #4a5568;
  color: #cbd5e0;
}

.eps-history-table tr:hover {
  background: #2d3748;
}

.eps-beat {
  color: #68d391;
  font-weight: 600;
}

.eps-miss {
  color: #fc8181;
  font-weight: 600;
}

.surprise-positive {
  color: #68d391;
  font-weight: 600;
}

.surprise-negative {
  color: #fc8181;
  font-weight: 600;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
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

.btn-primary {
  background: #4299e1;
  color: white;
}

.btn-primary:hover {
  background: #3182ce;
}

.expand-btn {
  background: none;
  border: none;
  color: #cbd5e0;
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  transition: transform 0.2s;
  margin-left: auto;
}

.expand-btn:hover {
  color: #e2e8f0;
}

.expand-btn.expanded {
  transform: rotate(0deg);
}

.eps-history-section {
  padding: 16px;
  background: #1a202c;
  border-top: 1px solid #4a5568;
}

.loading-eps {
  text-align: center;
  color: #a0aec0;
  padding: 20px;
  font-size: 14px;
}

.no-eps-history {
  text-align: center;
  color: #718096;
  padding: 20px;
  font-size: 14px;
}

.eps-history-table {
  overflow-x: auto;
}

.eps-history-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.eps-history-table th {
  background: #2d3748;
  color: #e2e8f0;
  padding: 10px 8px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #4a5568;
  position: sticky;
  top: 0;
}

.eps-history-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #4a5568;
  color: #cbd5e0;
}

.eps-history-table tr:hover {
  background: #2d3748;
}

.eps-beat {
  color: #68d391;
  font-weight: 600;
}

.eps-miss {
  color: #fc8181;
  font-weight: 600;
}

.surprise-positive {
  color: #68d391;
  font-weight: 600;
}

.surprise-negative {
  color: #fc8181;
  font-weight: 600;
}

.reliability-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.reliability-excellent {
  background: #2d5016;
  color: #68d391;
}

.reliability-good {
  background: #2c5282;
  color: #90cdf4;
}

.reliability-fair {
  background: #744210;
  color: #f6ad55;
}

.reliability-poor {
  background: #742a2a;
  color: #fc8181;
}

.reliability-summary {
  background: #1a202c;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  border-left: 3px solid #4299e1;
}

.reliability-stats {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  color: #a0aec0;
  font-size: 12px;
}

.stat-value {
  font-weight: 600;
  font-size: 14px;
}

.stat-value.beat {
  color: #68d391;
}

.stat-value.miss {
  color: #fc8181;
}

.eps-history-section-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.result-badge.beat {
  background: #2d5016;
  color: #68d391;
}

.result-badge.miss {
  background: #742a2a;
  color: #fc8181;
}

.result-badge.meet {
  background: #2d3748;
  color: #cbd5e0;
}

.eps-history-table tr.beat {
  background: rgba(104, 211, 145, 0.1);
}

.eps-history-table tr.miss {
  background: rgba(252, 129, 129, 0.1);
}
</style>

