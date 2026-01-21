<template>
  <div class="earnings-list">
    <div class="earnings-header">
      <h2>Earnings Calendar</h2>
      <div class="earnings-controls">
        <div class="search-container">
            <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="Search symbol or ask AI..." 
                class="search-input"
                @keyup.enter="handleSearchEnter"
            />
            <button class="search-ai-btn" @click="askLlamaGeneral" title="Ask AI">
                🤖
            </button>
        </div>
        <button class="settings-icon-btn" @click="$emit('open-settings')" title="Settings">
            ⚙️
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <span>Loading earnings...</span>
    </div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="filteredEarnings.length === 0" class="no-earnings">
      <span class="no-earnings-icon">📅</span>
      <p>No earnings found</p>
      <p class="no-earnings-hint">Try refreshing or check back later</p>
    </div>
    <div v-else class="earnings-content" ref="earningsContentRef">
      <div class="earnings-grouped-list">
        <div
          v-for="group in groupedEarnings"
          :key="group.date"
          class="earnings-date-group"
        >
          <div class="date-header">
            <div class="date-day">{{ formatDay(group.date) }}</div>
            <div class="date-full">{{ formatDateHeader(group.date) }}</div>
          </div>
          <div class="earnings-for-date">
            <div
              v-for="earning in group.earnings"
              :key="`${earning.symbol}-${earning.date}`"
              class="earning-item"
            >
              <div class="earning-main">
                <div class="earning-company" @click="openChartModal(earning)">
                  <span class="earning-symbol">{{ earning.symbol }}</span>
                  <span class="earning-name">{{ earning.company || earning.symbol }}</span>
                </div>
                <!-- Time badge -->
                <span 
                  class="time-badge" 
                  :class="getTimeBadgeClass(earning.time)"
                  :title="earning.time"
                >
                  {{ getTimeBadgeIcon(earning.time) }} {{ formatEarningTime(earning.time) }}
                </span>
              </div>
              <div class="earning-actions">
                <button
                  class="chart-btn"
                  @click.stop="openChartModal(earning)"
                  title="View Chart"
                >
                  📈
                </button>
                <button
                  class="llama-btn" 
                  @click.stop="askLlama(earning)"
                  title="Ask AI"
                >
                  🦙
                </button>
                <button
                  class="gemini-btn" 
                  @click.stop="askGemini(earning)"
                  title="Ask Gemini"
                >
                  ✨
                </button>
                <button
                  class="star-btn"
                  :class="{ 'starred': isInWatchlist(earning.symbol) }"
                  @click.stop="addToStockTab(earning)"
                  :title="'Add to Stock Tab'"
                >
                  ☆
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="hasMore && !loadingMore" class="load-more-indicator">
        Scroll down to load next 6 months...
      </div>
      <div v-if="loadingMore" class="loading-more-indicator">
        <div class="loading-spinner"></div>
        <span>Loading next 6 months...</span>
      </div>
    </div>

    <!-- Llama Modal -->
    <div v-if="showLlamaModal" class="modal-overlay" @click="closeLlamaModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ selectedEarning ? `Ask ${selectedProvider === 'gemini' ? 'Gemini' : 'Llama'} about ${selectedEarning.symbol}` : `Ask ${selectedProvider === 'gemini' ? 'Gemini' : 'Llama'} AI` }}</h3>
          <button class="close-btn" @click="closeLlamaModal">×</button>
        </div>
        <div class="modal-body">
          <div v-if="llamaLoading" class="loading-spinner"></div>
          <div v-else-if="llamaResponse" class="llama-response">
            <p>{{ llamaResponse }}</p>
            <button class="ask-another-btn" @click="llamaResponse = ''">Ask Another Question</button>
          </div>
          <div v-else class="llama-input-container">
            <p>{{ selectedEarning ? 'Ask a specific question or get a general summary:' : 'Ask any question about earnings or market trends:' }}</p>
            <div class="input-group">
                <input 
                    v-model="llamaQuestion" 
                    :placeholder="selectedEarning ? 'e.g. What are the revenue expectations?' : 'e.g. Which tech companies report next week?'" 
                    class="llama-input"
                    @keyup.enter="submitLlamaQuestion"
                />
                <button class="submit-btn" @click="submitLlamaQuestion">Ask</button>
            </div>
            <div class="quick-actions" v-if="selectedEarning">
                <button @click="submitLlamaQuestion('Summary')">Summary</button>
                <button @click="submitLlamaQuestion('Revenue Expectations')">Revenue</button>
                <button @click="submitLlamaQuestion('EPS Expectations')">EPS</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chart Modal -->
    <div v-if="showChartModal" class="modal-overlay" @click="closeChartModal">
      <div class="chart-modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ chartEarning?.symbol }} - {{ chartEarning?.company || chartEarning?.symbol }}</h3>
          <button class="close-btn" @click="closeChartModal">×</button>
        </div>
        <div class="chart-modal-body">
          <div v-if="chartLoading" class="loading">
            <div class="loading-spinner"></div>
            <span>Loading chart...</span>
          </div>
          <div v-else-if="chartData" class="chart-info">
            <div class="chart-price-section">
              <span class="chart-price">${{ chartData.price?.toFixed(2) || 'N/A' }}</span>
              <span class="chart-change" :class="{ 'positive': chartData.change >= 0, 'negative': chartData.change < 0 }">
                {{ chartData.change >= 0 ? '+' : '' }}{{ chartData.changePercent?.toFixed(2) || 0 }}%
              </span>
            </div>
            <div class="chart-details">
              <div class="detail-row"><span>Open:</span><span>${{ chartData.open?.toFixed(2) || 'N/A' }}</span></div>
              <div class="detail-row"><span>High:</span><span>${{ chartData.high?.toFixed(2) || 'N/A' }}</span></div>
              <div class="detail-row"><span>Low:</span><span>${{ chartData.low?.toFixed(2) || 'N/A' }}</span></div>
              <div class="detail-row"><span>Volume:</span><span>{{ formatVolume(chartData.volume) }}</span></div>
            </div>
            <div class="earnings-info" v-if="chartEarning">
              <div class="earnings-badge" :class="getTimeBadgeClass(chartEarning.time)">
                {{ getTimeBadgeIcon(chartEarning.time) }} {{ chartEarning.time || 'TBD' }}
              </div>
              <p class="earnings-date">Earnings: {{ formatDateHeader(chartEarning.date) }}</p>
            </div>
          </div>
          <div v-else class="no-data">Unable to load chart data</div>
        </div>
        <div class="chart-modal-footer">
          <button class="add-tab-btn" @click="addToStockTab(chartEarning)">
            ⭐ Add to Stock Tab
          </button>
        </div>
      </div>
    </div>

    <!-- Tab Selector Modal -->
    <div v-if="showTabSelector" class="modal-overlay" @click="closeTabSelector">
      <div class="tab-selector-content" @click.stop>
        <div class="modal-header">
          <h3>Select Stock Tab</h3>
          <button class="close-btn" @click="closeTabSelector">×</button>
        </div>
        <div class="tab-selector-body">
          <p>Choose which tab to add <strong>{{ pendingSymbol }}</strong> to:</p>
          <div class="tab-options">
            <button 
              v-for="tab in stockTabs" 
              :key="tab.id" 
              class="tab-option"
              @click="confirmAddToTab(tab)"
            >
              📊 {{ tab.name || tab.symbol || 'Stock Tab' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import api from '../services/api'
import { getCached, setCached } from '../utils/cache'
import { useWatchlistStore } from '../stores/watchlist'

const emit = defineEmits(['ticker-selected', 'open-settings', 'add-to-stock-tab', 'create-stock-tab'])

// Inject tabs from parent (Dashboard)
const tabs = inject('tabs', ref([]))

const earnings = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(null)
const monthsLoaded = ref(1)  // Track how many 6-month blocks we've loaded (1 = first 6 months)
const earningsContentRef = ref(null)

const searchQuery = ref('')
const showLlamaModal = ref(false)
const selectedEarning = ref(null)
const llamaResponse = ref('')
const llamaLoading = ref(false)
const llamaQuestion = ref('')
const selectedProvider = ref('local') // 'local' (Llama) or 'gemini'

// Chart modal state
const showChartModal = ref(false)
const chartEarning = ref(null)
const chartData = ref(null)
const chartLoading = ref(false)

// Tab selector state
const showTabSelector = ref(false)
const pendingSymbol = ref('')
const pendingEarning = ref(null)

// Get stock tabs from injected tabs
const stockTabs = computed(() => {
  return tabs.value.filter(tab => tab.type === 'stock' || tab.type === 'stocks')
})

const filteredEarnings = computed(() => {
  console.log(`[FRONTEND] filteredEarnings computed - earnings.value.length: ${earnings.value.length}`)
  
  let filtered = earnings.value
  
  // Filter by search query
  if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(e => 
          e.symbol.toLowerCase().includes(query) || 
          (e.company && e.company.toLowerCase().includes(query))
      )
  }

  // Filter out mock data and only show real earnings from yahoo_earnings_calendar or yfinance
  filtered = filtered
    .filter(earning => {
      const source = earning.source || ''
      const passes = source === 'yahoo_earnings_calendar' || 
             source === 'yfinance' || 
             source === 'nasdaq' ||
             source === 'nasdaq_api' ||
             source === 'yahoo_calendar' ||
             (!source && earning.date && earning.symbol) // Include if has valid data
      return passes
    })
    .sort((a, b) => {
      // Sort by date ascending
      const dateA = new Date(a.date)
      const dateB = new Date(b.date)
      return dateA - dateB
    })
  console.log(`[FRONTEND] filteredEarnings computed - filtered.length: ${filtered.length}`)
  if (filtered.length > 0) {
    console.log(`[FRONTEND] First filtered earning:`, filtered[0])
  }
  return filtered
})

// Get end date based on loaded months (6 months per block) - not used anymore, kept for compatibility
const getEndDate = () => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const endDate = new Date(today)
  endDate.setMonth(endDate.getMonth() + (monthsLoaded.value * 6))  // 6 months per block
  endDate.setHours(23, 59, 59, 999)
  return endDate
}

// Show all loaded earnings (no filtering by date range needed, backend handles it)
const visibleEarnings = computed(() => {
  return filteredEarnings.value
})

// Group earnings by date
const groupedEarnings = computed(() => {
  const groups = {}
  
  visibleEarnings.value.forEach(earning => {
    const dateKey = earning.date
    if (!groups[dateKey]) {
      groups[dateKey] = {
        date: dateKey,
        earnings: []
      }
    }
    groups[dateKey].earnings.push(earning)
  })
  
  // Sort groups by date
  return Object.values(groups).sort((a, b) => {
    return new Date(a.date) - new Date(b.date)
  })
})

const formatDay = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const dateOnly = new Date(date)
  dateOnly.setHours(0, 0, 0, 0)
  
  if (dateOnly.getTime() === today.getTime()) {
    return 'TODAY'
  } else if (dateOnly.getTime() === tomorrow.getTime()) {
    return 'TOMORROW'
  } else {
    return date.toLocaleDateString('en-US', { weekday: 'long' }).toUpperCase()
  }
}

const formatDateHeader = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

const hasMore = computed(() => {
  // Always allow loading more (infinite scroll for 6-month blocks)
  // Limit to reasonable amount (e.g., 4 years = 8 blocks of 6 months)
  return monthsLoaded.value < 8
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const dateOnly = new Date(date)
  dateOnly.setHours(0, 0, 0, 0)
  
  // Check if it's today, tomorrow, or format normally
  if (dateOnly.getTime() === today.getTime()) {
    return 'Today'
  } else if (dateOnly.getTime() === tomorrow.getTime()) {
    return 'Tomorrow'
  } else {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }
}

const loadEarnings = async (reset = true) => {
  if (reset) {
    earnings.value = []
    monthsLoaded.value = 1
  }
  
  loading.value = true
  error.value = null
  
  try {
    // Fetch earnings starting from today
    const today = new Date()
    const startDateStr = today.toISOString().split('T')[0]  // Format: YYYY-MM-DD
    
    console.log('='.repeat(60))
    console.log('[FRONTEND] loadEarnings called')
    console.log(`[FRONTEND] Starting from: ${startDateStr}`)
    console.log(`[FRONTEND] Reset: ${reset}`)
    console.log('='.repeat(60))
    
    // Fetch first 6 months starting from today
    // We omit endDate to force the backend to use the reliable Nasdaq API (get_earnings_calendar)
    // instead of the flaky YahooEarningsCalendar which is used for date ranges.
    const response = await api.getEarnings(
      startDateStr,
      6,   // months
      0,   // offset (first block)
      null // endDate (must be null to use calendar mode)
    )
    
    const earningsData = response.data
    console.log('='.repeat(60))
    console.log('[FRONTEND] Earnings response received')
    console.log(`[FRONTEND] Total earnings: ${earningsData?.earnings?.length || 0}`)
    if (earningsData?.earnings?.length > 0) {
      console.log(`[FRONTEND] First: ${earningsData.earnings[0].symbol} on ${earningsData.earnings[0].date}`)
      console.log(`[FRONTEND] Last: ${earningsData.earnings[earningsData.earnings.length - 1].symbol} on ${earningsData.earnings[earningsData.earnings.length - 1].date}`)
    }
    console.log('='.repeat(60))
    
    if (earningsData && earningsData.earnings) {
      const newEarnings = earningsData.earnings.filter(e => {
        // Only include real earnings from yahoo_earnings_calendar or yfinance or nasdaq
        const source = e.source || ''
        const passes = source === 'yahoo_earnings_calendar' || 
               source === 'yfinance' || 
               source === 'nasdaq' ||
               source === 'nasdaq_api' ||
               (!source && e.date && e.symbol)
        return passes
      })
      
      console.log(`[FRONTEND] After filtering: ${newEarnings.length} earnings`)
      
      if (reset) {
        earnings.value = newEarnings
      } else {
        // Merge and remove duplicates
        const existingKeys = new Set(earnings.value.map(e => `${e.symbol}-${e.date}`))
        const uniqueNew = newEarnings.filter(e => !existingKeys.has(`${e.symbol}-${e.date}`))
        earnings.value = [...earnings.value, ...uniqueNew]
      }
    } else {
      console.log('No earnings data in response')
      earnings.value = []
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load earnings'
    console.error('Error loading earnings:', err)
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  if (loadingMore.value) return
  
  loadingMore.value = true
  
  try {
    monthsLoaded.value++  // Load next 6-month block
    const startDate = new Date()
    const startDateStr = startDate.toISOString().split('T')[0]
    
    console.log(`[FRONTEND] Loading next 6-month block (offset_months: ${monthsLoaded.value - 1})`)
    
    // Fetch next 6 months (offset_months determines which block)
    const response = await api.getEarnings(
      startDateStr,
      6,  // 6 months per block
      monthsLoaded.value - 1  // offset_months: 0=first 6mo, 1=next 6mo, etc.
    )
    
    if (response.data && response.data.earnings) {
      const newEarnings = response.data.earnings.filter(e => {
        const source = e.source || ''
        return source === 'yahoo_earnings_calendar' || 
               source === 'yfinance' || 
               source === 'nasdaq' ||
               source === 'nasdaq_api' ||
               (!source && e.date && e.symbol)
      })
      
      // Merge and remove duplicates
      const existingKeys = new Set(earnings.value.map(e => `${e.symbol}-${e.date}`))
      const uniqueNew = newEarnings.filter(e => !existingKeys.has(`${e.symbol}-${e.date}`))
      earnings.value = [...earnings.value, ...uniqueNew]
      
      console.log(`[FRONTEND] Added ${uniqueNew.length} new earnings (total: ${earnings.value.length})`)
    }
  } catch (err) {
    console.error('Error loading more earnings:', err)
    error.value = err.response?.data?.detail || 'Failed to load more earnings'
    monthsLoaded.value--  // Revert on error
  } finally {
    loadingMore.value = false
  }
}

// Infinite scroll: detect when user scrolls near bottom
const handleScroll = () => {
  if (!earningsContentRef.value || loadingMore.value || !hasMore.value) return
  
  const earningsContent = earningsContentRef.value
  const scrollTop = earningsContent.scrollTop
  const scrollHeight = earningsContent.scrollHeight
  const clientHeight = earningsContent.clientHeight
  
  // Load more when within 200px of bottom
  if (scrollHeight - scrollTop - clientHeight < 200) {
    loadMore()
  }
}

const watchlistStore = useWatchlistStore()

const isInWatchlist = (symbol) => {
  return watchlistStore.watchlist.some(item => item.symbol === symbol)
}

const toggleWatchlist = async (earning) => {
  const symbol = earning.symbol
  const name = earning.company || earning.symbol
  
  try {
    if (isInWatchlist(symbol)) {
      await watchlistStore.removeItem(symbol)
    } else {
      await watchlistStore.addItem(symbol, name)
    }
  } catch (error) {
    console.error('Error toggling watchlist:', error)
    alert(`Failed to ${isInWatchlist(symbol) ? 'remove' : 'add'} ${symbol} from watchlist`)
  }
}

const selectTicker = (symbol) => {
  emit('ticker-selected', symbol)
}

// Time badge helpers
const getTimeBadgeClass = (time) => {
  if (!time) return 'time-tbd'
  const timeLower = time.toLowerCase()
  if (timeLower.includes('before') || timeLower.includes('bmo') || timeLower.includes('pre')) {
    return 'time-pre'
  } else if (timeLower.includes('after') || timeLower.includes('amc') || timeLower.includes('post')) {
    return 'time-after'
  }
  return 'time-tbd'
}

const getTimeBadgeIcon = (time) => {
  if (!time) return '⏰'
  const timeLower = time.toLowerCase()
  if (timeLower.includes('before') || timeLower.includes('bmo') || timeLower.includes('pre')) {
    return '🌅'
  } else if (timeLower.includes('after') || timeLower.includes('amc') || timeLower.includes('post')) {
    return '🌙'
  }
  return '⏰'
}

const formatEarningTime = (time) => {
  if (!time) return 'TBD'
  const timeLower = time.toLowerCase()
  if (timeLower.includes('before') || timeLower.includes('bmo') || timeLower.includes('pre')) {
    return 'Pre-Market'
  } else if (timeLower.includes('after') || timeLower.includes('amc') || timeLower.includes('post')) {
    return 'After Hours'
  }
  return 'TBD'
}

const formatVolume = (volume) => {
  if (!volume) return 'N/A'
  if (volume >= 1000000000) return (volume / 1000000000).toFixed(2) + 'B'
  if (volume >= 1000000) return (volume / 1000000).toFixed(2) + 'M'
  if (volume >= 1000) return (volume / 1000).toFixed(2) + 'K'
  return volume.toString()
}

// Chart modal methods
const openChartModal = async (earning) => {
  chartEarning.value = earning
  showChartModal.value = true
  chartLoading.value = true
  chartData.value = null
  
  try {
    const response = await api.getQuote(earning.symbol, '1d')
    if (response.data) {
      chartData.value = {
        price: response.data.price || response.data.close,
        change: response.data.change || 0,
        changePercent: response.data.changePercent || response.data.change_percent || 0,
        open: response.data.open,
        high: response.data.high,
        low: response.data.low,
        volume: response.data.volume
      }
    }
  } catch (err) {
    console.error('Error fetching chart data:', err)
  } finally {
    chartLoading.value = false
  }
}

const closeChartModal = () => {
  showChartModal.value = false
  chartEarning.value = null
  chartData.value = null
}

// Tab addition methods
const addToStockTab = (earning) => {
  const symbol = earning?.symbol || chartEarning.value?.symbol
  if (!symbol) return
  
  pendingSymbol.value = symbol
  pendingEarning.value = earning || chartEarning.value
  
  const stockTabCount = stockTabs.value.length
  
  if (stockTabCount === 0) {
    // No stock tabs - create new one
    emit('create-stock-tab', { symbol, name: pendingEarning.value?.company || symbol })
    closeChartModal()
  } else if (stockTabCount === 1) {
    // One stock tab - add directly
    emit('add-to-stock-tab', { tabId: stockTabs.value[0].id, symbol, name: pendingEarning.value?.company || symbol })
    closeChartModal()
  } else {
    // Multiple stock tabs - show selector
    showTabSelector.value = true
  }
}

const confirmAddToTab = (tab) => {
  emit('add-to-stock-tab', { tabId: tab.id, symbol: pendingSymbol.value, name: pendingEarning.value?.company || pendingSymbol.value })
  closeTabSelector()
  closeChartModal()
}

const closeTabSelector = () => {
  showTabSelector.value = false
  pendingSymbol.value = ''
  pendingEarning.value = null
}

onMounted(() => {
  loadEarnings()
  // Load watchlist to check which items are already added
  watchlistStore.loadWatchlist()
  
  // Setup infinite scroll after component is mounted and ref is available
  setTimeout(() => {
    if (earningsContentRef.value) {
      earningsContentRef.value.addEventListener('scroll', handleScroll)
    }
  }, 100)
})

onUnmounted(() => {
  // Cleanup scroll listener
  if (earningsContentRef.value) {
    earningsContentRef.value.removeEventListener('scroll', handleScroll)
  }
})

const askLlama = (earning) => {
  selectedEarning.value = earning
  selectedProvider.value = 'local'
  showLlamaModal.value = true
  llamaResponse.value = ''
  // If asking about specific earning, clear question. If general (from search bar), use search query
  if (earning) {
      llamaQuestion.value = ''
  } else {
      llamaQuestion.value = searchQuery.value
  }
}

const askLlamaGeneral = () => {
    askLlama(null)
}

const handleSearchEnter = () => {
    // If search query looks like a question or user explicitly wants to ask AI
    // For now, let's say if it's long and has spaces, it might be a question
    if (searchQuery.value.length > 0) {
        // Check if it matches any symbol exactly
        const exactMatch = earnings.value.find(e => e.symbol.toLowerCase() === searchQuery.value.toLowerCase())
        
        if (!exactMatch && (searchQuery.value.includes(' ') || searchQuery.value.length > 5)) {
            askLlamaGeneral()
        }
    }
}

const askGemini = (earning) => {
  selectedEarning.value = earning
  selectedProvider.value = 'gemini'
  showLlamaModal.value = true
  llamaResponse.value = ''
  llamaQuestion.value = ''
}

const closeLlamaModal = () => {
    showLlamaModal.value = false
    selectedEarning.value = null
}

const submitLlamaQuestion = async (predefinedQuestion = null) => {
    const question = typeof predefinedQuestion === 'string' ? predefinedQuestion : llamaQuestion.value
    if (!question) return

    llamaLoading.value = true
    try {
        const payload = {
            question: question
        }
        
        if (selectedEarning.value) {
            payload.symbol = selectedEarning.value.symbol
            payload.company = selectedEarning.value.company
            payload.date = selectedEarning.value.date
        }

        const response = await api.askLlamaAboutEarning(
            payload.symbol,
            payload.company,
            payload.date,
            payload.symbol,
            payload.company,
            payload.date,
            payload.question,
            selectedProvider.value
        )
        llamaResponse.value = response.data.response
    } catch (e) {
        llamaResponse.value = `Error asking ${selectedProvider.value === 'gemini' ? 'Gemini' : 'Llama'}: ` + (e.response?.data?.detail || e.message)
    } finally {
        llamaLoading.value = false
    }
}
</script>

<style scoped>
.earnings-list {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #000;
  color: #e0e0e0;
}

.earnings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #333;
}

.earnings-header h2 {
  margin: 0;
  color: #fff;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.search-container {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  max-width: 400px;
  margin: 0 16px;
}

.search-input {
  width: 100%;
  padding: 10px 40px 10px 16px;
  background-color: #1a1a1a;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #4299e1;
  background-color: #222;
}

.search-ai-btn {
  position: absolute;
  right: 8px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-ai-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: scale(1.1);
}

.settings-icon-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
}

.settings-icon-btn:hover {
  color: #fff;
  background-color: #1a1a1a;
  transform: rotate(90deg);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 16px;
  color: #888;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #333;
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error {
  text-align: center;
  padding: 40px;
  color: #f44336;
  font-size: 14px;
}

.no-earnings {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.no-earnings-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-earnings p {
  margin: 8px 0;
  font-size: 14px;
}

.no-earnings-hint {
  font-size: 12px;
  color: #555;
}

.earnings-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.earnings-grouped-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.earnings-date-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.date-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 8px;
  border-bottom: 1px solid #333;
  margin-bottom: 8px;
}

.date-day {
  font-size: 32px;
  font-weight: 700;
  color: #4299e1;
  letter-spacing: 1px;
  text-transform: uppercase;
  font-family: 'Roboto', sans-serif;
}

.date-full {
  font-size: 14px;
  color: #888;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.earnings-for-date {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.earning-item {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 14px 16px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.earning-item:hover {
  background: #222;
  border-color: #4299e1;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.1);
}

.earning-company {
  flex: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
}

.earning-company {
  display: flex;
  align-items: center;
  gap: 12px;
}

.earning-symbol {
  font-size: 18px;
  font-weight: 700;
  color: #4299e1;
  letter-spacing: 0.5px;
  font-family: 'Roboto Mono', monospace;
}

.earning-name {
  font-size: 14px;
  color: #aaa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.star-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 24px;
  cursor: pointer;
  padding: 4px 8px;
  transition: all 0.2s;
  line-height: 1;
  flex-shrink: 0;
}

.star-btn:hover {
  color: #4299e1;
  transform: scale(1.2);
}

.star-btn.starred {
  color: #4299e1;
}

.star-btn.starred:hover {
  color: #ffd700;
}

.load-more-btn {
  margin-top: 24px;
  width: 100%;
  padding: 12px;
  background: #1a1a1a;
  color: #4299e1;
  border: 1px solid #4299e1;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.3px;
}

.load-more-btn:hover:not(:disabled) {
  background: #4299e1;
  color: #fff;
}

.load-more-indicator {
  margin-top: 24px;
  text-align: center;
  padding: 16px;
  color: #888;
  font-size: 14px;
  font-style: italic;
}

.loading-more-indicator {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  gap: 12px;
  color: #888;
}

.loading-more-indicator .loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #333;
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Custom scrollbar */
.earnings-content::-webkit-scrollbar {
  width: 6px;
}

.earnings-content::-webkit-scrollbar-track {
  background: #0a0a0a;
  border-radius: 3px;
}

.earnings-content::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 3px;
  transition: background 0.2s;
}

.earnings-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.earnings-list {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #050505;
  color: #e0e0e0;
}

.earnings-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #222;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.earnings-header h2 {
  margin: 0;
  color: #fff;
  font-size: 18px;
  font-weight: 300;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.earnings-controls {
    display: flex;
    align-items: center;
    gap: 12px;
}

.search-input {
    background: #111;
    border: 1px solid #333;
    border-radius: 2px;
    padding: 10px 12px;
    color: #fff;
    font-size: 13px;
    width: 200px;
    transition: border-color 0.2s;
}

.search-input:focus {
    border-color: #666;
    outline: none;
    width: 250px;
}

.settings-icon-btn {
    background: #111;
    border: 1px solid #333;
    border-radius: 2px;
    color: #ccc;
    cursor: pointer;
    padding: 8px;
    font-size: 16px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 38px;
    width: 38px;
}

.settings-icon-btn:hover {
    background: #1a1a1a;
    border-color: #666;
    color: #fff;
}

.ask-ai-btn {
    background: #4299e1;
    color: #fff;
    border: none;
    border-radius: 2px;
    padding: 0 12px;
    height: 38px;
    cursor: pointer;
    font-weight: 600;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
}

.ask-ai-btn:hover {
    background: #3182ce;
    transform: translateY(-1px);
}

.llama-btn {
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    padding: 4px;
    transition: transform 0.2s;
}

.llama-btn:hover {
    transform: scale(1.2);
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 20px;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.llama-input-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.input-group {
    display: flex;
    gap: 8px;
}

.llama-input {
    flex: 1;
    background: #000;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 10px;
    color: #fff;
}

.submit-btn {
    background: #4299e1;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 0 16px;
    cursor: pointer;
    font-weight: 600;
}

.quick-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.quick-actions button {
    background: #333;
    border: none;
    border-radius: 16px;
    padding: 6px 12px;
    color: #ccc;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}

.quick-actions button:hover {
    background: #444;
    color: #fff;
}

.llama-response {
    background: #252525;
    padding: 16px;
    border-radius: 8px;
    line-height: 1.5;
    color: #e0e0e0;
    white-space: pre-wrap;
}

.ask-another-btn {
    margin-top: 16px;
    background: #333;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    color: #fff;
    cursor: pointer;
    width: 100%;
}

/* Earning card layout */
.earning-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.earning-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* Time badges */
.time-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.time-pre {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.time-after {
  background: rgba(249, 115, 22, 0.2);
  color: #fb923c;
  border: 1px solid rgba(249, 115, 22, 0.3);
}

.time-tbd {
  background: rgba(107, 114, 128, 0.2);
  color: #9ca3af;
  border: 1px solid rgba(107, 114, 128, 0.3);
}

/* Chart button */
.chart-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 6px;
  transition: all 0.2s;
  border-radius: 4px;
}

.chart-btn:hover {
  color: #4299e1;
  background: rgba(66, 153, 225, 0.1);
  transform: scale(1.1);
}

/* Chart Modal */
.chart-modal-content {
  background: #1a1a1a;
  border-radius: 16px;
  padding: 0;
  max-width: 450px;
  width: 90%;
  overflow: hidden;
  border: 1px solid #333;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
}

.chart-modal-body {
  padding: 24px;
}

.chart-price-section {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;
}

.chart-price {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
}

.chart-change {
  font-size: 18px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 6px;
}

.chart-change.positive {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.chart-change.negative {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.chart-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: #252525;
  border-radius: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.detail-row span:first-child {
  color: #888;
}

.detail-row span:last-child {
  color: #fff;
  font-weight: 500;
}

.earnings-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #252525;
  border-radius: 12px;
}

.earnings-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.earnings-date {
  color: #888;
  font-size: 13px;
  margin: 0;
}

.chart-modal-footer {
  padding: 16px 24px;
  background: #151515;
  border-top: 1px solid #333;
}

.add-tab-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #4299e1, #3182ce);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.add-tab-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
}

.no-data {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* Tab Selector Modal */
.tab-selector-content {
  background: #1a1a1a;
  border-radius: 16px;
  padding: 0;
  max-width: 350px;
  width: 90%;
  overflow: hidden;
  border: 1px solid #333;
}

.tab-selector-body {
  padding: 24px;
}

.tab-selector-body p {
  color: #aaa;
  margin-bottom: 16px;
  font-size: 14px;
}

.tab-selector-body strong {
  color: #4299e1;
}

.tab-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tab-option {
  width: 100%;
  padding: 14px 16px;
  background: #252525;
  border: 1px solid #333;
  border-radius: 10px;
  color: #fff;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-option:hover {
  background: #333;
  border-color: #4299e1;
  transform: translateX(4px);
}
</style>
