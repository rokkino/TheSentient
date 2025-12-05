import { defineStore } from 'pinia'
import api from '../services/api'

export const useNewsStore = defineStore('news', {
  state: () => ({
    news: [],
  }),
  
  actions: {
    async loadNews(tickers = null, limit = 50) {
      try {
        const response = await api.getNews(tickers, limit)
        this.news = response.data.news || []
      } catch (error) {
        console.error('Failed to load news:', error)
      }
    },
  },
})

