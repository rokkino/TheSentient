import { defineStore } from 'pinia'
import { useNewsStore } from './news'

export const useWebSocketStore = defineStore('websocket', {
  state: () => ({
    ws: null,
    connected: false,
  }),
  
  actions: {
    connect() {
      const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
      const wsUrl = `${WS_URL}/ws`
      
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        this.connected = true
        console.log('WebSocket connected')
        // Subscribe to news updates
        this.ws.send(JSON.stringify({
          type: 'subscribe_news',
          tickers: []
        }))
      }
      
      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        
        if (message.type === 'new_news') {
          const newsStore = useNewsStore()
          newsStore.news.unshift(message.data)
          // Keep only last 100 news items
          if (newsStore.news.length > 100) {
            newsStore.news = newsStore.news.slice(0, 100)
          }
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
      
      this.ws.onclose = () => {
        this.connected = false
        console.log('WebSocket disconnected')
        // Reconnect after 5 seconds
        setTimeout(() => this.connect(), 5000)
      }
    },
    
    disconnect() {
      if (this.ws) {
        this.ws.close()
        this.ws = null
        this.connected = false
      }
    },
  },
})

