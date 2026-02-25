<template>
  <div class="news-card" :class="[variant, { 'has-image': !!newsItem.thumbnail }]" @click="handleClick">
    <div class="card-glow"></div>
    
    <div v-if="newsItem.thumbnail" class="news-image-container">
      <img :src="newsItem.thumbnail" alt="News thumbnail" @error="handleImageError" />
      <div class="image-overlay"></div>
      <div class="news-badges">
        <span class="publisher-badge">
          {{ newsItem.publisher || 'Yahoo Finance' }}
        </span>
        <span class="time-badge">{{ formatTime(newsItem.providerPublishTime || newsItem.timestamp) }}</span>
      </div>
    </div>
    
    <div class="news-content">
      <div v-if="!newsItem.thumbnail" class="news-header">
        <span class="publisher-badge">{{ newsItem.publisher || 'Yahoo Finance' }}</span>
        <span class="time-badge">{{ formatTime(newsItem.providerPublishTime || newsItem.timestamp) }}</span>
      </div>
      
      <!-- Sentiment Badge -->
      <div v-if="newsItem.sentiment" class="sentiment-badge" :class="newsItem.sentiment">
        <span class="sentiment-icon">{{ getSentimentIcon(newsItem.sentiment) }}</span>
        <span class="sentiment-text">{{ getSentimentLabel(newsItem.sentiment) }}</span>
      </div>
      
      <!-- Assets/Tickers -->
      <div class="news-tags" v-if="getDisplayAssets().length > 0">
        <span v-for="asset in getDisplayAssets()" :key="asset" class="ticker-tag">
          {{ asset }}
        </span>
      </div>
      
      <h3 class="news-title">{{ newsItem.title }}</h3>
      <p class="news-summary">{{ newsItem.summary || newsItem.text }}</p>
      
      <!-- Trading Signal (if available) -->
      <div v-if="newsItem.signal" class="trading-signal" :class="newsItem.signal.direction">
        <div class="signal-header">
          <span class="signal-direction">{{ newsItem.signal.direction }}</span>
          <span class="signal-confidence">{{ newsItem.signal.confidence }}% Confidence</span>
        </div>
        <div class="signal-details">
          <div class="signal-metric">
            <span class="label">Impact:</span>
            <span class="value">{{ newsItem.signal.impact }}</span>
          </div>
          <div class="signal-metric">
            <span class="label">Horizon:</span>
            <span class="value">{{ newsItem.signal.horizon }}</span>
          </div>
        </div>
      </div>
      
      <div class="card-actions">
        <button class="ask-ai-btn" @click.stop="$emit('ask-ai', newsItem)">
          <span class="icon">✨</span> Ask AI
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>

const props = defineProps({
  newsItem: {
    type: Object,
    required: true
  },
  variant: {
    type: String,
    default: 'default'
  }
})

const emit = defineEmits(['ask-ai', 'click'])

const handleClick = () => {
  emit('click', props.newsItem)
}

const handleImageError = (e) => {
  e.target.style.display = 'none'
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  // Handle both Unix timestamp (number) and ISO string
  const date = typeof timestamp === 'number' ? new Date(timestamp * 1000) : new Date(timestamp)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000) // seconds
  
  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

const getDisplayAssets = () => {
  // Prefer extracted_assets, fallback to relatedTickers, then ticker
  const assets = props.newsItem.extracted_assets || props.newsItem.relatedTickers || []
  if (assets.length > 0) {
    return assets.slice(0, 5) // Show up to 5 assets
  }
  // Fallback to ticker if available
  if (props.newsItem.ticker) {
    return [props.newsItem.ticker]
  }
  return []
}

const getSentimentIcon = (sentiment) => {
  switch(sentiment?.toLowerCase()) {
    case 'positive': return '📈'
    case 'negative': return '📉'
    case 'neutral': return '➡️'
    default: return ''
  }
}

const getSentimentLabel = (sentiment) => {
  switch(sentiment?.toLowerCase()) {
    case 'positive': return 'Positiva'
    case 'negative': return 'Negativa'
    case 'neutral': return 'Neutrale'
    default: return ''
  }
}
</script>

<style scoped>
.news-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  display: flex;
  flex-direction: column;
  break-inside: avoid;
}

.news-card:hover {
  transform: translateY(-4px);
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(66, 153, 225, 0.5), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.news-card:hover .card-glow {
  opacity: 1;
}

.news-image-container {
  height: 180px;
  position: relative;
  overflow: hidden;
}

.news-image-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.news-card:hover .news-image-container img {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, transparent 50%, rgba(0, 0, 0, 0.8));
}

.news-badges {
  position: absolute;
  bottom: 12px;
  left: 12px;
  right: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.publisher-badge {
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.time-badge {
  font-size: 10px;
  color: #cbd5e0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  font-weight: 500;
}

.news-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.news-title {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  color: #fff;
}

.news-card.hero .news-title {
  font-size: 24px;
}

.news-tags {
  margin-bottom: 10px;
}

.sentiment-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
  border: 1px solid;
}

.sentiment-badge.positive {
  background: rgba(40, 167, 69, 0.15);
  color: #4cd168;
  border-color: rgba(40, 167, 69, 0.3);
}

.sentiment-badge.negative {
  background: rgba(220, 53, 69, 0.15);
  color: #ff6b6b;
  border-color: rgba(220, 53, 69, 0.3);
}

.sentiment-badge.neutral {
  background: rgba(108, 117, 125, 0.15);
  color: #adb5bd;
  border-color: rgba(108, 117, 125, 0.3);
}

.sentiment-icon {
  font-size: 14px;
}

.sentiment-text {
  font-size: 10px;
}

.ticker-tag {
  display: inline-block;
  background: rgba(66, 153, 225, 0.15);
  color: #63b3ed;
  font-size: 10px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid rgba(66, 153, 225, 0.2);
  margin-right: 6px;
  margin-bottom: 4px;
}

.news-summary {
  font-size: 13px;
  color: #b0b0b0;
  line-height: 1.6;
  margin: 0 0 12px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Trading Signal Styles */
.trading-signal {
  margin-top: 12px;
  padding: 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.trading-signal.bullish {
  background: linear-gradient(90deg, rgba(40, 167, 69, 0.1), transparent);
  border-left: 3px solid #28a745;
}

.trading-signal.bearish {
  background: linear-gradient(90deg, rgba(220, 53, 69, 0.1), transparent);
  border-left: 3px solid #dc3545;
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.signal-direction {
  font-weight: 800;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.bullish .signal-direction { color: #4cd168; }
.bearish .signal-direction { color: #ff6b6b; }

.signal-confidence {
  font-size: 10px;
  color: #888;
}

.signal-details {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.signal-metric {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.signal-metric .label {
  color: #666;
  font-weight: 600;
}

.signal-metric .value {
  color: #ddd;
  font-family: 'Roboto Mono', monospace;
}

.card-actions {
  margin-top: auto;
  padding-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.ask-ai-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a0aec0;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ask-ai-btn:hover {
  background: rgba(66, 153, 225, 0.15);
  color: #63b3ed;
  border-color: rgba(66, 153, 225, 0.3);
}

/* Hero Variant Overrides */
.news-card.hero {
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(35, 35, 35, 0.6);
}

.news-card.hero .news-image-container {
  height: 380px;
}

.news-card.hero .news-title {
  font-size: 28px;
  margin-bottom: 16px;
  line-height: 1.3;
}

.news-card.hero .news-summary {
  font-size: 15px;
  -webkit-line-clamp: 4;
}

@media (max-width: 768px) {
  .news-card {
    border-radius: 16px;
    margin-bottom: 18px;
    background: rgba(18, 18, 20, 0.9);
    border-color: rgba(255, 255, 255, 0.08);
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
  }

  .news-content {
    padding: 14px 16px 16px;
  }

  .news-image-container {
    height: 160px;
  }

  .news-card.hero .news-image-container {
    height: 240px;
  }

  .news-title {
    font-size: 15px;
    line-height: 1.35;
  }

  .news-card.hero .news-title {
    font-size: 20px;
  }

  .news-summary {
    font-size: 13px;
    -webkit-line-clamp: 4;
  }

  .ticker-tag {
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 999px;
  }

  .ask-ai-btn {
    min-height: 34px;
    padding: 8px 14px;
  }
}

@media (max-width: 480px) {
  .news-card {
    border-radius: 18px;
    margin-bottom: 16px;
  }

  .news-content {
    padding: 12px 14px 14px;
  }

  .news-image-container {
    height: 150px;
  }

  .news-card.hero .news-image-container {
    height: 210px;
  }

  .news-title {
    font-size: 14px;
  }

  .news-summary {
    font-size: 12.5px;
    -webkit-line-clamp: 3;
  }

  .publisher-badge,
  .time-badge {
    font-size: 9px;
  }

  .sentiment-badge {
    padding: 5px 10px;
    font-size: 10px;
  }

  .ask-ai-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
