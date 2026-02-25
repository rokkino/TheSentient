import { defineStore } from 'pinia'

export const useChartStore = defineStore('chart', {
  state: () => ({
    currentTicker: null,
    currentTimeframe: '1y',
    currentChartType: 'candle',
  }),
  
  actions: {
    setTicker(ticker) {
      this.currentTicker = ticker
    },
    
    setTimeframe(timeframe) {
      this.currentTimeframe = timeframe
    },
    
    setChartType(type) {
      this.currentChartType = type
    },
  },
})

