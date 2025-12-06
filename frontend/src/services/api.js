import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies in requests
  timeout: 30000, // 30 second timeout (increased for database operations)
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default {
  // Chart endpoints
  getChart(data) {
    return api.post('/chart', data)
  },
  
  getQuote(ticker, timeframe = '1d') {
    return api.get(`/quote/${ticker}`, { params: { timeframe } })
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
    return api.get('/earnings', { params, timeout: 30000 }) // 30 second timeout for earnings
  },
  
  getTickerEarnings(ticker) {
    return api.get(`/earnings/${ticker}`)
  },
  
  // Auth endpoints
  login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    return api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  
  register(username, email, password) {
    return api.post('/auth/register', {
      username,
      email,
      password,
    })
  },
  
  logout() {
    return api.post('/auth/logout')
  },
  
  getCurrentUser() {
    return api.get('/auth/me')
  },
  
  updateProfile(profileData) {
    return api.put('/auth/profile', profileData)
  },

  uploadProfilePicture(fileFormData) {
    return api.post('/auth/profile/picture', fileFormData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // Alpaca Paper Trading endpoints
  getAlpacaAccount() {
    return api.get('/alpaca/account')
  },

  getAlpacaPositions() {
    return api.get('/alpaca/positions')
  },

  getAlpacaOrders(status = null, limit = 50) {
    const params = { limit }
    if (status) params.status = status
    return api.get('/alpaca/orders', { params })
  },

  placeAlpacaOrder(orderData) {
    return api.post('/alpaca/orders', orderData)
  },

  cancelAlpacaOrder(orderId) {
    return api.delete(`/alpaca/orders/${orderId}`)
  },

  cancelAllAlpacaOrders() {
    return api.delete('/alpaca/orders')
  },

  getAlpacaPortfolioHistory(period = '1M', timeframe = '1Day') {
    return api.get('/alpaca/portfolio/history', { params: { period, timeframe } })
  },
  
  // Chat endpoints
  getChatMessages(limit = 100) {
    return api.get('/chat/messages', { params: { limit } })
  },
  
  sendChatMessage(messageData) {
    return api.post('/chat/message', messageData)
  },
}

