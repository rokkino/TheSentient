import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies in requests
  timeout: 120000, // 120 second timeout (increased for AI + Web Search)
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't redirect if it's a login attempt that failed
      // And don't redirect if we're already on the home page (to avoid infinite loops)
      if (!error.config.url.includes('/auth/login') && window.location.pathname !== '/') {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/'
      }
    }
    return Promise.reject(error)
  }
)

export default {
  // Chart endpoints
  getChart(data) {
    return api.post('/chart', data)
  },

  analyzeChart(data) {
    return api.post('/chart/analyze', data)
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

  fetchNewsContent(url) {
    return api.post('/news/fetch-content', { url })
  },

  // AI endpoints
  analyzeNews(newsItem) {
    return api.post('/analyze', newsItem)
  },

  // Earnings endpoints - Now uses months (6-month blocks) instead of weeks
  getEarnings(startDate = null, months = 6, offsetMonths = 0, endDate = null) {
    console.log('🌐 API.getEarnings called:', { startDate, months, offsetMonths, endDate })
    const params = { months, offset_months: offsetMonths }
    if (startDate) {
      params.start_date = startDate
    }
    if (endDate) {
      params.end_date = endDate
    }
    console.log('🌐 API.getEarnings params:', params)
    return api.get('/earnings', { params, timeout: 300000 }) // 5 minute timeout for 6 months of data
  },

  askLlamaAboutEarning(symbol, company, date, question = null, provider = 'local') {
    return api.post('/earnings/ask', { symbol, company, date, question, provider })
  },

  askLlamaAboutNews(newsItem, question) {
    return api.post('/news/ask', {
      title: newsItem.title,
      text: newsItem.text || newsItem.summary,
      ticker: newsItem.ticker,
      publisher: newsItem.publisher,
      date: newsItem.timestamp,
      question
    })
  },

  getTickerEarnings(ticker) {
    return api.get(`/earnings/${ticker}`)
  },

  getTickerEpsHistory(ticker, years = 2) {
    return api.get(`/earnings/${ticker}/eps-history`, { params: { years } })
  },

  getStockFinancials(ticker) {
    return api.get(`/stock/${ticker}/financials`)
  },

  // Auth endpoints
  login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    // Don't set Content-Type manually - let axios set it with the correct boundary
    return api.post('/auth/login', formData)
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
      // Let axios set Content-Type automatically with correct boundary
      headers: {},
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
  getChatMessages(limit = 100, recipientId = null) {
    const params = { limit }
    if (recipientId) params.recipient_id = recipientId
    return api.get('/chat/messages', { params })
  },

  sendChatMessage(messageData) {
    return api.post('/chat/message', messageData)
  },

  deleteChatMessage(messageId) {
    return api.delete(`/chat/message/${messageId}`)
  },

  clearChatHistory(recipientId = null) {
    const params = {}
    if (recipientId) params.recipient_id = recipientId
    return api.delete('/chat/history', { params })
  },

  // User tabs endpoints
  getUserTabs() {
    return api.get('/user/tabs')
  },

  saveUserTabs(tabs) {
    return api.put('/user/tabs', { tabs })
  },

  // Bot endpoints
  createBot(botData) {
    return api.post('/bots', botData)
  },

  getBots() {
    return api.get('/bots')
  },

  getPublicBots() {
    return api.get('/bots/public')
  },

  getBot(botId) {
    return api.get(`/bots/${botId}`)
  },

  updateBotConfig(botId, config) {
    return api.put(`/bots/${botId}/config`, config)
  },

  activateBot(botId) {
    return api.post(`/bots/${botId}/activate`)
  },

  deactivateBot(botId) {
    return api.post(`/bots/${botId}/deactivate`)
  },

  deleteBot(botId) {
    return api.delete(`/bots/${botId}`)
  },

  exportBot(botId) {
    return api.get(`/bots/${botId}/export`)
  },

  importBot(importData) {
    return api.post('/bots/import', importData)
  },

  importBotConfig(botId, importData) {
    return api.post(`/bots/${botId}/import`, importData)
  },

  callLlama(botId, data = null) {
    return api.post(`/bots/${botId}/call/llama`, data)
  },

  callGemini(botId) {
    return api.post(`/bots/${botId}/call/gemini`)
  },

  // Strategy endpoints
  getStrategies() {
    return api.get('/strategies')
  },

  createStrategy(strategyData) {
    return api.post('/strategies', strategyData)
  },

  updateStrategy(strategyId, strategyData) {
    return api.put(`/strategies/${strategyId}`, strategyData)
  },

  deleteStrategy(strategyId) {
    return api.delete(`/strategies/${strategyId}`)
  },

  generateStrategy(prompt) {
    return api.post('/strategies/generate', { prompt })
  },
}
