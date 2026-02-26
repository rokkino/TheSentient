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
  background: var(--glass-bg, rgba(30, 41, 59, 0.5));
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-md, 16px);
  overflow: hidden;
  margin-bottom: 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  display: flex;
  flex-direction: column;
  break-inside: avoid;
  box-shadow: var(--shadow-card, 0 8px 32px rgba(0, 0, 0, 0.35));
}

.news-card:hover {
  transform: translateY(-4px);
  border-color: var(--glass-border-hover, rgba(255, 255, 255, 0.2));
  box-shadow: var(--shadow-glass, 0 25px 50px -12px rgba(0, 0, 0, 0.5));
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(52, 211, 153, 0.5), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 1;
}

.news-card:hover .card-glow {
  opacity: 1;
}

/* ── Image with fixed aspect-ratio ── */
.news-image-container {
  position: relative;
  overflow: hidden;
  aspect-ratio: 16 / 9;
}

.news-image-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.news-card:hover .news-image-container img {
  transform: scale(1.05);
}

/* ── Dark gradient overlay for title legibility ── */
.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.85) 0%,
    rgba(0, 0, 0, 0.4) 40%,
    transparent 60%
  );
}

.news-badges {
  position: absolute;
  bottom: 12px;
  left: 14px;
  right: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 2;
}

.publisher-badge {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  padding: 5px 10px;
  border-radius: var(--radius-full, 9999px);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-primary, #e2e8f0);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.time-badge {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.7);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
  font-weight: 500;
}

.news-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.news-title {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.45;
  color: var(--text-white, #ffffff);
  letter-spacing: -0.02em;
}

.news-card.hero .news-title {
  font-size: 24px;
}

.news-tags {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* ── Sentiment pills — rounded-full, translucent pastel ── */
.sentiment-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border-radius: var(--radius-full, 9999px);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 12px;
  border: 1px solid;
}

.sentiment-badge.positive {
  background: var(--accent-gain-bg, rgba(52, 211, 153, 0.15));
  color: var(--accent-gain, #34d399);
  border-color: rgba(52, 211, 153, 0.25);
}

.sentiment-badge.negative {
  background: var(--accent-loss-bg, rgba(244, 63, 94, 0.15));
  color: var(--accent-loss, #f43f5e);
  border-color: rgba(244, 63, 94, 0.25);
}

.sentiment-badge.neutral {
  background: rgba(148, 163, 184, 0.12);
  color: var(--text-secondary, #94a3b8);
  border-color: rgba(148, 163, 184, 0.2);
}

.sentiment-icon {
  font-size: 13px;
}

.sentiment-text {
  font-size: 10px;
}

.ticker-tag {
  display: inline-block;
  background: var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
  color: #60a5fa;
  font-size: 10px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-full, 9999px);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.news-summary {
  font-size: 13px;
  color: var(--text-secondary, #94a3b8);
  line-height: 1.7;
  margin: 0 0 14px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Trading Signal ── */
.trading-signal {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-sm, 8px);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
}

.trading-signal.bullish {
  background: linear-gradient(90deg, var(--accent-gain-bg, rgba(52, 211, 153, 0.15)), transparent);
  border-left: 3px solid var(--accent-gain, #34d399);
}

.trading-signal.bearish {
  background: linear-gradient(90deg, var(--accent-loss-bg, rgba(244, 63, 94, 0.15)), transparent);
  border-left: 3px solid var(--accent-loss, #f43f5e);
}

.signal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.signal-direction {
  font-weight: 700;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.bullish .signal-direction { color: var(--accent-gain, #34d399); }
.bearish .signal-direction { color: var(--accent-loss, #f43f5e); }

.signal-confidence {
  font-size: 10px;
  color: var(--text-muted, #64748b);
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
  color: var(--text-muted, #64748b);
  font-weight: 600;
}

.signal-metric .value {
  color: var(--text-primary, #e2e8f0);
  font-family: 'Inter', sans-serif;
}

.card-actions {
  margin-top: auto;
  padding-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.ask-ai-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  color: var(--text-secondary, #94a3b8);
  padding: 7px 14px;
  border-radius: var(--radius-full, 9999px);
  font-size: 11px;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ask-ai-btn:hover {
  background: var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.3);
}

/* ── Hero Variant ── */
.news-card.hero {
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.news-card.hero .news-image-container {
  aspect-ratio: 21 / 9;
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

/* ── Mobile ── */
@media (max-width: 768px) {
  .news-card {
    border-radius: var(--radius-md, 16px);
    margin-bottom: 18px;
  }

  .news-content {
    padding: 16px;
  }

  .news-image-container {
    aspect-ratio: 16 / 9;
  }

  .news-card.hero .news-image-container {
    aspect-ratio: 16 / 9;
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
  }

  .ask-ai-btn {
    min-height: 34px;
    padding: 8px 14px;
  }
}

@media (max-width: 480px) {
  .news-card {
    border-radius: var(--radius-md, 16px);
    margin-bottom: 16px;
  }

  .news-content {
    padding: 14px;
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
