<template>
  <div class="news-feed-container">
    <div class="news-header">
      <h2>All News</h2>
      <div class="news-controls">
        <input
          v-model="searchQuery"
          @input="filterNews"
          placeholder="Search news..."
          class="search-input"
        />
        <select v-model="selectedTicker" @change="handleFilterChange" class="ticker-filter">
          <option value="">All Tickers</option>
          <option value="__watchlist__">My Watchlist</option>
          <option v-for="ticker in uniqueTickers" :key="ticker" :value="ticker">
            {{ ticker }}
          </option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading news...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="filteredNews.length === 0" class="no-news">
      No news found.
    </div>
    <div v-else class="news-list">
      <NewsCard
        v-for="newsItem in filteredNews"
        :key="newsItem.link"
        :news-item="newsItem"
      />
    </div>

    <button
      v-if="hasMore && !loading"
      @click="loadMore"
      class="load-more-btn"
      :disabled="loadingMore"
    >
      {{ loadingMore ? 'Loading...' : 'Load More' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import NewsCard from './NewsCard.vue'
import api from '../services/api'
import { useNewsStore } from '../stores/news'
import { useWatchlistStore } from '../stores/watchlist'
import { getCached, setCached } from '../utils/cache'

const newsStore = useNewsStore()
const watchlistStore = useWatchlistStore()

// Load saved publisher filters
const getSavedPublishers = () => {
  try {
    const saved = localStorage.getItem('selectedPublishers')
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Error loading saved publishers:', e)
  }
  return null
}

const newsItems = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(null)
const searchQuery = ref('')
const selectedTicker = ref(localStorage.getItem('news_selected_ticker') || '')
const currentPage = ref(1)
const pageSize = 50
const hasMore = ref(true)

const uniqueTickers = computed(() => {
  const tickers = new Set()
  newsItems.value.forEach(item => {
    if (item.ticker) {
      tickers.add(item.ticker)
    }
  })
  return Array.from(tickers).sort()
})

const filteredNews = computed(() => {
  let filtered = newsItems.value

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(item =>
      item.title?.toLowerCase().includes(query) ||
      item.text?.toLowerCase().includes(query) ||
      item.publisher?.toLowerCase().includes(query)
    )
  }

  // Filter by ticker
  if (selectedTicker.value && selectedTicker.value !== '__watchlist__') {
    filtered = filtered.filter(item => item.ticker === selectedTicker.value)
  }

  return filtered
})

const handleFilterChange = () => {
  localStorage.setItem('news_selected_ticker', selectedTicker.value)
  loadNews(1)
}

const loadNews = async (page = 1) => {
  if (page === 1) {
    loading.value = true
    newsItems.value = []
  } else {
    loadingMore.value = true
  }
  
  error.value = null

  try {
    const savedPublishers = getSavedPublishers()
    let tickers = null
    
    // If "My Watchlist" is selected, use watchlist tickers
    if (selectedTicker.value === '__watchlist__') {
      // Ensure watchlist is loaded
      if (watchlistStore.watchlist.length === 0) {
        await watchlistStore.loadWatchlist()
      }
      
      tickers = watchlistStore.watchlist.map(item => item.symbol)
      
      if (tickers.length === 0) {
        loading.value = false
        loadingMore.value = false
        error.value = 'No items in watchlist'
        return // No items in watchlist
      }
    }
    
    // Create cache key
    const tickersKey = tickers ? tickers.sort().join(',') : 'all'
    const publishersKey = savedPublishers ? savedPublishers.sort().join(',') : 'all'
    const cacheKey = `${tickersKey}_${publishersKey}_${page}`
    
    // Check cache first
    let newsData = getCached('news', cacheKey)
    
    if (!newsData) {
      console.log('Fetching news from API...', { tickers, limit: pageSize * page, publishers: savedPublishers })
      const response = await api.getNews(tickers, pageSize * page, savedPublishers)
      console.log('News API response:', response)
      newsData = response.data
      
      // Validate response structure
      if (!newsData || !newsData.news) {
        console.error('Invalid news response structure:', newsData)
        error.value = 'Invalid response from server'
        return
      }
      
      // Cache the response
      setCached('news', newsData, cacheKey)
    } else {
      console.log('Using cached news data')
    }
    
    if (newsData && newsData.news) {
      if (page === 1) {
        newsItems.value = newsData.news
      } else {
        // Merge new items, avoiding duplicates
        const existingLinks = new Set(newsItems.value.map(n => n.link))
        const newItems = newsData.news.filter(n => !existingLinks.has(n.link))
        newsItems.value = [...newsItems.value, ...newItems]
      }
      
      hasMore.value = newsData.news.length === pageSize
      currentPage.value = page
      
      console.log(`Loaded ${newsData.news.length} news items`)
    } else {
      console.error('No news data in response:', newsData)
      error.value = 'No news data received'
    }
  } catch (err) {
    console.error('Error loading news:', err)
    error.value = err.response?.data?.detail || err.message || 'Failed to load news'
    console.error('Error details:', {
      message: err.message,
      response: err.response?.data,
      status: err.response?.status
    })
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  loadNews(currentPage.value + 1)
}

const filterNews = () => {
  // Filtering is handled by computed property
}

// Watch for new news from WebSocket
watch(() => newsStore.news, (newNews) => {
  if (newNews && newNews.length > 0) {
    // Add new news items that aren't already in the list
    const existingLinks = new Set(newsItems.value.map(n => n.link))
    const newItems = newNews.filter(n => !existingLinks.has(n.link))
    if (newItems.length > 0) {
      newsItems.value = [...newItems, ...newsItems.value]
    }
  }
}, { deep: true })

onMounted(() => {
  loadNews()
  // Also load from store if available
  if (newsStore.news && newsStore.news.length > 0) {
    newsItems.value = [...newsStore.news]
  }
})
</script>

<style scoped>
.news-feed-container {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Prevent container from scrolling */
  background: #050505;
}

.news-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #222;
}

.news-header h2 {
  margin: 0 0 15px 0;
  color: #fff;
  font-size: 18px;
  font-weight: 300;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.news-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 10px 12px;
  background: #111;
  color: #fff;
  border: 1px solid #333;
  border-radius: 2px;
  font-size: 13px;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #666;
}

.ticker-filter {
  padding: 10px 12px;
  background: #111;
  color: #fff;
  border: 1px solid #333;
  border-radius: 2px;
  font-size: 13px;
  cursor: pointer;
  min-width: 150px;
}

.ticker-filter:hover {
  border-color: #555;
}

.loading, .error, .no-news {
  text-align: center;
  padding: 40px;
  color: #666;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.error {
  color: #f44336;
}

.news-list {
  flex: 1;
  overflow-y: auto; /* Enable vertical scrolling */
  padding-right: 5px;
  min-height: 0; /* Important for flex child scrolling */
}

.load-more-btn {
  margin-top: 20px;
  width: 100%;
  padding: 12px;
  background: #151515;
  color: #fff;
  border: 1px solid #333;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
}

.load-more-btn:hover:not(:disabled) {
  background: #222;
  border-color: #666;
}

.load-more-btn:disabled {
  background: #0a0a0a;
  color: #444;
  cursor: not-allowed;
  border-color: #222;
}
</style>

