<template>
  <div class="dashboard">
    <!-- Top Tab Bar -->
    <div class="tab-bar">
      <div class="tabs-section">
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
      <UserProfile
        :username="currentUser?.username"
        :email="currentUser?.email"
        :is-logged-in="isLoggedIn"
        :profile-picture-url="currentUser?.profile_picture_url"
        @login="showLoginModal = true"
        @register="showRegisterModal = true"
        @logout="handleLogout"
        @profile="handleViewProfile"
        @settings="showSettings = true"
      />
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

      <!-- Flex Chat Tab -->
      <div
        v-if="activeTab === 5"
        class="tab-panel flex-panel"
      >
        <FlexChat />
      </div>

      <!-- Stocks Tab -->
      <div
        v-for="tab in tabs"
        :key="tab.id"
        v-show="activeTab === tab.id && tab && tab.type === 'stocks'"
        class="tab-panel"
      >
        <!-- Chart Info Bar -->
        <div v-if="tab && tab.chartInfo" class="chart-info-bar">
          <div class="info-item">
            <label>Symbol:</label>
            <span class="info-value">{{ tab.chartInfo.symbol || '--' }}</span>
          </div>
          <div class="info-item">
            <label>Name:</label>
            <span class="info-value">{{ tab.chartInfo.name || '--' }}</span>
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
          <div class="info-item price-item">
            <span class="price-value">{{ tab.chartInfo.price ? tab.chartInfo.price.toFixed(2) : '--' }}</span>
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

          <div class="indicators-buttons">
            <button
              :class="['indicator-btn', { active: tab.indicators?.rsi }]"
              @click="toggleIndicator(tab.id, 'rsi')"
              title="RSI (Relative Strength Index)"
            >
              RSI
            </button>
            <button
              :class="['indicator-btn', { active: tab.indicators?.ma13 }]"
              @click="toggleIndicator(tab.id, 'ma13')"
              title="MA 13"
            >
              MA13
            </button>
            <button
              :class="['indicator-btn', { active: tab.indicators?.ma50 }]"
              @click="toggleIndicator(tab.id, 'ma50')"
              title="MA 50"
            >
              MA50
            </button>
            <button
              :class="['indicator-btn', { active: tab.indicators?.ma200 }]"
              @click="toggleIndicator(tab.id, 'ma200')"
              title="MA 200"
            >
              MA200
            </button>
            <button
              :class="['indicator-btn', { active: tab.indicators?.ma800 }]"
              @click="toggleIndicator(tab.id, 'ma800')"
              title="MA 800"
            >
              MA800
            </button>
            <button
              :class="['indicator-btn', { active: tab.indicators?.bullRun }]"
              @click="toggleIndicator(tab.id, 'bullRun')"
              title="Bull/Bear Run Signals"
            >
              🐂🐻
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
                @keyup.enter="addTopResult"
                placeholder="Search to add to watchlist..."
                class="search-input"
              />
              <button 
                @click="addTopResult" 
                class="add-btn"
                :disabled="searchResults.length === 0"
                :title="searchResults.length > 0 ? 'Add first result' : 'No results'"
              >
                ✓
              </button>
            </div>
            
            <div v-if="searchLoading" class="search-loading">
              <span class="loading-spinner">⏳</span> Searching...
            </div>
            
            <div v-else-if="searchQuery.length >= 2 && searchResults.length === 0" class="search-no-results">
              No results found. Try a different search term.
            </div>
            
            <div v-else-if="searchResults.length > 0" class="search-results">
              <div
                v-for="result in searchResults"
                :key="result.symbol"
                @click.stop="handleResultClick(result, tab.id)"
                @mousedown.prevent
                class="search-result-item"
                :title="`Click to add ${result.symbol} to watchlist`"
              >
                <span class="result-symbol">{{ result.symbol }}</span>
                <span class="result-name">- {{ result.name }}</span>
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
    <template v-for="tab in tabs" :key="`flyout-${tab.id}`">
      <FlyoutNewsPanel
        v-if="tab && tab.viewMode === 3 && activeTab === tab.id"
        :news-items="filteredNews"
        @view-toggle="(mode) => setViewMode(tab.id, mode)"
      />
    </template>

    <!-- Settings Modal -->
    <SettingsModal
      v-if="showSettings"
      @close="showSettings = false"
      @save="handleSettingsSave"
    />

    <!-- Profile Modal -->
    <ProfileModal
      :show="showProfileModal"
      :user="currentUser"
      @close="showProfileModal = false"
      @saved="handleProfileSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { createChart } from 'lightweight-charts'
import { useWatchlistStore } from '../stores/watchlist'
import { useNewsStore } from '../stores/news'
import { useAuthStore } from '../stores/auth'
import NewsCard from '../components/NewsCard.vue'
import FlyoutNewsPanel from '../components/FlyoutNewsPanel.vue'
import SettingsModal from '../components/SettingsModal.vue'
import EarningsList from '../components/EarningsList.vue'
import NewsFeed from '../components/NewsFeed.vue'
import BotList from '../components/BotList.vue'
import FlexChat from '../components/FlexChat.vue'
import UserProfile from '../components/UserProfile.vue'
import LoginModal from '../components/LoginModal.vue'
import RegisterModal from '../components/RegisterModal.vue'
import ProfileModal from '../components/ProfileModal.vue'
import api from '../services/api'
import { getCached, setCached, saveIndicatorSettings, loadIndicatorSettings } from '../utils/cache'

const watchlistStore = useWatchlistStore()
const newsStore = useNewsStore()
const authStore = useAuthStore()

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
  },
  {
    id: 5,
    name: 'Flex',
    type: 'flex'
  }
])

const searchQuery = ref('')
const searchResults = ref([])
const showSettings = ref(false)
const showLoginModal = ref(false)
const showRegisterModal = ref(false)
const showProfileModal = ref(false)
const chartRefs = ref({})
const searchTimeout = ref(null)
const searchLoading = ref(false)
const searchError = ref(null)
const isAddingToWatchlist = ref(false)
const currentUser = computed(() => authStore.user)
const isLoggedIn = computed(() => authStore.isAuthenticated)

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
  // Check authentication
  await authStore.checkAuth()
  
  // Restore active tab from localStorage
  const savedActiveTab = localStorage.getItem('activeTab')
  if (savedActiveTab) {
    const tabId = parseInt(savedActiveTab)
    if (tabs.value.find(t => t && t.id === tabId)) {
      activeTab.value = tabId
    }
  }
  
  await watchlistStore.loadWatchlist()
  await newsStore.loadNews()
  if (watchlist.value.length > 0) {
    const firstTab = tabs.value[0]
    selectTicker(firstTab.id, watchlist.value[0].symbol)
  }
})

const setActiveTab = (tabId) => {
  activeTab.value = tabId
  // Persist active tab to localStorage
  localStorage.setItem('activeTab', tabId.toString())
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

const handleLoginSuccess = (userData) => {
  showLoginModal.value = false
  // Auth is already handled in LoginModal
}

const handleRegisterSuccess = (userData) => {
  showRegisterModal.value = false
  // Auth is already handled in RegisterModal
}

const handleLogout = async () => {
  await authStore.logout()
  // Redirect to home
  window.location.href = '/'
}

const handleViewProfile = () => {
  showProfileModal.value = true
}

const handleProfileSaved = () => {
  // Profile was updated, refresh user data
  if (authStore) {
    authStore.fetchUser()
  }
}

const setTimeframe = async (tabId, tf) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    tab.timeframe = tf
    if (tab.selectedTicker) {
      // Update quote with new timeframe to recalculate change/change%
      try {
        const response = await api.getQuote(tab.selectedTicker, tf)
        const quote = response.data
        if (tab.chartInfo) {
          tab.chartInfo.change = quote.change
          tab.chartInfo.changePercent = quote.changePercent
        }
      } catch (error) {
        console.error('Failed to update quote:', error)
      }
      await loadChart(tabId)
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

const toggleIndicator = (tabId, indicator) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    if (!tab.indicators) {
      tab.indicators = {
        rsi: false,
        ma13: false,
        ma50: false,
        ma200: false,
        ma800: false,
        bullRun: false
      }
    }
    tab.indicators[indicator] = !tab.indicators[indicator]
    // Save settings for this ticker
    if (tab.selectedTicker) {
      saveIndicatorSettings(tab.selectedTicker, tab.indicators)
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
  // Clear previous timeout
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
    searchTimeout.value = null
  }
  
  // Clear results if query is empty
  if (searchQuery.value.length === 0) {
    searchResults.value = []
    searchLoading.value = false
    return
  }
  
  // For very short queries (1 char), don't search yet
  if (searchQuery.value.length === 1) {
    searchLoading.value = false
    searchResults.value = []
    return
  }
  
  // Debounce search - wait 400ms after user stops typing
  searchTimeout.value = setTimeout(async () => {
    // Capture current query at the start
    const currentQuery = searchQuery.value
    
    if (currentQuery.length < 2) {
      searchLoading.value = false
      searchResults.value = []
      return
    }
    
    // Show loading only if query hasn't changed
    if (currentQuery === searchQuery.value) {
      searchLoading.value = true
    }
    
    try {
      // Add timeout to prevent hanging (3 seconds - fast feedback)
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Search timeout')), 3000)
      })
      
      const searchPromise = api.search(currentQuery)
      const response = await Promise.race([searchPromise, timeoutPromise])
      
      // Check if query changed while waiting - if so, ignore results
      if (currentQuery !== searchQuery.value) {
        console.log('Query changed during search, ignoring results')
        return
      }
      
      if (response.data && response.data.results) {
        searchResults.value = response.data.results
      } else {
        searchResults.value = []
      }
    } catch (error) {
      // Check if query changed during error
      if (currentQuery !== searchQuery.value) {
        return
      }
      
      // Handle timeout or errors - try to use query as direct ticker if it looks like one
      const queryUpper = currentQuery.trim().toUpperCase()
      if (queryUpper.length >= 1 && queryUpper.length <= 5 && queryUpper.replace('.', '').replace('=', '').replace('^', '').match(/^[A-Z0-9]+$/)) {
        // Query looks like a ticker, add it directly
        searchResults.value = [{
          symbol: queryUpper,
          name: queryUpper,
          type: 'EQUITY',
          exchange: 'N/A'
        }]
      } else {
        searchResults.value = []
      }
    } finally {
      // Only update loading state if query hasn't changed
      if (currentQuery === searchQuery.value) {
        searchLoading.value = false
      }
    }
  }, 400) // 400ms debounce - good balance between responsiveness and performance
}

const addTopResult = () => {
  if (searchResults.value.length > 0) {
    const currentTab = tabs.value.find(t => t.id === activeTab.value)
    addToWatchlist(searchResults.value[0], currentTab.id)
  }
}

const handleResultClick = async (item, tabId) => {
  if (isAddingToWatchlist.value) {
    console.log('Already adding to watchlist, ignoring click')
    return
  }
  console.log('Result clicked:', item, 'tabId:', tabId)
  await addToWatchlist(item, tabId)
}

const addToWatchlist = async (item, tabId) => {
  if (!item || !item.symbol) {
    console.error('Invalid item:', item)
    return
  }
  
  if (isAddingToWatchlist.value) {
    console.log('Already adding to watchlist')
    return
  }
  
  isAddingToWatchlist.value = true
  
  try {
    console.log('Adding to watchlist:', item.symbol, item.name, 'tabId:', tabId)
    
    // Find the current active tab - use the Stocks tab (type === 'stocks')
    let targetTabId = tabId
    if (!targetTabId) {
      // Find the first Stocks tab
      const stocksTab = tabs.value.find(t => t && t.type === 'stocks')
      targetTabId = stocksTab ? stocksTab.id : activeTab.value
    }
    
    // Verify the tab exists and is a stocks tab
    const targetTab = tabs.value.find(t => t && t.id === targetTabId)
    if (!targetTab || targetTab.type !== 'stocks') {
      // Find or create a stocks tab
      const stocksTab = tabs.value.find(t => t && t.type === 'stocks')
      if (stocksTab) {
        targetTabId = stocksTab.id
      } else {
        console.error('No stocks tab found')
        return
      }
    }
    
    console.log('Using tabId:', targetTabId)
    console.log('Current activeTab before activation:', activeTab.value)
    
    // Activate the tab if it's not already active
    if (activeTab.value !== targetTabId) {
      console.log('Activating tab:', targetTabId)
      try {
        setActiveTab(targetTabId)
        await nextTick()
        await new Promise(resolve => setTimeout(resolve, 200))
        console.log('Tab activated, new activeTab:', activeTab.value)
      } catch (error) {
        console.error('Error activating tab:', error)
        throw error
      }
    } else {
      console.log('Tab already active')
    }
    
    console.log('Adding item to watchlist store...')
    try {
      await watchlistStore.addItem(item.symbol, item.name || item.symbol)
      console.log('WatchlistStore.addItem completed successfully')
      console.log('Current watchlist after add:', watchlist.value)
    } catch (error) {
      console.error('Error in watchlistStore.addItem:', error)
      console.error('Error details:', error.response?.data || error.message)
      alert(`Failed to add ${item.symbol} to watchlist: ${error.response?.data?.detail || error.message || 'Unknown error'}`)
      return // Stop here if there's an error
    }
    console.log('Item added to watchlist, clearing search...')
    searchQuery.value = ''
    searchResults.value = []
    
    // Force a reactive update
    await nextTick()
    console.log('Watchlist after nextTick:', watchlist.value)
    
    // Wait a bit for the watchlist to update and DOM to be ready
    console.log('Waiting for DOM to be ready...')
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 300))
    
    // Verify tab is still active and visible
    const currentActiveTab = activeTab.value
    console.log('Current activeTab:', currentActiveTab, 'Target tab:', targetTabId)
    if (currentActiveTab !== targetTabId) {
      console.log('Tab changed, activating target tab again')
      setActiveTab(targetTabId)
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    console.log('Selecting ticker:', item.symbol, 'on tab:', targetTabId)
    await selectTicker(targetTabId, item.symbol)
    console.log('selectTicker completed')
  } catch (error) {
    console.error('Error adding to watchlist:', error)
    console.error('Error response:', error.response)
    console.error('Error stack:', error.stack)
    alert(`Failed to add ${item.symbol} to watchlist: ${error.response?.data?.detail || error.message || 'Unknown error'}`)
  } finally {
    isAddingToWatchlist.value = false
  }
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
  console.log('selectTicker called:', { tabId, symbol })
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab) {
    console.error('Tab not found:', tabId, 'Available tabs:', tabs.value.map(t => t?.id))
    return
  }
  
  console.log('Tab found:', tab)
  tab.selectedTicker = symbol
  tab.chartInfo.symbol = symbol
  
  // Get quote info with current timeframe
  try {
    console.log('Fetching quote for:', symbol, 'timeframe:', tab.timeframe)
    const response = await api.getQuote(symbol, tab.timeframe || '1d')
    const quote = response.data
    tab.chartInfo.name = quote.name
    tab.chartInfo.price = quote.price
    tab.chartInfo.change = quote.change
    tab.chartInfo.changePercent = quote.changePercent
    tab.chartInfo.volume = quote.volume
    console.log('Quote loaded:', quote)
  } catch (error) {
    console.error('Failed to get quote:', error)
  }
  
  // Wait a bit to ensure DOM is ready
  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 100))
  
  console.log('Loading chart for tab:', tabId)
  await loadChart(tabId)
}

const loadChart = async (tabId) => {
  console.log('loadChart called:', tabId)
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab || !tab.selectedTicker) {
    console.error('Tab or ticker not found:', { tab: !!tab, ticker: tab?.selectedTicker })
    return
  }

  const chartContainer = chartRefs.value[tabId]
  if (!chartContainer) {
    console.error('Chart container not found for tab:', tabId, 'Available refs:', Object.keys(chartRefs.value))
    // Try to wait a bit more for the DOM to be ready
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))
    const retryContainer = chartRefs.value[tabId]
    if (!retryContainer) {
      console.error('Chart container still not found after retry')
      return
    }
  }

  try {
    // Check cache first
    const cacheKey = `${tab.selectedTicker}_${tab.timeframe}_${tab.chartType}`
    let chartData = getCached('chart', cacheKey)
    
    if (!chartData || !chartData.data || chartData.data.length === 0) {
      // Fetch from API
      const response = await api.getChart({
        ticker: tab.selectedTicker,
        timeframe: tab.timeframe,
        chart_type: tab.chartType.toLowerCase()
      })
      chartData = response.data
      // Cache the response
      setCached('chart', chartData, cacheKey)
    } else {
      console.log('Using cached chart data for', tab.selectedTicker)
    }

    await nextTick()

    const data = chartData.data
    const earningsDates = chartData.earnings_dates || []

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

    // Initialize indicators state if not exists, load from cache if available
    if (!tab.indicators) {
      const savedSettings = loadIndicatorSettings(tab.selectedTicker)
      tab.indicators = savedSettings || {
        rsi: true,
        ma13: false,
        ma50: false,
        ma200: false,
        ma800: false,
        bullRun: true
      }
    }
    
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
      
      const lineData = validData.map(d => ({
        time: d.time / 1000,
        value: d.close,
      })).filter(d => !isNaN(d.value))
      
      if (lineData.length > 0) {
        tab.lineSeries.setData(lineData)
      }
      
      // Add earnings markers
      if (earningsDates.length > 0 && lineData.length > 0) {
        const markers = earningsDates.map(earning => {
          // Find the closest data point to the earnings date
          const earningsTime = earning.timestamp / 1000
          let closestDataPoint = lineData[0]
          let minDiff = Math.abs(lineData[0].time - earningsTime)
          
          for (const point of lineData) {
            const diff = Math.abs(point.time - earningsTime)
            if (diff < minDiff) {
              minDiff = diff
              closestDataPoint = point
            }
          }
          
          return {
            time: closestDataPoint.time,
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
    if (earningsDates.length > 0 && validData.length > 0) {
      // Find min and max prices in the dataset
      const allPrices = validData.flatMap(d => [d.high, d.low, d.close, d.open].filter(p => p != null))
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

    // Add Moving Averages
    const maSeries = {}
    const maConfigs = [
      { key: 'ma13', period: 13, color: '#E1C542', enabled: tab.indicators?.ma13 },
      { key: 'ma50', period: 50, color: '#4AA3DF', enabled: tab.indicators?.ma50 },
      { key: 'ma200', period: 200, color: '#F39C12', enabled: tab.indicators?.ma200 },
      { key: 'ma800', period: 800, color: '#999999', enabled: tab.indicators?.ma800 },
    ]
    
    maConfigs.forEach(config => {
      if (config.enabled && data.some(d => d[config.key] != null)) {
        const maData = data
          .filter(d => d[config.key] != null)
          .map(d => ({
            time: d.time / 1000,
            value: d[config.key]
          }))
        
        if (maData.length > 0) {
          const series = tab.chart.addLineSeries({
            color: config.color,
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: true,
            title: `MA${config.period}`
          })
          series.setData(maData)
          maSeries[config.key] = series
        }
      }
    })
    tab.maSeries = maSeries

    // Add RSI indicator as overlay on main chart
    if (tab.indicators?.rsi && data.some(d => d.rsi != null)) {
      const rsiData = data
        .filter(d => d.rsi != null)
        .map(d => ({
          time: d.time / 1000,
          value: d.rsi
        }))
      
      if (rsiData.length > 0) {
        // Create RSI series with separate price scale on the right
        const rsiSeries = tab.chart.addLineSeries({
          color: '#9c27b0',
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: true,
          title: 'RSI',
          priceScaleId: 'rsi',
        })
        
        // Configure RSI price scale (0-100 range) on right side
        tab.chart.priceScale('rsi').applyOptions({
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        })
        
        // Add RSI reference lines (30, 50, 70)
        rsiSeries.createPriceLine({
          price: 30,
          color: '#ef5350',
          lineWidth: 1,
          lineStyle: 1, // Dashed
          axisLabelVisible: true,
          title: 'Oversold',
        })
        rsiSeries.createPriceLine({
          price: 50,
          color: '#888',
          lineWidth: 1,
          lineStyle: 1,
          axisLabelVisible: true,
          title: 'Neutral',
        })
        rsiSeries.createPriceLine({
          price: 70,
          color: '#26a69a',
          lineWidth: 1,
          lineStyle: 1,
          axisLabelVisible: true,
          title: 'Overbought',
        })
        
        rsiSeries.setData(rsiData)
        tab.rsiSeries = rsiSeries
      }
    }

    // Add Bull Run markers
    if (tab.indicators?.bullRun && data.some(d => d.bull_run != null && d.bull_run !== 0)) {
      const bullRunMarkers = []
      data.forEach((d) => {
        if (d.bull_run === 1) {
          // Bull signal
          bullRunMarkers.push({
            time: d.time / 1000,
            position: 'belowBar',
            color: '#26a69a',
            shape: 'arrowUp',
            size: 2,
            text: '🐂',
          })
        } else if (d.bull_run === -1) {
          // Bear signal
          bullRunMarkers.push({
            time: d.time / 1000,
            position: 'aboveBar',
            color: '#ef5350',
            shape: 'arrowDown',
            size: 2,
            text: '🐻',
          })
        }
      })
      
      if (bullRunMarkers.length > 0) {
        // Get existing markers and add bull run markers
        const existingMarkers = tab.chartType === 'Candle' && tab.candlestickSeries
          ? (tab.candlestickSeries.markers() || [])
          : (tab.lineSeries?.markers() || [])
        
        const allMarkers = [...existingMarkers, ...bullRunMarkers]
        
        if (tab.chartType === 'Candle' && tab.candlestickSeries) {
          tab.candlestickSeries.setMarkers(allMarkers)
        } else if (tab.lineSeries) {
          tab.lineSeries.setMarkers(allMarkers)
        }
      }
    }

    tab.chart.timeScale().fitContent()
    
    // Save indicator settings for this ticker
    if (tab.indicators) {
      saveIndicatorSettings(tab.selectedTicker, tab.indicators)
    }
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
  background-color: #000000;
  color: #e0e0e0;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 5px;
  padding: 0 20px;
  background-color: #0a0a0a;
  border-bottom: 1px solid #222;
  height: 50px;
}

.tabs-section {
  display: flex;
  flex: 1;
  gap: 2px;
  height: 100%;
  align-items: flex-end;
}

.tab-btn {
  padding: 0 24px;
  height: 40px;
  background-color: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #888;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  transition: all 0.3s ease;
  letter-spacing: 1px;
}

.tab-btn:hover {
  color: #fff;
  background-color: #111;
}

.tab-btn.active {
  background-color: #000;
  border-bottom: 2px solid #fff;
  color: #fff;
}

.add-tab-btn {
  padding: 0 12px;
  height: 30px;
  background-color: #1a1a1a;
  border: 1px solid #333;
  border-radius: 2px;
  color: #888;
  cursor: pointer;
  font-size: 16px;
  margin-left: 10px;
  margin-bottom: 5px;
  transition: all 0.2s;
}

.add-tab-btn:hover {
  background-color: #333;
  color: #fff;
}

/* Tab Content */
.tab-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.tab-panel {
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.stocks-panel, .earnings-panel, .news-panel, .bot-panel, .flex-panel {
  height: 100%;
}

/* Main Content Layout for Stocks Tab */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0; /* Important for flex scrolling */
}

/* Chart Info Bar */
.chart-info-bar {
  display: flex;
  align-items: center;
  gap: 30px;
  padding: 15px 30px;
  background-color: #050505;
  border-bottom: 1px solid #222;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 10px;
  color: #666;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.info-value {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
  font-family: 'Roboto Mono', monospace;
}

.info-value.positive {
  color: #4caf50;
}

.info-value.negative {
  color: #f44336;
}

.price-item {
  margin-left: auto;
  align-items: flex-end;
}

.price-value {
  font-size: 24px;
  font-weight: 300;
  color: #fff;
  font-family: 'Roboto Mono', monospace;
  letter-spacing: -1px;
}

/* Chart Toolbar */
.chart-toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 30px;
  background-color: #0a0a0a;
  border-bottom: 1px solid #222;
}

.timeframe-buttons, .chart-type-buttons {
  display: flex;
  background-color: #151515;
  border-radius: 4px;
  padding: 2px;
}

.timeframe-btn, .chart-type-btn {
  padding: 6px 12px;
  background-color: transparent;
  border: none;
  border-radius: 2px;
  color: #888;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
}

.timeframe-btn:hover, .chart-type-btn:hover {
  color: #fff;
}

.timeframe-btn.active, .chart-type-btn.active {
  background-color: #333;
  color: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.5);
}

.indicators-buttons {
  display: flex;
  gap: 8px;
  margin-left: 20px;
}

.indicator-btn {
  padding: 6px 12px;
  background-color: #151515;
  border: 1px solid #333;
  border-radius: 2px;
  color: #888;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
  text-transform: uppercase;
}

.indicator-btn:hover {
  border-color: #555;
  color: #fff;
}

.indicator-btn.active {
  background-color: #fff;
  color: #000;
  border-color: #fff;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.view-mode-btn, .settings-btn {
  padding: 8px;
  background-color: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 16px;
  transition: color 0.2s;
}

.view-mode-btn:hover, .settings-btn:hover {
  color: #fff;
}

.view-mode-btn.active {
  color: #fff;
}

/* Panels */
.left-panel {
  width: 280px;
  background-color: #050505;
  border-right: 1px solid #222;
  padding: 20px;
}

.search-section {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 10px 12px;
  background-color: #111;
  border: 1px solid #333;
  border-radius: 2px;
  color: #fff;
  font-size: 13px;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #666;
}

.add-btn {
  display: none; /* Hide default add button, use enter key */
}

.panel-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #666;
  letter-spacing: 1px;
  margin-bottom: 15px;
  padding-bottom: 5px;
  border-bottom: 1px solid #222;
}

.watchlist {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 15px;
}

.watchlist-item {
  padding: 12px 10px;
  border-bottom: 1px solid #1a1a1a;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watchlist-item:hover {
  background-color: #111;
}

.watchlist-item.active {
  background-color: #1a1a1a;
  border-left: 3px solid #4299e1; /* Blue accent for better visibility */
  padding-left: 7px; /* Adjust padding to compensate for border */
}

.symbol {
  font-weight: 700;
  color: #fff;
  font-size: 14px;
  letter-spacing: 0.5px;
}

.watchlist-item.active .symbol {
  color: #4299e1; /* Highlight symbol when active */
}

.name {
  font-size: 11px;
  color: #666;
  text-align: right;
  font-family: 'Roboto Mono', monospace;
}

.watchlist-item.active .name {
  color: #888;
}

.remove-btn {
  width: 100%;
  padding: 12px;
  background-color: transparent;
  border: 1px solid #333;
  border-radius: 2px;
  color: #666;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: auto; /* Push to bottom if parent is flex column */
}

.remove-btn:hover {
  border-color: #f44336;
  color: #f44336;
  background-color: rgba(244, 67, 54, 0.05);
}

.chart-container {
  background-color: #000;
}

.right-panel {
  background-color: #050505;
  border-left: 1px solid #222;
}

.welcome-screen h1 {
  font-weight: 300;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-size: 24px;
  margin-bottom: 15px;
}

.welcome-screen p {
  color: #666;
  font-size: 13px;
  letter-spacing: 0.5px;
}

/* Custom overrides for lightweight charts */
:deep(.tv-lightweight-charts) {
  font-family: 'Roboto Mono', monospace !important;
}
</style>
