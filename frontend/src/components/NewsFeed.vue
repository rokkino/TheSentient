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
        <select v-model="selectedTicker" @change="filterNews" class="ticker-filter">
          <option value="">All Tickers</option>
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

const newsStore = useNewsStore()

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
const selectedTicker = ref('')
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
  if (selectedTicker.value) {
    filtered = filtered.filter(item => item.ticker === selectedTicker.value)
  }

  return filtered
})

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
    const response = await api.getNews(null, pageSize * page, savedPublishers)
    
    if (response.data && response.data.news) {
      if (page === 1) {
        newsItems.value = response.data.news
      } else {
        // Merge new items, avoiding duplicates
        const existingLinks = new Set(newsItems.value.map(n => n.link))
        const newItems = response.data.news.filter(n => !existingLinks.has(n.link))
        newsItems.value = [...newsItems.value, ...newItems]
      }
      
      hasMore.value = response.data.news.length === pageSize * page
      currentPage.value = page
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load news'
    console.error('Error loading news:', err)
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
  overflow: hidden;
}

.news-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #2d3748;
}

.news-header h2 {
  margin: 0 0 15px 0;
  color: #e2e8f0;
  font-size: 24px;
}

.news-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 10px;
  background: #2d3748;
  color: #e2e8f0;
  border: 1px solid #4a5568;
  border-radius: 6px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: #718096;
}

.ticker-filter {
  padding: 10px;
  background: #2d3748;
  color: #e2e8f0;
  border: 1px solid #4a5568;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  min-width: 150px;
}

.ticker-filter:hover {
  border-color: #718096;
}

.loading, .error, .no-news {
  text-align: center;
  padding: 40px;
  color: #a0aec0;
}

.error {
  color: #fc8181;
}

.news-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
}

.load-more-btn {
  margin-top: 20px;
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

