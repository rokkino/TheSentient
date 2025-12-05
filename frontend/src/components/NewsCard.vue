<template>
  <div class="news-card" @click="openLink">
    <div class="news-title">{{ newsItem.title }}</div>
    <div class="news-info">
      {{ newsItem.publisher }} ({{ newsItem.ticker }}) - {{ formatTime(newsItem.timestamp) }}
    </div>
    <div class="news-text">{{ newsItem.text }}</div>
    
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
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

const openLink = () => {
  if (props.newsItem.link) {
    window.open(props.newsItem.link, '_blank')
  }
}
</script>

<style scoped>
.news-card {
  background-color: #2d2d2d;
  border: 1px solid #444;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.news-card:hover {
  background-color: #3a3a3a;
  border-color: #555;
  transform: translateY(-2px);
}

.news-title {
  font-size: 16px;
  font-weight: bold;
  color: #f0f0f0;
  margin-bottom: 8px;
}

.news-info {
  font-size: 12px;
  color: #888;
  font-style: italic;
  margin-bottom: 8px;
}

.news-text {
  font-size: 15px;
  color: #d0d0d0;
  line-height: 1.6;
  margin-bottom: 10px;
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

