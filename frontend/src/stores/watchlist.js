import { defineStore } from 'pinia'
import api from '../services/api'

export const useWatchlistStore = defineStore('watchlist', {
  state: () => ({
    watchlist: [],
  }),
  
  actions: {
    async loadWatchlist() {
      try {
        const response = await api.getWatchlist()
        this.watchlist = response.data.watchlist || []
      } catch (error) {
        console.error('Failed to load watchlist:', error)
      }
    },
    
    async addItem(symbol, name) {
      try {
        await api.addToWatchlist(symbol, name)
        await this.loadWatchlist()
      } catch (error) {
        console.error('Failed to add item:', error)
      }
    },
    
    async removeItem(symbol) {
      try {
        await api.removeFromWatchlist(symbol)
        await this.loadWatchlist()
      } catch (error) {
        console.error('Failed to remove item:', error)
      }
    },
  },
})

