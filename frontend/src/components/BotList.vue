<template>
  <div class="bot-list-container">
    <div class="leaderboard-section" v-if="bots.length > 0">
      <div class="leaderboard-header">
        <h3>🏆 Performance Leaderboard</h3>
        <div class="metric-toggles">
          <button 
            :class="{ active: leaderboardMetric === 'winRate' }" 
            @click="leaderboardMetric = 'winRate'"
          >Win Rate</button>
          <button 
            :class="{ active: leaderboardMetric === 'profit' }" 
            @click="leaderboardMetric = 'profit'"
          >Total Profit</button>
        </div>
      </div>
      
      <!-- Performance Chart -->
      <div class="performance-chart-container" v-if="leaderboardBots.length > 0">
        <div class="chart-and-overlay">
          <div ref="chartContainer" class="chart-wrapper" v-show="!loading"></div>
          <div ref="chartOverlay" class="chart-avatar-overlay" v-show="!loading"></div>
        </div>
        <div class="chart-legend" v-if="!loading">
          <div 
            v-for="(bot, index) in leaderboardBots" 
            :key="bot.id" 
            class="legend-item"
            :style="{ '--bot-color': getBotColor(bot.name) }"
          >
            <div class="legend-left">
              <div class="legend-color"></div>
              <div class="legend-bot-icon" :style="{ borderColor: getBotColor(bot.name) }">
                <img :src="botIconUrl" :alt="bot.name" class="legend-bot-img" />
              </div>
            </div>
            <div class="legend-content">
              <div class="legend-name-row">
                <span class="legend-name">{{ bot.name }}</span>
                <span class="legend-rank">#{{ index + 1 }}</span>
              </div>
              <div class="legend-stats">
                <span class="legend-stat">
                  <span class="stat-label">{{ leaderboardMetric === 'winRate' ? 'Win Rate' : 'Profit' }}:</span>
                  <span class="stat-value">{{ formatMetricValue(bot) }}</span>
                </span>
                <span class="legend-stat">
                  <span class="stat-label">Trades:</span>
                  <span class="stat-value">{{ bot.totalTrades || 0 }}</span>
                </span>
                <span class="legend-stat">
                  <span class="stat-label">Status:</span>
                  <span class="stat-value status" :class="bot.status?.toLowerCase() || 'inactive'">
                    {{ (bot.status || 'INACTIVE').toUpperCase() }}
                  </span>
                </span>
                <span v-if="(bot.status === 'active') && (bot.activatedAt || bot.activated_at)" class="legend-stat legend-active-since">
                  <span class="stat-label start-flag-label" title="Attivo da">
                    <span class="start-flag-icon" aria-hidden="true">🏁</span>
                    Attivo dal
                  </span>
                  <span class="stat-value">{{ formatActiveSince(bot.activatedAt || bot.activated_at) }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="leaderboard-graph">
        <div v-for="(bot, index) in leaderboardBots" :key="bot.id" class="graph-row" :style="{ '--bot-color': getBotColor(bot.name) }">
          <div class="rank">{{ index + 1 }}</div>
          <div class="bot-info">
            <div class="bot-avatar">
              <img :src="botIconUrl" :alt="bot.name" class="bot-avatar-img" />
            </div>
            <span class="bot-name" :title="bot.name">{{ bot.name }}</span>
          </div>
          <div class="bar-container">
            <div 
              class="bar" 
              :style="{ width: getBarWidth(bot) + '%' }"
              :class="[leaderboardMetric, { empty: getBarWidth(bot) === 0 }]"
            >
              <div class="bar-glow" v-if="getBarWidth(bot) > 0"></div>
            </div>
            <div class="bar-empty-hint" v-if="getBarWidth(bot) === 0">—</div>
          </div>
          <div class="metric-value">
            {{ formatMetricValue(bot) }}
          </div>
        </div>
      </div>
    </div>

    <div class="section-divider" v-if="bots.length > 0"></div>

    <div v-if="loading" class="loading">Loading bots...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="bots.length === 0" class="no-bots">
      <p>No bots available yet. Create your first bot to get started!</p>
    </div>
    <div v-else class="bots-grid">
      <BotCard
        v-for="bot in bots"
        :key="bot.id"
        :bot="bot"
        @configure="handleConfigureBot"
        @activate="handleActivateBot"
        @deactivate="handleDeactivateBot"
        @import="handleImportBot"
        @export="handleExportBot"
      />
    </div>
    
    <BotConfigModal
      :show="showConfigModal"
      :bot="selectedBot"
      @close="showConfigModal = false"
      @saved="handleConfigSaved"
    />
    
    <CreateBotModal
      :show="showCreateModal"
      @close="showCreateModal = false"
      @created="handleBotCreated"
    />
    
    <ImportBotModal
      :show="showImportModal"
      :target-bot="importTargetBot"
      @close="showImportModal = false"
      @imported="handleBotImported"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue'
import { createChart } from 'lightweight-charts'
import botIconUrl from '../assets/bot_icon.jpg'
import BotCard from './BotCard.vue'
import BotConfigModal from './BotConfigModal.vue'
import CreateBotModal from './CreateBotModal.vue'
import ImportBotModal from './ImportBotModal.vue'
import api from '../services/api'

const emit = defineEmits(['create-bot'])

const showCreateModal = ref(false)
const showImportModal = ref(false)
const importTargetBot = ref(null)

const bots = ref([])
const loading = ref(false)
const error = ref(null)
const selectedBot = ref(null)
const showConfigModal = ref(false)

// Leaderboard Logic
const leaderboardMetric = ref('winRate') // 'winRate' or 'profit'
const chartContainer = ref(null)
const chartOverlay = ref(null)
let chart = null
let seriesMap = new Map()
const lastPointByBotId = new Map()
let avatarOverlayUpdater = null
let isInitializing = false

const leaderboardBots = computed(() => {
  return [...bots.value].sort((a, b) => {
    if (leaderboardMetric.value === 'winRate') {
      return b.winRate - a.winRate
    } else {
      return b.profit - a.profit
    }
  }).slice(0, 5) // Top 5
})

const maxMetricValue = computed(() => {
  if (bots.value.length === 0) return 100
  
  if (leaderboardMetric.value === 'winRate') {
    return 100 // Win rate is always out of 100%
  } else {
    const maxProfit = Math.max(...bots.value.map(b => b.profit))
    return maxProfit > 0 ? maxProfit : 100 // Avoid division by zero
  }
})

const getBarWidth = (bot) => {
  let value = 0
  let max = maxMetricValue.value
  
  if (leaderboardMetric.value === 'winRate') {
    value = bot.winRate
  } else {
    value = bot.profit > 0 ? bot.profit : 0 // Don't show negative bars for now
  }
  
  // Ensure a minimum width for visibility if value > 0
  if (value > 0) {
    const percentage = (value / max) * 100
    return Math.max(percentage, 5) 
  }
  return 0
}

const formatMetricValue = (bot) => {
  if (leaderboardMetric.value === 'winRate') {
    return `${bot.winRate.toFixed(1)}%`
  } else {
    return `$${bot.profit.toFixed(2)}`
  }
}

const formatActiveSince = (dateStr) => {
  if (!dateStr) return '—'
  const d = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
}

const getBotColor = (name) => {
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const hexToRgba = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// Generate historical performance data with more points
const generateHistoricalData = (bot, currentValue) => {
  const days = 60 // More data points for smoother chart
  const data = []
  const baseValue = currentValue * 0.65 // Start from 65% of current value
  const volatility = currentValue * 0.12 // 12% volatility
  
  // Add some variation to make it more interesting
  const trendType = bot.id % 3 // Different trend types
  let trendMultiplier = 1
  
  for (let i = 0; i <= days; i++) {
    const progress = i / days
    
    // Different trend patterns
    if (trendType === 0) {
      // Steady growth
      trendMultiplier = 0.65 + (progress * 0.35)
    } else if (trendType === 1) {
      // Slow start, fast finish
      trendMultiplier = 0.65 + (Math.pow(progress, 0.7) * 0.35)
    } else {
      // Fast start, steady finish
      trendMultiplier = 0.65 + (Math.pow(progress, 1.3) * 0.35)
    }
    
    const trend = baseValue + (currentValue - baseValue) * trendMultiplier
    const random = (Math.random() - 0.5) * volatility * (1 - progress * 0.5) // Less volatility near end
    const value = Math.max(0, trend + random)
    
    const date = new Date()
    date.setDate(date.getDate() - (days - i))
    
    data.push({
      time: Math.floor(date.getTime() / 1000),
      value: leaderboardMetric.value === 'winRate' ? Math.min(100, value) : value
    })
  }
  
  return data
}

// Initialize chart
const initChart = async () => {
  if (!chartContainer.value || leaderboardBots.value.length === 0) {
    return
  }
  
  // Prevent multiple simultaneous initializations
  if (isInitializing) {
    return
  }
  
  isInitializing = true
  
  try {
    // Clean up existing chart completely
    if (chart) {
      try {
        chart.remove()
      } catch (e) {
        console.warn('Error removing chart:', e)
      }
      chart = null
    }
    seriesMap.clear()
    
    // Clear container and overlay
    if (chartContainer.value) {
      while (chartContainer.value.firstChild) {
        chartContainer.value.removeChild(chartContainer.value.firstChild)
      }
    }
    if (chartOverlay.value) {
      chartOverlay.value.innerHTML = ''
    }
    lastPointByBotId.clear()
    avatarOverlayUpdater = null
    
    await nextTick()
    
    // Ensure container still exists and is visible
    if (!chartContainer.value) {
      isInitializing = false
      return
    }
    
    // Check if container is visible (has dimensions)
    const rect = chartContainer.value.getBoundingClientRect()
    if (rect.width === 0 || rect.height === 0) {
      // Container not visible yet, retry after a short delay
      setTimeout(() => {
        isInitializing = false
        if (leaderboardBots.value.length > 0) {
          initChart()
        }
      }, 100)
      return
    }
    
    // Force container to have dimensions
    const containerWidth = rect.width || chartContainer.value.clientWidth || chartContainer.value.offsetWidth || 800
    const containerHeight = rect.height || 300
    
    if (containerWidth === 0 || containerHeight === 0) {
      isInitializing = false
      return
    }
    
    // Create chart
    chart = createChart(chartContainer.value, {
      width: containerWidth,
      height: containerHeight,
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: '#a0aec0',
      },
      grid: {
        vertLines: { color: 'rgba(45, 55, 72, 0.5)' },
        horzLines: { color: 'rgba(45, 55, 72, 0.5)' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#2d3748',
      },
      rightPriceScale: {
        borderColor: '#2d3748',
        scaleMargins: {
          top: 0.2, // More space at top
          bottom: 0.1,
        },
      },
      handleScroll: false,
      handleScale: false,
      localization: {
        priceFormatter: (price) => {
          if (leaderboardMetric.value === 'winRate') {
            return `${price.toFixed(1)}%`
          } else {
            return `$${price.toFixed(2)}`
          }
        },
      },
    })
  
  // Add series for each bot
  leaderboardBots.value.forEach((bot, index) => {
    const currentValue = leaderboardMetric.value === 'winRate' ? bot.winRate : bot.profit
    const historicalData = generateHistoricalData(bot, currentValue)
    
    const color = getBotColor(bot.name)
    const series = chart.addAreaSeries({
      lineColor: color,
      topColor: hexToRgba(color, 0.4),
      bottomColor: hexToRgba(color, 0.0),
      lineWidth: 2,
      title: '', // no text label on chart - icon (marker) only; name is in legend
      priceFormat: {
        type: 'price',
        precision: leaderboardMetric.value === 'winRate' ? 1 : 2,
        minMove: leaderboardMetric.value === 'winRate' ? 0.1 : 0.01,
      },
      lastValueVisible: false,
      priceLineVisible: false,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 5,
    })
    
    const lastPoint = historicalData[historicalData.length - 1]
    lastPointByBotId.set(bot.id, { time: lastPoint.time, value: lastPoint.value })

    // Only midpoint marker; last point shows round image overlay instead
    const markers = []
    const midPoint = historicalData[Math.floor(historicalData.length / 2)]
    markers.push({
      time: midPoint.time,
      position: 'inBar',
      color: color,
      shape: 'circle',
      size: 0.6,
    })

    series.setData(historicalData)
    series.setMarkers(markers)
    seriesMap.set(bot.id, series)
  })

  chart.timeScale().fitContent()

  const updateAvatarOverlay = () => {
    if (!chartOverlay.value || !chart) return
    chartOverlay.value.innerHTML = ''
    const w = chartContainer.value?.offsetWidth || 0
    const h = chartContainer.value?.offsetHeight || 0
    if (w === 0 || h === 0) return
    chartOverlay.value.style.width = w + 'px'
    chartOverlay.value.style.height = h + 'px'
    const size = 28
    const half = size / 2
    leaderboardBots.value.forEach((bot) => {
      const last = lastPointByBotId.get(bot.id)
      const series = seriesMap.get(bot.id)
      if (!last || !series) return
      const x = chart.timeScale().timeToCoordinate(last.time)
      const y = series.priceToCoordinate(last.value)
      if (x == null || y == null) return
      const img = document.createElement('img')
      img.src = botIconUrl
      img.alt = bot.name
      img.className = 'chart-bot-avatar'
      img.style.cssText = `position:absolute;left:${x - half}px;top:${y - half}px;width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;border:2px solid ${getBotColor(bot.name)};pointer-events:none;`
      chartOverlay.value.appendChild(img)
    })
  }

  await nextTick()
  updateAvatarOverlay()
  chart.timeScale().subscribeVisibleTimeRangeChange(updateAvatarOverlay)
  avatarOverlayUpdater = updateAvatarOverlay
  } finally {
    isInitializing = false
  }
}

// Watch for metric changes - debounced to avoid multiple calls
let chartUpdateTimeout = null
watch([leaderboardMetric, leaderboardBots], () => {
  if (chartUpdateTimeout) {
    clearTimeout(chartUpdateTimeout)
  }
  chartUpdateTimeout = setTimeout(() => {
    if (leaderboardBots.value.length > 0 && chartContainer.value) {
      initChart()
    }
  }, 100)
}, { deep: true })

// Watch for bots changes
watch(() => bots.value.length, () => {
  if (chartUpdateTimeout) {
    clearTimeout(chartUpdateTimeout)
  }
  chartUpdateTimeout = setTimeout(() => {
    if (bots.value.length > 0 && chartContainer.value) {
      nextTick(() => {
        initChart()
      })
    }
  }, 100)
})

const handleConfigureBot = (bot) => {
  selectedBot.value = bot
  showConfigModal.value = true
}

const handleImportBot = (bot) => {
  importTargetBot.value = bot
  showImportModal.value = true
}

const handleDeactivateBot = async (bot) => {
  try {
    await api.deactivateBot(bot.id)
    await loadBots() // Reload bots to update status
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to deactivate bot'
  }
}

const handleActivateBot = async (bot) => {
  try {
    await api.activateBot(bot.id)
    await loadBots() // Reload bots to update status
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to activate bot'
  }
}

const handleConfigSaved = () => {
  loadBots() // Reload bots after config is saved
}

const handleBotCreated = () => {
  console.log('Bot created, reloading bots...')
  // Small delay to ensure the backend has committed the transaction
  setTimeout(() => {
    loadBots()
  }, 300)
}

const handleExportBot = async (bot) => {
  try {
    const response = await api.exportBot(bot.id)
    const exportData = response.data
    
    // Create a blob and download it
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `bot_${bot.name.replace(/\s+/g, '_')}_${Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to export bot'
    console.error('Error exporting bot:', err)
  }
}

const handleBotImported = () => {
  console.log('Bot imported, reloading bots...')
  setTimeout(() => {
    loadBots()
  }, 300)
}

const loadBots = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await api.getBots()
    console.log('Bots API response:', response.data)
    
    if (response.data && response.data.bots) {
      bots.value = response.data.bots.map(bot => ({
        ...bot,
        winRate: parseFloat(bot.win_rate) || 0,
        totalTrades: parseInt(bot.total_trades) || 0,
        profit: parseFloat(bot.profit) || 0,
        owner: bot.owner || bot.user?.username || 'You',
        status: bot.status || 'inactive',
        description: bot.description || '',
        activatedAt: bot.activated_at || null
      }))
      console.log('Bots loaded:', bots.value.length)
    } else {
      console.warn('Unexpected response format:', response.data)
      bots.value = []
    }
  } catch (err) {
    console.error('Error loading bots:', err)
    error.value = err.response?.data?.detail || err.message || 'Failed to load bots'
    bots.value = []
  } finally {
    loading.value = false
  }
}

// Handle window resize - debounced
let resizeTimeout = null
const handleResize = () => {
  if (resizeTimeout) {
    clearTimeout(resizeTimeout)
  }
  resizeTimeout = setTimeout(() => {
    if (chart && chartContainer.value) {
      const newWidth = chartContainer.value.clientWidth || chartContainer.value.offsetWidth
      const newHeight = chartContainer.value.clientHeight || chartContainer.value.offsetHeight
      if (newWidth > 0 && newHeight > 0) {
        chart.applyOptions({ width: newWidth, height: newHeight })
      }
      avatarOverlayUpdater?.()
    }
  }, 150)
}

onMounted(async () => {
  await loadBots()
  await nextTick()
  
  // Wait a bit more to ensure DOM is fully ready
  setTimeout(() => {
    if (bots.value.length > 0 && chartContainer.value) {
      initChart()
    }
  }, 200)
  
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartUpdateTimeout) {
    clearTimeout(chartUpdateTimeout)
  }
  if (resizeTimeout) {
    clearTimeout(resizeTimeout)
  }
  if (chart) {
    chart.remove()
    chart = null
  }
  seriesMap.clear()
  isInitializing = false
})
</script>

<style scoped>
.bot-list-container {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

/* Leaderboard Styles */
.leaderboard-section {
  background: #1a202c;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
  border: 1px solid #2d3748;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.performance-chart-container {
  margin-bottom: 24px;
  background: #0f1419;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #2d3748;
}

.chart-and-overlay {
  position: relative;
  width: 100%;
  height: 300px;
  margin-bottom: 16px;
}

.chart-wrapper {
  width: 100%;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
  overflow: hidden;
}

.chart-avatar-overlay {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: visible;
  min-height: 300px;
}

.chart-wrapper :deep(.tv-lightweight-charts) {
  width: 100% !important;
  height: 100% !important;
}

.chart-wrapper :deep(canvas) {
  display: block !important;
}

.chart-legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #2d3748;
}

.legend-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #1a202c;
  border-radius: 10px;
  border: 1px solid #2d3748;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.legend-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: var(--bot-color);
  opacity: 0;
  transition: opacity 0.3s;
}

.legend-item:hover {
  background: #2d3748;
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
  border-color: var(--bot-color);
}

.legend-item:hover::before {
  opacity: 1;
}

.legend-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.legend-color {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--bot-color);
  box-shadow: 0 0 10px var(--bot-color);
}

.legend-bot-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 2px solid var(--bot-color, #805ad5);
}

.legend-bot-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.legend-content {
  flex: 1;
  min-width: 0;
}

.legend-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.legend-name {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.legend-rank {
  font-size: 11px;
  color: #718096;
  font-weight: 700;
  background: #2d3748;
  padding: 2px 6px;
  border-radius: 4px;
}

.legend-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.legend-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.stat-label {
  color: #718096;
  font-weight: 500;
}

.stat-value {
  color: #e2e8f0;
  font-weight: 700;
}

.stat-value.status {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  font-weight: 600;
}

.stat-value.status.active {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.stat-value.status.inactive {
  background: rgba(113, 128, 150, 0.2);
  color: #718096;
}

.legend-active-since .stat-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.start-flag-icon {
  font-size: 14px;
  line-height: 1;
}

.leaderboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.leaderboard-header h3 {
  margin: 0;
  font-size: 18px;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-toggles {
  display: flex;
  background: #2d3748;
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.metric-toggles button {
  background: transparent;
  border: none;
  color: #a0aec0;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.metric-toggles button.active {
  background: #4a5568;
  color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.leaderboard-graph {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.graph-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.rank {
  font-size: 14px;
  font-weight: 700;
  color: #718096;
  width: 20px;
  text-align: center;
}

.graph-row:nth-child(1) .rank { color: #fbbf24; } /* Gold */
.graph-row:nth-child(2) .rank { color: #94a3b8; } /* Silver */
.graph-row:nth-child(3) .rank { color: #b45309; } /* Bronze */

.bot-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 180px;
  max-width: 220px;
  flex-shrink: 0;
}

.bot-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 2px solid var(--bot-color, #805ad5);
}

.bot-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.bot-name {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-container {
  flex: 1;
  min-width: 80px;
  height: 28px;
  background: linear-gradient(180deg, #1e2530 0%, #252d3a 100%);
  border: 1px solid #3d4a5c;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.bar {
  height: 100%;
  border-radius: 6px;
  position: relative;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 0;
}

.bar.winRate {
  background: linear-gradient(90deg, #2563eb 0%, #3b82f6 50%, #60a5fa 100%);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
}

.bar.profit {
  background: linear-gradient(90deg, #059669 0%, #10b981 50%, #34d399 100%);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}

.bar.empty {
  width: 0 !important;
  min-width: 0 !important;
}

.bar-empty-hint {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  white-space: nowrap;
  pointer-events: none;
  letter-spacing: 0.5px;
}

.bar-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
  transform: skewX(-20deg) translateX(-150%);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  100% { transform: skewX(-20deg) translateX(150%); }
}

.metric-value {
  min-width: 72px;
  text-align: right;
  font-weight: 700;
  color: #e2e8f0;
  font-size: 14px;
  letter-spacing: 0.3px;
}

.section-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #2d3748, transparent);
  margin: 0 0 32px 0;
}

.loading, .error, .no-bots {
  text-align: center;
  padding: 60px 20px;
  color: #a0aec0;
}

.error {
  color: #fc8181;
}

.no-bots {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.bots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .bot-list-container {
    padding: 16px;
    padding-bottom: max(16px, env(safe-area-inset-bottom));
  }

  .leaderboard-section {
    padding: 16px;
    margin-bottom: 24px;
  }

  .leaderboard-header {
    flex-wrap: wrap;
    gap: 12px;
  }

  .leaderboard-header h3 {
    font-size: 16px;
  }

  .metric-toggles {
    width: 100%;
  }

  .metric-toggles button {
    flex: 1;
    min-height: 40px;
  }

  .performance-chart-container {
    padding: 12px;
  }

  .chart-and-overlay {
    height: 220px;
  }

  .chart-avatar-overlay {
    min-height: 220px;
  }

  .chart-legend {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .legend-item {
    padding: 10px;
  }

  .graph-row {
    flex-wrap: wrap;
  }

  .bots-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .bot-info {
    min-width: 100px;
    max-width: 140px;
  }

  .metric-value {
    min-width: 52px;
    font-size: 12px;
  }

  .bar-container {
    min-width: 56px;
  }
}

@media (max-width: 480px) {
  .bot-list-container {
    padding: 12px;
  }

  .leaderboard-section {
    padding: 12px;
  }

  .chart-and-overlay {
    height: 180px;
  }

  .chart-avatar-overlay {
    min-height: 180px;
  }
}
</style>

