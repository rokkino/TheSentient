/**
 * Cache utility for storing and retrieving cached data with TTL
 */

const CACHE_PREFIX = 'thesentient_cache_'
const CACHE_TTL = {
  chart: 5 * 60 * 1000, // 5 minutes for chart data
  news: 10 * 60 * 1000, // 10 minutes for news
  news_store: 10 * 60 * 1000, // 10 minutes for news store
  earnings: 60 * 60 * 1000, // 60 minutes (1 hour) for earnings - they don't change frequently
}

/**
 * Generate cache key
 */
function getCacheKey(type, ...params) {
  return `${CACHE_PREFIX}${type}_${params.join('_')}`
}

/**
 * Get cached data if not expired
 */
export function getCached(type, ...params) {
  try {
    const key = getCacheKey(type, ...params)
    const cached = localStorage.getItem(key)
    if (!cached) return null
    
    const { data, timestamp, ttl } = JSON.parse(cached)
    const now = Date.now()
    
    // Check if cache is expired
    if (now - timestamp > ttl) {
      localStorage.removeItem(key)
      return null
    }
    
    return data
  } catch (error) {
    console.error('Error reading cache:', error)
    return null
  }
}

/**
 * Set cached data with TTL
 */
export function setCached(type, data, ...params) {
  try {
    const key = getCacheKey(type, ...params)
    const ttl = CACHE_TTL[type] || 5 * 60 * 1000
    const cacheEntry = {
      data,
      timestamp: Date.now(),
      ttl
    }
    localStorage.setItem(key, JSON.stringify(cacheEntry))
  } catch (error) {
    console.error('Error writing cache:', error)
    // If storage is full, try to clear old cache entries
    if (error.name === 'QuotaExceededError') {
      clearOldCache()
      // Retry once
      try {
        localStorage.setItem(key, JSON.stringify(cacheEntry))
      } catch (retryError) {
        console.error('Failed to cache after cleanup:', retryError)
      }
    }
  }
}

/**
 * Clear old cache entries
 */
function clearOldCache() {
  const now = Date.now()
  const keysToRemove = []
  
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key && key.startsWith(CACHE_PREFIX)) {
      try {
        const cached = localStorage.getItem(key)
        const { timestamp, ttl } = JSON.parse(cached)
        if (now - timestamp > ttl) {
          keysToRemove.push(key)
        }
      } catch (e) {
        // Invalid cache entry, remove it
        keysToRemove.push(key)
      }
    }
  }
  
  keysToRemove.forEach(key => localStorage.removeItem(key))
  console.log(`Cleared ${keysToRemove.length} expired cache entries`)
}

/**
 * Clear all cache
 */
export function clearCache(type = null) {
  if (type) {
    // Clear specific type
    const prefix = getCacheKey(type, '')
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i)
      if (key && key.startsWith(prefix)) {
        localStorage.removeItem(key)
      }
    }
  } else {
    // Clear all cache
    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i)
      if (key && key.startsWith(CACHE_PREFIX)) {
        localStorage.removeItem(key)
      }
    }
  }
}

/**
 * Save indicator settings for a ticker
 */
export function saveIndicatorSettings(ticker, settings) {
  try {
    const key = `indicator_settings_${ticker}`
    localStorage.setItem(key, JSON.stringify(settings))
  } catch (error) {
    console.error('Error saving indicator settings:', error)
  }
}

/**
 * Load indicator settings for a ticker
 */
export function loadIndicatorSettings(ticker) {
  try {
    const key = `indicator_settings_${ticker}`
    const saved = localStorage.getItem(key)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (error) {
    console.error('Error loading indicator settings:', error)
  }
  return null
}

