import { defineStore } from 'pinia'
import api from '../services/api'
import { getCached, setCached } from '../utils/cache'

export const useNewsStore = defineStore('news', {
  state: () => ({
    news: [],
    lastUpdated: null,
  }),
  
  actions: {
    async loadNews(tickers = null, limit = 50) {
      const cacheKey = `news_store_${tickers ? tickers.join(',') : 'all'}_${limit}`
      
      // Try cache first
      const cached = getCached('news_store', cacheKey)
      if (cached) {
        this.news = cached
        return
      }

      try {
        const response = await api.getNews(tickers, limit)
        this.news = response.data.news || []
        
        // Save to cache (5 minutes)
        setCached('news_store', this.news, cacheKey, 5 * 60 * 1000)
        this.lastUpdated = Date.now()
      } catch (error) {
        console.error('Failed to load news:', error)
      }
    },
    
    // Add method to manually clear cache/force refresh
    clearCache() {
      // Logic to clear specific cache entries would go in utils/cache.js
      // For now we just reset state
      this.news = []
      this.lastUpdated = null
    }
  },
})

