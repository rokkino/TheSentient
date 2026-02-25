import { defineStore } from 'pinia'
import api from '../services/api'

export const useWatchlistStore = defineStore('watchlist', {
  state: () => ({
    watchlist: [],
  }),
  
  actions: {
    async loadWatchlist() {
      try {
        console.log('WatchlistStore: Loading watchlist...')
        const response = await api.getWatchlist()
        console.log('WatchlistStore: Watchlist loaded:', response.data)
        this.watchlist = response.data.watchlist || []
        console.log('WatchlistStore: State updated:', this.watchlist)
      } catch (error) {
        console.error('Failed to load watchlist:', error)
      }
    },
    
    async addItem(symbol, name) {
      try {
        console.log('WatchlistStore: Adding item', symbol, name)
        await api.addToWatchlist(symbol, name)
        console.log('WatchlistStore: Item added, reloading watchlist...')
        await this.loadWatchlist()
        console.log('WatchlistStore: Watchlist reloaded', this.watchlist)
      } catch (error) {
        console.error('WatchlistStore: Failed to add item:', error)
        throw error // Re-throw to let caller handle it
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

