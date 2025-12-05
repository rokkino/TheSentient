import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default {
  // Chart endpoints
  getChart(data) {
    return api.post('/chart', data)
  },
  
  getQuote(ticker) {
    return api.get(`/quote/${ticker}`)
  },
  
  // Search endpoints
  search(query) {
    return api.post('/search', { query })
  },
  
  // Watchlist endpoints
  getWatchlist() {
    return api.get('/watchlist')
  },
  
  addToWatchlist(symbol, name) {
    return api.post('/watchlist', { symbol, name })
  },
  
  removeFromWatchlist(symbol) {
    return api.delete(`/watchlist/${symbol}`)
  },
  
  // News endpoints
  getNews(tickers = null, limit = 50, publishers = null) {
    const params = { limit }
    if (tickers) {
      params.tickers = tickers.join(',')
    }
    if (publishers && publishers.length > 0) {
      params.publishers = publishers.join(',')
    }
    return api.get('/news', { params })
  },
  
  getTickerNews(ticker, limit = 20, publishers = null) {
    const params = { limit }
    if (publishers && publishers.length > 0) {
      params.publishers = publishers.join(',')
    }
    return api.get(`/news/${ticker}`, { params })
  },
  
  getNewsPublishers() {
    return api.get('/news/publishers')
  },
  
  // AI endpoints
  analyzeNews(newsItem) {
    return api.post('/analyze', newsItem)
  },
  
  // Earnings endpoints
  getEarnings(startDate = null, weeks = 1, offset = 0) {
    const params = { weeks, offset }
    if (startDate) {
      params.start_date = startDate
    }
    return api.get('/earnings', { params })
  },
  
  getTickerEarnings(ticker) {
    return api.get(`/earnings/${ticker}`)
  },
}

