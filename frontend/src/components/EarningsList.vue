<template>
  <div class="earnings-list-container">
    <div class="earnings-controls">
      <div class="search-container">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Search symbol or company..." 
          class="search-input"
        />
        <span v-if="searchQuery" class="clear-search" @click="searchQuery = ''">×</span>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
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

      <!-- Default View (Today/Tomorrow/Next) -->
      <template v-else>
        <!-- Today's Earnings -->
        <div class="earnings-section">
          <h3 class="section-title">
            📅 Today's Earnings ({{ formatDate(today) }})
          </h3>
          <div v-if="todayEarnings.length === 0" class="no-earnings">
            <p>No earnings scheduled for today</p>
          </div>
          <div v-else class="earnings-list">
            <div 
              v-for="earning in todayEarnings" 
              :key="`today-${earning.symbol}-${earning.date}`"
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
        
        <!-- Tomorrow's Earnings -->
        <div class="earnings-section">
          <h3 class="section-title">
            📅 Tomorrow's Earnings ({{ formatDate(tomorrow) }})
          </h3>
          <div v-if="tomorrowEarnings.length === 0" class="no-earnings">
            <p>No earnings scheduled for tomorrow</p>
          </div>
          <div v-else class="earnings-list">
            <div 
              v-for="earning in tomorrowEarnings" 
              :key="`tomorrow-${earning.symbol}-${earning.date}`"
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
      </template>
      
      <div class="summary">
        <p v-if="searchQuery">
          Found {{ filteredEarnings.length }} earnings for "{{ searchQuery }}"
        </p>
        <template v-else>
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
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'

const loading = ref(false)
const error = ref(null)
const earnings = ref([])
const searchQuery = ref('')

// Helper function to get next business day (skip weekends)
const getNextBusinessDay = (date) => {
  const newDate = new Date(date) // Don't mutate original
  newDate.setDate(newDate.getDate() + 1)
  
  // Skip weekends
  while (newDate.getDay() === 0 || newDate.getDay() === 6) {
    newDate.setDate(newDate.getDate() + 1)
  }
  
  return newDate.toISOString().split('T')[0]
}

const today = computed(() => {
  const now = new Date()
  return now.toISOString().split('T')[0]
})

const tomorrow = computed(() => {
  return getNextBusinessDay(today.value)
})

const filteredEarnings = computed(() => {
  if (!searchQuery.value) return []
  
  const query = searchQuery.value.toLowerCase().trim()
  return earnings.value.filter(e => {
    const symbol = (e.symbol || e.ticker || '').toLowerCase()
    const company = (e.company || e.companymearningsshortname || e.companyshortname || '').toLowerCase()
    
    return symbol.includes(query) || company.includes(query)
  }).slice(0, 50) // Limit results for performance
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

const loadEarnings = async () => {
  loading.value = true
  error.value = null
  
  try {
    console.log('Loading earnings...')
    console.log(`Today: ${today.value}, Tomorrow: ${tomorrow.value}`)
    
    // Fetch earnings for next 3 months to allow searching
    const response = await api.getEarnings(null, 3, 0)
    
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
    
    // Normalize and clean earnings data
    earningsData = earningsData.map(earning => {
      let symbol = earning.symbol || earning.ticker || ''
      if (typeof symbol !== 'string') {
        symbol = String(symbol)
      }
      symbol = symbol.trim().toUpperCase()
      
      let company = earning.company || earning.companymearningsshortname || earning.companyshortname || symbol
      if (typeof company !== 'string') {
        company = String(company)
      }
      company = company.trim()
      
      return {
        ...earning,
        symbol: symbol,
        company: company,
        ticker: symbol,
        date: earning.date || '',
        time: earning.time || 'TBD'
      }
    })
    
    earnings.value = earningsData
    
    console.log(`Today earnings (${today.value}):`, todayEarnings.value.length)
    console.log(`Tomorrow earnings (${tomorrow.value}):`, tomorrowEarnings.value.length)
  } catch (err) {
    console.error('Error loading earnings:', err)
    error.value = err.response?.data?.detail || err.message || 'Impossibile caricare i dati degli earnings. Riprova più tardi.'
    earnings.value = []
  } finally {
    loading.value = false
  }
}

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
  overflow-y: auto;
  padding: 20px;
  background-color: #050505;
  color: #fff;
}

.earnings-controls {
  margin-bottom: 20px;
}

.search-container {
  position: relative;
  max-width: 400px;
}

.search-input {
  width: 100%;
  padding: 10px 35px 10px 15px;
  background-color: #1a1a1a;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: #4299e1;
  outline: none;
  background-color: #222;
}

.clear-search {
  position: absolute;
  right: 18px;
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

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 20px;
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
</style>
