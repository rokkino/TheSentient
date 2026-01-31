<template>
  <div class="news-feed-container">
    <div class="news-header-glass">
      <div class="header-content">
        <h2>Market Pulse</h2>
        <div class="news-controls">
          <div class="search-wrapper">
            <span class="search-icon">🔍</span>
            <input
              v-model="searchQuery"
              @input="filterNews"
              placeholder="Search news..."
              class="search-input"
            />
          </div>
          
          <select v-model="selectedTicker" @change="handleFilterChange" class="ticker-filter">
            <option value="">Global Market</option>
            <option value="__watchlist__">My Watchlist</option>
          </select>
          
          <button
            @click="refreshNews"
            class="update-btn"
            :disabled="loading"
            title="Refresh news"
          >
            <span class="update-icon" :class="{ spinning: loading }">↻</span>
          </button>
        </div>
      </div>
    </div>

    <div class="scroll-container" ref="newsListRef" @scroll="handleScroll">
      <div v-if="loading && newsItems.length === 0" class="loading-state">
        <div class="spinner"></div>
        <span>Gathering intel...</span>
      </div>
      
      <div v-else-if="error" class="error-state">
        <span class="error-icon">⚠️</span>
        {{ error }}
      </div>
      
      <div v-else-if="filteredNews.length === 0" class="empty-state">
        No news found matching your criteria.
      </div>
      
      <div v-else class="news-content">
        <!-- Hero Section -->
        <div v-if="heroItem" class="hero-section">
          <NewsCard
            :news-item="heroItem"
            variant="hero"
            @ask-ai="askLlama"
            @click="handleNewsClick"
          />
        </div>

        <!-- Masonry Grid -->
        <div class="masonry-grid">
          <NewsCard
            v-for="newsItem in remainingItems"
            :key="newsItem.link"
            :news-item="newsItem"
            @ask-ai="askLlama"
            @click="handleNewsClick"
          />
        </div>

        <div v-if="loadingMore" class="loading-more">
          <div class="spinner-small"></div>
        </div>
        
        <div v-if="!hasMore && filteredNews.length > 0" class="end-marker">
          <span>End of feed</span>
        </div>
      </div>
    </div>

    <!-- News Detail Modal -->
    <NewsDetailModal
      :show="showNewsDetailModal"
      :news-item="selectedDetailNewsItem"
      @close="closeNewsDetailModal"
      @ask-ai="askLlamaFromDetail"
    />

    <!-- Llama Modal -->
    <div v-if="showLlamaModal" class="modal-overlay llama-modal-overlay" @click="closeLlamaModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ selectedNewsItem ? 'Ask AI about News' : 'Ask AI' }}</h3>
          <button class="close-btn" @click="closeLlamaModal">×</button>
        </div>
        <div class="modal-body">
          <div v-if="selectedNewsItem" class="selected-context">
            <div class="context-title">{{ selectedNewsItem.title }}</div>
            <div class="context-meta">
              {{ selectedNewsItem.publisher }} • {{ new Date(selectedNewsItem.timestamp).toLocaleString() }}
            </div>
          </div>

          <div v-if="llamaLoading" class="loading-spinner"></div>
          <div v-else-if="llamaResponse" class="llama-response">
            <div class="response-text">{{ llamaResponse }}</div>
            <button class="ask-another-btn" @click="llamaResponse = ''">Ask Another Question</button>
          </div>
          <div v-else class="llama-input-container">
            <p>Ask a question about this news article:</p>
            <div class="input-group">
                <input 
                    v-model="llamaQuestion" 
                    placeholder="e.g. How does this affect the stock price?" 
                    class="llama-input"
                    @keyup.enter="submitLlamaQuestion"
                    ref="llamaInputRef"
                />
                <button class="submit-btn" @click="submitLlamaQuestion">Ask</button>
            </div>
            <div class="quick-actions">
                <button @click="submitLlamaQuestion('Summarize this article')">Summarize</button>
                <button @click="submitLlamaQuestion('Is this bullish or bearish?')">Sentiment</button>
                <button @click="submitLlamaQuestion('What are the key takeaways?')">Key Points</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import NewsCard from './NewsCard.vue'
import NewsDetailModal from './NewsDetailModal.vue'
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
const pageSize = 10 
const maxPages = 10 
const hasMore = ref(true)
const newsListRef = ref(null)
const isLoadingNextPage = ref(false)

// Llama Modal State
const showLlamaModal = ref(false)
const selectedNewsItem = ref(null)
const llamaResponse = ref('')
const llamaLoading = ref(false)
const llamaQuestion = ref('')
const llamaInputRef = ref(null)

// News Detail Modal State
const showNewsDetailModal = ref(false)
const selectedDetailNewsItem = ref(null)

const handleNewsClick = (newsItem) => {
  selectedDetailNewsItem.value = newsItem
  showNewsDetailModal.value = true
}

const closeNewsDetailModal = () => {
  showNewsDetailModal.value = false
  selectedDetailNewsItem.value = null
}

const askLlamaFromDetail = (newsItem) => {
  // We can keep the detail modal open or close it. 
  // Let's keep it open but ensure Llama modal is on top (via z-index).
  askLlama(newsItem)
}

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

  // Filter by watchlist if selected
  if (selectedTicker.value === '__watchlist__') {
    if (watchlistStore.watchlist.length > 0) {
      const watchlistSymbols = new Set(watchlistStore.watchlist.map(item => item.symbol))
      filtered = filtered.filter(item => item.ticker && watchlistSymbols.has(item.ticker))
    } else {
      filtered = []
    }
  }

  return filtered
})

const heroItem = computed(() => {
  if (filteredNews.value.length === 0) return null
  return filteredNews.value[0]
})

const remainingItems = computed(() => {
  if (filteredNews.value.length <= 1) return []
  return filteredNews.value.slice(1)
})

const handleFilterChange = () => {
  localStorage.setItem('news_selected_ticker', selectedTicker.value)
}

const refreshNews = async (force = false) => {
  if (force) {
    const savedPublishers = getSavedPublishers()
    let tickers = null
    
    if (selectedTicker.value === '__watchlist__') {
      if (watchlistStore.watchlist.length === 0) {
        await watchlistStore.loadWatchlist()
      }
      tickers = watchlistStore.watchlist.map(item => item.symbol)
    }
    
    const tickersKey = tickers ? tickers.sort().join(',') : 'all'
    const publishersKey = savedPublishers ? savedPublishers.sort().join(',') : 'all'
    const cacheKey = `${tickersKey}_${publishersKey}_1`
    
    try {
      const fullCacheKey = `thesentient_cache_news_${cacheKey}`
      localStorage.removeItem(fullCacheKey)
    } catch (e) {
      console.error('[NEWS] Error clearing cache:', e)
    }
  }
  
  await loadNews(1, force)
}

const loadNews = async (page = 1, forceRefresh = false) => {
  if (page === 1) {
    loading.value = true
    if (forceRefresh) {
      newsItems.value = []
    }
  } else {
    loadingMore.value = true
    isLoadingNextPage.value = true
  }
  
  error.value = null

  try {
    const savedPublishers = getSavedPublishers()
    let tickers = null
    
    if (selectedTicker.value === '__watchlist__') {
      if (watchlistStore.watchlist.length === 0) {
        await watchlistStore.loadWatchlist()
      }
      
      tickers = watchlistStore.watchlist.map(item => item.symbol)
      
      if (tickers.length === 0) {
        loading.value = false
        loadingMore.value = false
        error.value = 'No items in watchlist'
        return 
      }
    }
    
    const tickersKey = tickers ? tickers.sort().join(',') : 'all'
    const publishersKey = savedPublishers ? savedPublishers.sort().join(',') : 'all'
    const cacheKey = `${tickersKey}_${publishersKey}_${page}`
    
    let newsData = null
    if (!forceRefresh) {
      newsData = getCached('news', cacheKey)
    }
    
    if (!newsData) {
      const limit = pageSize * page
      const response = await api.getNews(tickers, limit, savedPublishers)
      newsData = response.data
      
      if (page > 1 && newsData.news) {
        const startIndex = (page - 1) * pageSize
        newsData.news = newsData.news.slice(startIndex, startIndex + pageSize)
      }
      
      if (!newsData || !newsData.news) {
        error.value = 'Invalid response from server'
        return
      }
      
      setCached('news', newsData, cacheKey)
    }
    
    if (newsData && newsData.news) {
      if (page === 1) {
        newsItems.value = newsData.news
      } else {
        const existingLinks = new Set(newsItems.value.map(n => n.link))
        const newItems = newsData.news.filter(n => !existingLinks.has(n.link))
        newsItems.value = [...newsItems.value, ...newItems]
      }
      
      hasMore.value = newsData.news.length === pageSize && page < maxPages
      currentPage.value = page
      
      if (page >= maxPages) {
        hasMore.value = false
      }
    } else {
      error.value = 'No news data received'
    }
  } catch (err) {
    console.error('Error loading news:', err)
    error.value = err.response?.data?.detail || err.message || 'Failed to load news'
  } finally {
    loading.value = false
    loadingMore.value = false
    isLoadingNextPage.value = false
  }
}

const handleScroll = (event) => {
  const element = event.target
  const scrollTop = element.scrollTop
  const scrollHeight = element.scrollHeight
  const clientHeight = element.clientHeight
  
  const scrollPercentage = (scrollTop + clientHeight) / scrollHeight
  
  if (scrollPercentage > 0.8 && hasMore.value && !loadingMore.value && !isLoadingNextPage.value && currentPage.value < maxPages) {
    loadMore()
  }
}

const loadMore = () => {
  if (currentPage.value >= maxPages) {
    hasMore.value = false
    return
  }
  loadNews(currentPage.value + 1)
}

const filterNews = () => {
  // Filtering is handled by computed property
}

watch(() => newsStore.news, (newNews) => {
  if (newNews && newNews.length > 0) {
    const existingLinks = new Set(newsItems.value.map(n => n.link))
    const newItems = newNews.filter(n => !existingLinks.has(n.link))
    if (newItems.length > 0) {
      newsItems.value = [...newItems, ...newsItems.value]
    }
  }
}, { deep: true })

onMounted(async () => {
  if (selectedTicker.value === '__watchlist__' && watchlistStore.watchlist.length === 0) {
    await watchlistStore.loadWatchlist()
  }
  
  const savedPublishers = getSavedPublishers()
  let tickers = null
  
  if (selectedTicker.value === '__watchlist__') {
    tickers = watchlistStore.watchlist.map(item => item.symbol)
  }
  
  const tickersKey = tickers ? tickers.sort().join(',') : 'all'
  const publishersKey = savedPublishers ? savedPublishers.sort().join(',') : 'all'
  const cacheKey = `${tickersKey}_${publishersKey}_1`
  
  const cachedNews = getCached('news', cacheKey)
  
  if (cachedNews && cachedNews.news && cachedNews.news.length > 0) {
    newsItems.value = cachedNews.news
    hasMore.value = cachedNews.news.length === pageSize
    currentPage.value = 1
  } else {
    await loadNews(1)
  }
  
  if (newsStore.news && newsStore.news.length > 0 && newsItems.value.length === 0) {
    newsItems.value = [...newsStore.news]
  }
})

// Llama Functions
const askLlama = (newsItem) => {
  selectedNewsItem.value = newsItem
  showLlamaModal.value = true
  llamaResponse.value = ''
  llamaQuestion.value = ''
  // Focus input next tick
  setTimeout(() => {
    if (llamaInputRef.value) llamaInputRef.value.focus()
  }, 100)
}

const closeLlamaModal = () => {
  showLlamaModal.value = false
  selectedNewsItem.value = null
}

const submitLlamaQuestion = async (predefinedQuestion = null) => {
  const question = typeof predefinedQuestion === 'string' ? predefinedQuestion : llamaQuestion.value
  if (!question) return

  llamaLoading.value = true
  try {
    const response = await api.askLlamaAboutNews(selectedNewsItem.value, question)
    llamaResponse.value = response.data.response
  } catch (e) {
    llamaResponse.value = "Error asking AI: " + (e.response?.data?.detail || e.message)
  } finally {
    llamaLoading.value = false
  }
}
</script>

<style scoped>
.news-feed-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #050505;
  color: #fff;
  position: relative;
}

.news-header-glass {
  padding: 20px 30px;
  background: rgba(20, 20, 20, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  z-index: 10;
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
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.news-controls {
  display: flex;
  gap: 12px;
  align-items: center;
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
  padding: 10px 15px 10px 35px;
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

.ticker-filter {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 30px;
  padding: 10px 20px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  appearance: none;
  min-width: 160px;
  transition: all 0.3s ease;
}

.ticker-filter:hover {
  background: rgba(255, 255, 255, 0.1);
}

.update-btn {
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

.update-btn:hover:not(:disabled) {
  background: rgba(66, 153, 225, 0.2);
  transform: rotate(180deg);
}

.update-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 30px;
  scroll-behavior: smooth;
}

.news-content {
  max-width: 1600px;
  margin: 0 auto;
}

.hero-section {
  margin-bottom: 30px;
  animation: fadeIn 0.6s ease-out;
}

.masonry-grid {
  column-count: 3;
  column-gap: 24px;
  animation: fadeIn 0.8s ease-out;
}

@media (max-width: 1400px) {
  .masonry-grid {
    column-count: 2;
  }
}

@media (max-width: 800px) {
  .masonry-grid {
    column-count: 1;
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input {
    width: 100%;
  }
  
  .search-input:focus {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .news-feed-container {
    padding-bottom: env(safe-area-inset-bottom);
  }

  .news-header-glass {
    padding: 12px 16px;
  }

  .search-input {
    min-height: 44px;
    font-size: 16px;
  }
}

.loading-state, .error-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #888;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

.spinner-small {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-more {
  display: flex;
  justify-content: center;
  padding: 30px 0;
}

.end-marker {
  text-align: center;
  padding: 40px 0;
  color: #444;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 2px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
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

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

.llama-modal-overlay {
  z-index: 3000; /* Higher than NewsDetailModal (2000) */
}

.modal-content {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-header {
  padding: 20px;
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
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
}

.selected-context {
  background: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 3px solid #4299e1;
}

.context-title {
  font-weight: 600;
  color: #fff;
  margin-bottom: 5px;
}

.context-meta {
  font-size: 12px;
  color: #888;
}

.llama-input-container p {
  margin-top: 0;
  color: #ccc;
  font-size: 14px;
}

.input-group {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.llama-input {
  flex: 1;
  background: #111;
  border: 1px solid #333;
  color: #fff;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
}

.llama-input:focus {
  outline: none;
  border-color: #4299e1;
}

.submit-btn {
  background: #4299e1;
  color: #fff;
  border: none;
  padding: 0 20px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover {
  background: #3182ce;
}

.quick-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.quick-actions button {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ccc;
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-actions button:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #666;
  color: #fff;
}

.llama-response {
  background: rgba(66, 153, 225, 0.1);
  border: 1px solid rgba(66, 153, 225, 0.2);
  border-radius: 8px;
  padding: 20px;
}

.response-text {
  color: #e2e8f0;
  line-height: 1.6;
  font-size: 15px;
  white-space: pre-wrap;
}

.ask-another-btn {
  margin-top: 15px;
  background: transparent;
  border: 1px solid #4299e1;
  color: #4299e1;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.ask-another-btn:hover {
  background: rgba(66, 153, 225, 0.1);
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>

