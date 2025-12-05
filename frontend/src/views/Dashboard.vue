<template>
  <div class="dashboard">
    <!-- Top Tab Bar -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="setActiveTab(tab.id)"
      >
        {{ tab.name }}
      </button>
      <button class="add-tab-btn" @click="addNewTab">+</button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Earnings Tab -->
      <div
        v-if="activeTab === 2"
        class="tab-panel earnings-panel"
      >
        <EarningsList @ticker-selected="(symbol) => handleEarningsTickerSelect(symbol)" />
      </div>

      <!-- News Tab -->
      <div
        v-if="activeTab === 3"
        class="tab-panel news-panel"
      >
        <NewsFeed />
      </div>

      <!-- Bot Tab -->
      <div
        v-if="activeTab === 4"
        class="tab-panel bot-panel"
      >
        <BotList 
          @view-bot="handleViewBot"
          @compete="handleCompete"
          @create-bot="handleCreateBot"
        />
      </div>

      <!-- Stocks Tab -->
      <div
        v-for="tab in tabs"
        :key="tab.id"
        v-show="activeTab === tab.id && tab && tab.type === 'stocks'"
        class="tab-panel"
      >
        <!-- Chart Info Bar (Editable) -->
        <div v-if="tab && tab.chartInfo" class="chart-info-bar">
          <div class="info-item">
            <label>Symbol:</label>
            <input
              v-model="tab.chartInfo.symbol"
              @change="updateChartInfo(tab.id)"
              class="editable-input"
              placeholder="Enter symbol"
            />
          </div>
          <div class="info-item">
            <label>Name:</label>
            <input
              v-model="tab.chartInfo.name"
              @change="updateChartInfo(tab.id)"
              class="editable-input"
              placeholder="Enter name"
            />
          </div>
          <div class="info-item">
            <label>Price:</label>
            <span class="info-value">{{ tab.chartInfo.price || '--' }}</span>
          </div>
          <div class="info-item">
            <label>Change:</label>
            <span :class="['info-value', { positive: tab.chartInfo.change > 0, negative: tab.chartInfo.change < 0 }]">
              {{ tab.chartInfo.change ? (tab.chartInfo.change > 0 ? '+' : '') + tab.chartInfo.change.toFixed(2) : '--' }}
            </span>
          </div>
          <div class="info-item">
            <label>Change %:</label>
            <span :class="['info-value', { positive: tab.chartInfo.changePercent > 0, negative: tab.chartInfo.changePercent < 0 }]">
              {{ tab.chartInfo.changePercent ? (tab.chartInfo.changePercent > 0 ? '+' : '') + tab.chartInfo.changePercent.toFixed(2) + '%' : '--' }}
            </span>
          </div>
          <div class="info-item">
            <label>Volume:</label>
            <span class="info-value">{{ formatVolume(tab.chartInfo.volume) }}</span>
          </div>
        </div>

        <!-- Chart Toolbar -->
        <div v-if="tab" class="chart-toolbar">
          <div class="timeframe-buttons">
            <button
              v-for="tf in timeframes"
              :key="tf"
              :class="['timeframe-btn', { active: tab.timeframe === tf }]"
              @click="setTimeframe(tab.id, tf)"
            >
              {{ tf }}
            </button>
          </div>
          
          <div class="chart-type-buttons">
            <button
              v-for="type in chartTypes"
              :key="type"
              :class="['chart-type-btn', { active: tab.chartType === type }]"
              @click="setChartType(tab.id, type)"
            >
              {{ type }}
            </button>
          </div>

          <div class="toolbar-actions">
            <button
              v-for="mode in viewModes"
              :key="mode.id"
              :class="['view-mode-btn', { active: tab.viewMode === mode.id }]"
              @click="setViewMode(tab.id, mode.id)"
              :title="mode.name"
            >
              {{ mode.icon }}
            </button>
            <button class="settings-btn" @click="showSettings = true">⚙️</button>
          </div>
        </div>

        <!-- Main Content Area -->
        <div v-if="tab" class="main-content">
          <!-- Left Panel: Watchlist -->
          <div class="left-panel" v-if="tab.viewMode !== 3">
            <div class="search-section">
              <input
                v-model="searchQuery"
                @input="handleSearch"
                placeholder="Search to add to watchlist..."
                class="search-input"
              />
              <button @click="addTopResult" class="add-btn">✓</button>
            </div>
            
            <div v-if="searchResults.length > 0" class="search-results">
              <div
                v-for="result in searchResults"
                :key="result.symbol"
                @click="addToWatchlist(result, tab.id)"
                class="search-result-item"
              >
                {{ result.symbol }} - {{ result.name }}
              </div>
            </div>

            <h3 class="panel-title">My Watchlist</h3>
            <div class="watchlist">
              <div
                v-for="item in watchlist"
                :key="item.symbol"
                :class="['watchlist-item', { active: tab.selectedTicker === item.symbol }]"
                @click="selectTicker(tab.id, item.symbol)"
              >
                <div class="symbol">{{ item.symbol }}</div>
                <div class="name">{{ item.name }}</div>
              </div>
            </div>
            <button @click="removeSelected(tab.id)" class="remove-btn">🗑️ Remove</button>
          </div>

          <!-- Center: Chart -->
          <div class="chart-container">
            <div v-if="!tab.selectedTicker" class="welcome-screen">
              <h1>Portfolio Tracker</h1>
              <p>Add an asset from the search bar to begin.</p>
            </div>
            <div v-else :ref="el => setChartRef(tab.id, el)" class="chart-wrapper"></div>
          </div>

          <!-- Right Panel: News (View Mode 2) -->
          <div class="right-panel" v-if="tab.viewMode === 2">
            <h3 class="panel-title">Feed Notizie</h3>
            <div class="news-feed">
              <NewsCard
                v-for="newsItem in newsItems"
                :key="newsItem.link"
                :news-item="newsItem"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Flyout News Panel (View Mode 3) -->
    <FlyoutNewsPanel
      v-for="tab in tabs"
      :key="`flyout-${tab.id}`"
      v-if="tab && tab.viewMode === 3 && activeTab === tab.id"
      :news-items="filteredNews"
      @view-toggle="(mode) => setViewMode(tab.id, mode)"
    />

    <!-- Settings Modal -->
    <SettingsModal
      v-if="showSettings"
      @close="showSettings = false"
      @save="handleSettingsSave"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { createChart } from 'lightweight-charts'
import { useWatchlistStore } from '../stores/watchlist'
import { useNewsStore } from '../stores/news'
import NewsCard from '../components/NewsCard.vue'
import FlyoutNewsPanel from '../components/FlyoutNewsPanel.vue'
import SettingsModal from '../components/SettingsModal.vue'
import EarningsList from '../components/EarningsList.vue'
import NewsFeed from '../components/NewsFeed.vue'
import BotList from '../components/BotList.vue'
import api from '../services/api'

const watchlistStore = useWatchlistStore()
const newsStore = useNewsStore()

const timeframes = ['1d', '5d', '1m', '3m', '6m', '1y', '5y']
const chartTypes = ['Candle', 'Line']
const viewModes = [
  { id: 1, name: 'Chart Only', icon: '📊' },
  { id: 2, name: 'Chart + News', icon: '📰' },
  { id: 3, name: 'Chart + Flyout', icon: '🔔' }
]

const activeTab = ref(1)
const tabs = ref([
  {
    id: 1,
    name: 'Stocks',
    type: 'stocks',
    selectedTicker: null,
    timeframe: '1y',
    chartType: 'Candle',
    viewMode: 1,
    chartInfo: {
      symbol: '',
      name: '',
      price: null,
      change: null,
      changePercent: null,
      volume: null
    },
    chart: null,
    candlestickSeries: null,
    lineSeries: null
  },
  {
    id: 2,
    name: 'Earnings',
    type: 'earnings'
  },
  {
    id: 3,
    name: 'News',
    type: 'news'
  },
  {
    id: 4,
    name: 'Bot',
    type: 'bot'
  }
])

const searchQuery = ref('')
const searchResults = ref([])
const showSettings = ref(false)
const chartRefs = ref({})

const watchlist = computed(() => watchlistStore.watchlist)
const newsItems = computed(() => newsStore.news)
const filteredNews = computed(() => {
  const currentTab = tabs.value.find(t => t && t.id === activeTab.value)
  if (currentTab && currentTab.viewMode === 3) {
    return newsItems.value.filter(item => 
      watchlist.value.some(w => w.symbol === item.ticker)
    )
  }
  return newsItems.value
})

const setChartRef = (tabId, el) => {
  if (el) {
    chartRefs.value[tabId] = el
  }
}

onMounted(async () => {
  await watchlistStore.loadWatchlist()
  await newsStore.loadNews()
  if (watchlist.value.length > 0) {
    const firstTab = tabs.value[0]
    selectTicker(firstTab.id, watchlist.value[0].symbol)
  }
})

const setActiveTab = (tabId) => {
  activeTab.value = tabId
  const tab = tabs.value.find(t => t.id === tabId)
  if (tab && tab.selectedTicker) {
    nextTick(() => {
      loadChart(tabId)
    })
  }
}

const addNewTab = () => {
  const newId = Math.max(...tabs.value.map(t => t.id)) + 1
  tabs.value.push({
    id: newId,
    name: `Tab ${newId}`,
    type: 'stocks',
    selectedTicker: null,
    timeframe: '1y',
    chartType: 'Candle',
    viewMode: 1,
    chartInfo: {
      symbol: '',
      name: '',
      price: null,
      change: null,
      changePercent: null,
      volume: null
    },
    chart: null,
    candlestickSeries: null,
    lineSeries: null,
    earningsLines: []
  })
  activeTab.value = newId
}

const handleEarningsTickerSelect = (symbol) => {
  // Switch to Stocks tab and select the ticker
  const stocksTab = tabs.value.find(t => t.type === 'stocks')
  if (stocksTab) {
    activeTab.value = stocksTab.id
    nextTick(() => {
      selectTicker(stocksTab.id, symbol)
    })
  }
}

const handleViewBot = (bot) => {
  console.log('View bot:', bot)
  // TODO: Implement bot details view
  alert(`Viewing details for ${bot.name}`)
}

const handleCompete = (bot) => {
  console.log('Compete with bot:', bot)
  // TODO: Implement competition feature
  alert(`Starting competition with ${bot.name}`)
}

const handleCreateBot = () => {
  console.log('Create new bot')
  // TODO: Implement bot creation
  alert('Bot creation feature coming soon!')
}

const setTimeframe = (tabId, tf) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    tab.timeframe = tf
    if (tab.selectedTicker) {
      loadChart(tabId)
    }
  }
}

const setChartType = (tabId, type) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    tab.chartType = type
    if (tab.selectedTicker) {
      loadChart(tabId)
    }
  }
}

const setViewMode = (tabId, mode) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    tab.viewMode = mode
  }
}

const updateChartInfo = async (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab || !tab.chartInfo || !tab.chartInfo.symbol) return

  try {
    const response = await api.getQuote(tab.chartInfo.symbol)
    const quote = response.data
    tab.chartInfo.name = quote.name || tab.chartInfo.name
    tab.chartInfo.price = quote.price
    tab.chartInfo.change = quote.change
    tab.chartInfo.changePercent = quote.changePercent
    tab.chartInfo.volume = quote.volume

    // If symbol changed and matches a ticker, load chart
    if (tab.chartInfo.symbol && tab.chartInfo.symbol === tab.selectedTicker) {
      selectTicker(tabId, tab.chartInfo.symbol)
    }
  } catch (error) {
    console.error('Failed to update chart info:', error)
  }
}

const handleSearch = async () => {
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }
  
  try {
    const response = await api.search(searchQuery.value)
    searchResults.value = response.data.results || []
  } catch (error) {
    console.error('Search error:', error)
  }
}

const addTopResult = () => {
  if (searchResults.value.length > 0) {
    const currentTab = tabs.value.find(t => t.id === activeTab.value)
    addToWatchlist(searchResults.value[0], currentTab.id)
  }
}

const addToWatchlist = async (item, tabId) => {
  await watchlistStore.addItem(item.symbol, item.name)
  searchQuery.value = ''
  searchResults.value = []
  selectTicker(tabId, item.symbol)
}

const removeSelected = async (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab && tab.selectedTicker) {
    await watchlistStore.removeItem(tab.selectedTicker)
    tab.selectedTicker = null
    tab.chartInfo = {
      symbol: '',
      name: '',
      price: null,
      change: null,
      changePercent: null,
      volume: null
    }
    if (tab.chart) {
      tab.chart.remove()
      tab.chart = null
    }
    
    if (watchlist.value.length > 0) {
      selectTicker(tabId, watchlist.value[0].symbol)
    }
  }
}

const selectTicker = async (tabId, symbol) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    tab.selectedTicker = symbol
    tab.chartInfo.symbol = symbol
    
    // Get quote info
    try {
      const response = await api.getQuote(symbol)
      const quote = response.data
      tab.chartInfo.name = quote.name
      tab.chartInfo.price = quote.price
      tab.chartInfo.change = quote.change
      tab.chartInfo.changePercent = quote.changePercent
      tab.chartInfo.volume = quote.volume
    } catch (error) {
      console.error('Failed to get quote:', error)
    }
    
    await loadChart(tabId)
  }
}

const loadChart = async (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab || !tab.selectedTicker) return

  const chartContainer = chartRefs.value[tabId]
  if (!chartContainer) return

  try {
    const response = await api.getChart({
      ticker: tab.selectedTicker,
      timeframe: tab.timeframe,
      chart_type: tab.chartType.toLowerCase()
    })

    await nextTick()

    if (tab.chart) {
      // Remove earnings lines if they exist
      if (tab.earningsLines && tab.earningsLines.length > 0) {
        tab.earningsLines.forEach(line => {
          try {
            tab.chart.removeSeries(line)
          } catch (e) {
            // Series might already be removed
          }
        })
        tab.earningsLines = []
      }
      tab.chart.remove()
    }

    tab.chart = createChart(chartContainer, {
      width: chartContainer.clientWidth,
      height: chartContainer.clientHeight,
      layout: {
        background: { color: '#1e1e1e' },
        textColor: '#dcdcdc',
      },
      grid: {
        vertLines: { color: '#333' },
        horzLines: { color: '#333' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    })

    const data = response.data.data
    const earningsDates = response.data.earnings_dates || []
    
    // Debug: log earnings dates
    if (earningsDates.length > 0) {
      console.log(`Found ${earningsDates.length} earnings dates for ${tab.selectedTicker}:`, earningsDates)
    } else {
      console.log(`No earnings dates found for ${tab.selectedTicker}`)
    }

    if (tab.chartType === 'Candle') {
      tab.candlestickSeries = tab.chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      })
      tab.candlestickSeries.setData(data.map(d => ({
        time: d.time / 1000,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      })))
      
      // Add earnings markers
      if (earningsDates.length > 0) {
        const markers = earningsDates.map(earning => {
          // Find the closest data point to the earnings date
          const earningsTime = earning.timestamp / 1000
          let closestDataPoint = data[0]
          let minDiff = Math.abs(data[0].time / 1000 - earningsTime)
          
          for (const point of data) {
            const diff = Math.abs(point.time / 1000 - earningsTime)
            if (diff < minDiff) {
              minDiff = diff
              closestDataPoint = point
            }
          }
          
          return {
            time: closestDataPoint.time / 1000,
            position: 'aboveBar',
            color: '#ff9800',
            shape: 'arrowDown',
            size: 3,
            text: 'E',
          }
        })
        
        tab.candlestickSeries.setMarkers(markers)
      }
    } else {
      tab.lineSeries = tab.chart.addLineSeries({
        color: '#2196F3',
        lineWidth: 2,
      })
      tab.lineSeries.setData(data.map(d => ({
        time: d.time / 1000,
        value: d.close,
      })))
      
      // Add earnings markers
      if (earningsDates.length > 0) {
        const markers = earningsDates.map(earning => {
          // Find the closest data point to the earnings date
          const earningsTime = earning.timestamp / 1000
          let closestDataPoint = data[0]
          let minDiff = Math.abs(data[0].time / 1000 - earningsTime)
          
          for (const point of data) {
            const diff = Math.abs(point.time / 1000 - earningsTime)
            if (diff < minDiff) {
              minDiff = diff
              closestDataPoint = point
            }
          }
          
          return {
            time: closestDataPoint.time / 1000,
            position: 'aboveBar',
            color: '#ff9800',
            shape: 'arrowDown',
            size: 3,
            text: 'E',
          }
        })
        
        tab.lineSeries.setMarkers(markers)
      }
    }

    // Add vertical lines for earnings using a separate series
    // Note: Lightweight-charts doesn't support true vertical lines directly
    // We create a line series with many points close together to simulate a vertical line
    if (earningsDates.length > 0 && data.length > 0) {
      // Find min and max prices in the dataset
      const allPrices = data.flatMap(d => [d.high, d.low, d.close, d.open].filter(p => p != null))
      const minPrice = Math.min(...allPrices)
      const maxPrice = Math.max(...allPrices)
      const pricePadding = (maxPrice - minPrice) * 0.02 // 2% padding
      
      // Create vertical lines using a line series
      earningsDates.forEach(earning => {
        const earningsTime = earning.timestamp / 1000
        
        // Find the closest data point to the earnings date
        let closestDataPoint = data[0]
        let minDiff = Math.abs(data[0].time / 1000 - earningsTime)
        
        for (const point of data) {
          const diff = Math.abs(point.time / 1000 - earningsTime)
          if (diff < minDiff) {
            minDiff = diff
            closestDataPoint = point
          }
        }
        
        const earningsTimestamp = closestDataPoint.time / 1000
        
        // Create a vertical line using a line series
        // We use many points with very small time increments to create a vertical line
        const verticalLineSeries = tab.chart.addLineSeries({
          color: '#ff9800',
          lineWidth: 3,
          lineStyle: 0, // Solid
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
          pointMarkersVisible: false,
        })
        
        // Create points for vertical line: from min to max price with same timestamp
        // We use a small time increment to ensure points are ordered correctly
        const verticalPoints = []
        const numPoints = 200 // More points = smoother line
        const timeIncrement = 0.000001 // Very small increment (1 microsecond)
        
        for (let i = 0; i < numPoints; i++) {
          const price = (minPrice - pricePadding) + (maxPrice - minPrice + pricePadding * 2) * (i / (numPoints - 1))
          verticalPoints.push({
            time: earningsTimestamp + (i * timeIncrement),
            value: price,
          })
        }
        
        verticalLineSeries.setData(verticalPoints)
        
        // Store reference to remove later if needed
        if (!tab.earningsLines) {
          tab.earningsLines = []
        }
        tab.earningsLines.push(verticalLineSeries)
      })
    }

    tab.chart.timeScale().fitContent()
  } catch (error) {
    console.error('Chart load error:', error)
  }
}

const formatVolume = (volume) => {
  if (!volume) return '--'
  if (volume >= 1e9) return (volume / 1e9).toFixed(2) + 'B'
  if (volume >= 1e6) return (volume / 1e6).toFixed(2) + 'M'
  if (volume >= 1e3) return (volume / 1e3).toFixed(2) + 'K'
  return volume.toString()
}

const handleSettingsSave = (settings) => {
  // Save settings to localStorage
  if (settings.newsTickers) {
    localStorage.setItem('newsTickers', JSON.stringify(settings.newsTickers))
  }
  if (settings.selectedPublishers) {
    localStorage.setItem('selectedPublishers', JSON.stringify(settings.selectedPublishers))
  }
  
  showSettings.value = false
  
  // Note: NewsFeed component will automatically reload when settings change
  // because it reads from localStorage on each load
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #1e1e1e;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 10px;
  background-color: #2d2d2d;
  border-bottom: 1px solid #444;
}

.tab-btn {
  padding: 8px 16px;
  background-color: #3c3c3c;
  border: 1px solid #555;
  border-radius: 6px 6px 0 0;
  color: #dcdcdc;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.tab-btn:hover {
  background-color: #4a4a4a;
}

.tab-btn.active {
  background-color: #1e1e1e;
  border-bottom-color: #1e1e1e;
  color: #fff;
}

.add-tab-btn {
  padding: 8px 12px;
  background-color: #3c3c3c;
  border: 1px solid #555;
  border-radius: 6px;
  color: #dcdcdc;
  cursor: pointer;
  font-size: 18px;
  margin-left: 10px;
}

.add-tab-btn:hover {
  background-color: #4a4a4a;
}

.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tab-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Chart Info Bar (Editable) */
.chart-info-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 20px;
  background-color: #252525;
  border-bottom: 1px solid #444;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item label {
  font-size: 13px;
  color: #888;
  font-weight: 500;
}

.editable-input {
  padding: 4px 8px;
  background-color: #1e1e1e;
  border: 1px solid #444;
  border-radius: 4px;
  color: #dcdcdc;
  font-size: 13px;
  min-width: 100px;
}

.editable-input:focus {
  border-color: #007acc;
  outline: none;
}

.info-value {
  font-size: 13px;
  color: #dcdcdc;
  font-weight: 500;
  min-width: 60px;
}

.info-value.positive {
  color: #26a69a;
}

.info-value.negative {
  color: #ef5350;
}

/* Chart Toolbar */
.chart-toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 20px;
  background-color: #2d2d2d;
  border-bottom: 1px solid #444;
}

.timeframe-buttons, .chart-type-buttons {
  display: flex;
  gap: 5px;
}

.timeframe-btn, .chart-type-btn {
  padding: 6px 12px;
  background-color: #3c3c3c;
  border: 1px solid #555;
  border-radius: 4px;
  color: #dcdcdc;
  cursor: pointer;
  font-size: 13px;
}

.timeframe-btn:hover, .chart-type-btn:hover {
  background-color: #4a4a4a;
}

.timeframe-btn.active, .chart-type-btn.active {
  background-color: #007acc;
  color: #fff;
  border-color: #007acc;
}

.toolbar-actions {
  display: flex;
  gap: 5px;
  margin-left: auto;
}

.view-mode-btn, .settings-btn {
  padding: 6px 10px;
  background-color: #3c3c3c;
  border: 1px solid #555;
  border-radius: 4px;
  color: #dcdcdc;
  cursor: pointer;
  font-size: 14px;
}

.view-mode-btn:hover, .settings-btn:hover {
  background-color: #4a4a4a;
}

.view-mode-btn.active {
  background-color: #007acc;
  color: #fff;
  border-color: #007acc;
}

.earnings-panel, .news-panel, .bot-panel {
  height: 100%;
  overflow: hidden;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 300px;
  background-color: #2d2d2d;
  border-right: 1px solid #444;
  display: flex;
  flex-direction: column;
  padding: 10px;
  overflow-y: auto;
}

.search-section {
  display: flex;
  gap: 5px;
  margin-bottom: 10px;
}

.search-input {
  flex: 1;
  padding: 8px;
  background-color: #1e1e1e;
  border: 1px solid #444;
  border-radius: 4px;
  color: #dcdcdc;
}

.add-btn {
  padding: 8px 12px;
  background-color: #007acc;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
}

.search-results {
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 10px;
  border: 1px solid #444;
  border-radius: 4px;
  background-color: #1e1e1e;
}

.search-result-item {
  padding: 8px;
  cursor: pointer;
  border-bottom: 1px solid #333;
}

.search-result-item:hover {
  background-color: #3a3a3a;
}

.panel-title {
  padding: 10px 0;
  border-bottom: 1px solid #444;
  margin-bottom: 10px;
  font-size: 16px;
  font-weight: bold;
}

.watchlist {
  flex: 1;
  overflow-y: auto;
}

.watchlist-item {
  padding: 12px;
  cursor: pointer;
  border-radius: 4px;
  margin-bottom: 5px;
  transition: background-color 0.2s;
}

.watchlist-item:hover {
  background-color: #3a3a3a;
}

.watchlist-item.active {
  background-color: #007acc;
  color: #fff;
}

.symbol {
  font-weight: bold;
}

.name {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

.watchlist-item.active .name {
  color: #ccc;
}

.remove-btn {
  padding: 8px;
  background-color: #5a2a27;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  margin-top: 10px;
}

.remove-btn:hover {
  background-color: #7a3a37;
}

.chart-container {
  flex: 1;
  position: relative;
  background-color: #1e1e1e;
}

.chart-wrapper {
  width: 100%;
  height: 100%;
}

.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888;
}

.welcome-screen h1 {
  font-size: 32px;
  margin-bottom: 10px;
  color: #dcdcdc;
}

.right-panel {
  width: 300px;
  background-color: #2d2d2d;
  border-left: 1px solid #444;
  display: flex;
  flex-direction: column;
  padding: 10px;
  overflow-y: auto;
}

.news-feed {
  flex: 1;
  overflow-y: auto;
}
</style>
