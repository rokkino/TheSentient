import { defineStore } from 'pinia'
import { useNewsStore } from './news'

export const useWebSocketStore = defineStore('websocket', {
  state: () => ({
    ws: null,
    connected: false,
  }),
  
  actions: {
    connect() {
      // Don't reconnect if already connected or connecting
      if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
        return
      }
      
      const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
      const wsUrl = `${WS_URL}/ws`
      
      try {
        this.ws = new WebSocket(wsUrl)
        
        this.ws.onopen = () => {
          this.connected = true
          console.log('WebSocket connected')
          // Subscribe to news updates
          try {
            this.ws.send(JSON.stringify({
              type: 'subscribe_news',
              tickers: []
            }))
          } catch (e) {
            console.error('Error sending WebSocket message:', e)
          }
        }
        
        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            
            if (message.type === 'new_news') {
              const newsStore = useNewsStore()
              newsStore.news.unshift(message.data)
              // Keep only last 100 news items
              if (newsStore.news.length > 100) {
                newsStore.news = newsStore.news.slice(0, 100)
              }
            } else if (message.type === 'chat_message') {
              // Handle chat messages
              // This will be handled by FlexChat component
            }
          } catch (e) {
            console.error('Error parsing WebSocket message:', e)
          }
        }
        
        this.ws.onerror = (error) => {
          console.warn('WebSocket error (will retry):', error)
          this.connected = false
        }
        
        this.ws.onclose = (event) => {
          this.connected = false
          console.log('WebSocket disconnected', event.code, event.reason)
          // Only reconnect if it wasn't a manual close
          if (event.code !== 1000) {
            // Reconnect after 5 seconds
            setTimeout(() => {
              if (!this.connected) {
                this.connect()
              }
            }, 5000)
          }
        }
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error)
        this.connected = false
        // Retry after 5 seconds
        setTimeout(() => {
          if (!this.connected) {
            this.connect()
          }
        }, 5000)
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

