<template>
  <div class="news-card" @click="openLink">
    <div class="news-header">
      <div class="news-title">{{ newsItem.title || 'No title' }}</div>
      <div class="news-meta">
        <span class="news-publisher">{{ newsItem.publisher || 'Yahoo Finance' }}</span>
        <span class="news-ticker">{{ formatTicker(newsItem.ticker) }}</span>
        <span class="news-time">{{ formatTime(newsItem.timestamp) }}</span>
      </div>
    </div>
    <div v-if="newsItem.text && newsItem.text !== newsItem.title" class="news-text">{{ newsItem.text }}</div>
    
    <div v-if="newsItem.trading_signal" class="trading-signal" :class="signalClass">
      <div class="signal-label">
        {{ newsItem.trading_signal.direction }} - Confidence: {{ newsItem.trading_signal.confidence }}%
      </div>
      <div v-if="newsItem.trading_signal.stop_loss && newsItem.trading_signal.take_profit" class="signal-info">
        Stop Loss: {{ newsItem.trading_signal.stop_loss }}<br>
        Take Profit: {{ newsItem.trading_signal.take_profit }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  newsItem: {
    type: Object,
    required: true
  }
})

const signalClass = computed(() => {
  if (props.newsItem.trading_signal?.direction === 'BEARISH') {
    return 'bearish'
  }
  return 'bullish'
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return ''
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return ''
  }
}

const formatTicker = (ticker) => {
  if (!ticker) return ''
  // Replace = with - for futures, remove ^ for indices
  return ticker.replace('=', '-').replace('^', '')
}

const openLink = () => {
  if (props.newsItem.link) {
    window.open(props.newsItem.link, '_blank')
  }
}
</script>

<style scoped>
.news-card {
  background: rgba(26, 26, 26, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.news-card:hover {
  background: rgba(26, 26, 26, 0.95);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.news-header {
  margin-bottom: 12px;
}

.news-title {
  font-size: 17px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 10px;
  line-height: 1.4;
  letter-spacing: -0.2px;
}

.news-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #9ca3af;
}

.news-publisher {
  font-weight: 500;
  color: #d1d5db;
}

.news-ticker {
  background: rgba(66, 153, 225, 0.15);
  color: #4299e1;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.5px;
}

.news-time {
  color: #6b7280;
  font-weight: 400;
}

.news-text {
  font-size: 14px;
  color: #d1d5db;
  line-height: 1.6;
  margin-top: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.trading-signal {
  background-color: #2a4a2a;
  border: 1px solid #3a6a3a;
  border-radius: 8px;
  padding: 10px;
  margin-top: 10px;
}

.trading-signal.bearish {
  background-color: #4a2a2a;
  border-color: #6a3a3a;
}

.signal-label {
  font-size: 13px;
  font-weight: bold;
  color: #90ee90;
  margin-bottom: 6px;
}

.trading-signal.bearish .signal-label {
  color: #ff6b6b;
}

.signal-info {
  font-size: 12px;
  color: #b0b0b0;
  line-height: 1.5;
}
</style>

