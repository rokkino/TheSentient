<template>
  <div class="earnings-list">
    <div class="earnings-header">
      <h2>Earnings Calendar</h2>
      <div class="earnings-filters">
        <label>Week:</label>
        <select v-model="currentWeek" @change="loadEarnings">
          <option v-for="week in weekOptions" :key="week.value" :value="week.value">
            {{ week.label }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading earnings...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="earnings.length === 0" class="no-earnings">
      No earnings found for this week.
    </div>
    <div v-else class="earnings-content">
      <div class="earnings-grouped">
        <div
          v-for="(group, date) in groupedEarnings"
          :key="date"
          class="earnings-day"
        >
          <h3 class="day-header">{{ formatDate(date) }}</h3>
          <div class="earnings-items">
            <div
              v-for="earning in group"
              :key="`${earning.symbol}-${earning.date}`"
              class="earning-item"
              @click="selectTicker(earning.symbol)"
            >
              <div class="earning-symbol">{{ earning.symbol }}</div>
              <div class="earning-company">{{ earning.company }}</div>
              <div class="earning-time">{{ earning.time || 'TBD' }}</div>
            </div>
          </div>
        </div>
      </div>

      <button
        v-if="hasMore"
        @click="loadMore"
        class="load-more-btn"
        :disabled="loadingMore"
      >
        {{ loadingMore ? 'Loading...' : 'Load More Weeks' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'

const props = defineProps({
  onTickerSelect: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['ticker-selected'])

const earnings = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(null)
const currentWeek = ref(0)
const weeksLoaded = ref(1)

const weekOptions = computed(() => {
  const options = []
  for (let i = 0; i < 12; i++) {
    const date = new Date()
    date.setDate(date.getDate() + (i * 7))
    options.push({
      value: i,
      label: `Week ${i + 1} (${formatDate(date.toISOString().split('T')[0])})`
    })
  }
  return options
})

const groupedEarnings = computed(() => {
  const grouped = {}
  earnings.value.forEach(earning => {
    const date = earning.date
    if (!grouped[date]) {
      grouped[date] = []
    }
    grouped[date].push(earning)
  })
  return grouped
})

const hasMore = computed(() => {
  return earnings.value.length > 0 && weeksLoaded.value < 8 // Max 8 weeks
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const loadEarnings = async (reset = true) => {
  if (reset) {
    earnings.value = []
    weeksLoaded.value = 1
  }
  
  loading.value = true
  error.value = null
  
  try {
    const startDate = new Date()
    startDate.setDate(startDate.getDate() + (currentWeek.value * 7))
    
    const response = await api.getEarnings(
      startDate.toISOString().split('T')[0],
      1,
      currentWeek.value
    )
    
    if (response.data && response.data.earnings) {
      if (reset) {
        earnings.value = response.data.earnings
      } else {
        earnings.value = [...earnings.value, ...response.data.earnings]
      }
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load earnings'
    console.error('Error loading earnings:', err)
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  loadingMore.value = true
  
  try {
    weeksLoaded.value++
    const startDate = new Date()
    startDate.setDate(startDate.getDate() + (weeksLoaded.value * 7))
    
    const response = await api.getEarnings(
      startDate.toISOString().split('T')[0],
      1,
      weeksLoaded.value
    )
    
    if (response.data && response.data.earnings) {
      earnings.value = [...earnings.value, ...response.data.earnings]
    }
  } catch (err) {
    console.error('Error loading more earnings:', err)
  } finally {
    loadingMore.value = false
  }
}

const selectTicker = (symbol) => {
  if (props.onTickerSelect) {
    props.onTickerSelect(symbol)
  }
  emit('ticker-selected', symbol)
}

onMounted(() => {
  loadEarnings()
})
</script>

<style scoped>
.earnings-list {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.earnings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #2d3748;
}

.earnings-header h2 {
  margin: 0;
  color: #e2e8f0;
  font-size: 24px;
}

.earnings-filters {
  display: flex;
  align-items: center;
  gap: 10px;
}

.earnings-filters label {
  color: #a0aec0;
  font-size: 14px;
}

.earnings-filters select {
  background: #2d3748;
  color: #e2e8f0;
  border: 1px solid #4a5568;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 14px;
  cursor: pointer;
}

.earnings-filters select:hover {
  border-color: #718096;
}

.loading, .error, .no-earnings {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
}

.error {
  color: #fc8181;
}

.earnings-content {
  flex: 1;
  overflow-y: auto;
}

.earnings-grouped {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.earnings-day {
  background: #2d3748;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #4a5568;
}

.day-header {
  margin: 0 0 12px 0;
  color: #e2e8f0;
  font-size: 18px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #4a5568;
}

.earnings-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.earning-item {
  background: #1a202c;
  border: 1px solid #4a5568;
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.earning-item:hover {
  background: #2d3748;
  border-color: #718096;
  transform: translateY(-2px);
}

.earning-symbol {
  font-size: 16px;
  font-weight: 600;
  color: #63b3ed;
  margin-bottom: 4px;
}

.earning-company {
  font-size: 12px;
  color: #a0aec0;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.earning-time {
  font-size: 11px;
  color: #718096;
}

.load-more-btn {
  margin-top: 24px;
  width: 100%;
  padding: 12px;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.load-more-btn:hover:not(:disabled) {
  background: #3182ce;
}

.load-more-btn:disabled {
  background: #4a5568;
  cursor: not-allowed;
  opacity: 0.6;
}
</style>

