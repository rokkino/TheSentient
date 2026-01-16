<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <div class="header-left">
          <span class="publisher-badge">{{ newsItem?.publisher || 'News' }}</span>
          <span class="date-badge" v-if="newsItem?.providerPublishTime">{{ formatDate(newsItem.providerPublishTime) }}</span>
        </div>
        <button class="close-btn" @click="close">&times;</button>
      </div>
      
      <div class="modal-body" v-if="newsItem">
        <div class="news-hero" v-if="newsItem.thumbnail">
          <img :src="newsItem.thumbnail" alt="News Image" @error="handleImageError" />
          <div class="hero-overlay"></div>
        </div>

        <h2 class="news-title">{{ newsItem.title }}</h2>
        
        <div class="news-meta">
          <span v-for="ticker in newsItem.relatedTickers" :key="ticker" class="ticker-tag">{{ ticker }}</span>
        </div>

        <div class="news-text">
          <div v-if="loading" class="loading-content">
            <div class="spinner"></div>
            <span>Fetching full article...</span>
          </div>
          <div v-else class="article-content">
            <template v-if="formattedText.length > 0">
              <p v-for="(paragraph, index) in formattedText" :key="index">{{ paragraph }}</p>
            </template>
            <p v-else>No content available.</p>
          </div>
        </div>

        <div class="news-actions">
          <button class="action-btn primary" @click="$emit('ask-ai', newsItem)">
            <span class="icon">🤖</span> Ask AI
          </button>
          <a :href="newsItem.link" target="_blank" class="action-btn secondary">
            <span class="icon">🔗</span> Read Original
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, ref, watch, computed } from 'vue'
import api from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  newsItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'ask-ai'])

const loading = ref(false)
const fullContent = ref('')

const formattedText = computed(() => {
  const text = fullContent.value || props.newsItem?.text || props.newsItem?.summary || 'No content available.'
  console.log('Computing formattedText. Source length:', text.length)
  // Split by one or more newlines to be safer
  const paragraphs = text.split(/\n+/).map(p => p.trim()).filter(p => p.length > 0)
  console.log('Formatted paragraphs:', paragraphs.length)
  return paragraphs
})

watch(() => props.newsItem, async (newItem) => {
  if (newItem && props.show) {
    await loadContent(newItem)
  }
}, { immediate: true })

watch(() => props.show, async (show) => {
  if (show && props.newsItem) {
    await loadContent(props.newsItem)
  }
})

const loadContent = async (item) => {
  // Reset
  fullContent.value = ''
  
  // If text is short (likely just summary) and we have a link, try to fetch full content
  const currentText = item.text || item.summary || ''
  if (currentText.length < 500 && item.link) {
    loading.value = true
    try {
      const response = await api.fetchNewsContent(item.link)
      if (response.data.content && response.data.content.length > currentText.length) {
        fullContent.value = response.data.content
      }
    } catch (e) {
      console.error('Error fetching full content:', e)
    } finally {
      loading.value = false
    }
  }
}

const close = () => {
  emit('close')
  fullContent.value = ''
}

const formatDate = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp * 1000).toLocaleString()
}

const handleImageError = (e) => {
  e.target.style.display = 'none'
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease-out;
}

.modal-content {
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(26, 26, 26, 0.95);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
}

.header-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.publisher-badge {
  background: #2d3748;
  color: #a0aec0;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.date-badge {
  color: #718096;
  font-size: 12px;
}

.close-btn {
  background: none;
  border: none;
  color: #718096;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 0;
}

.news-hero {
  position: relative;
  width: 100%;
  height: 300px;
  overflow: hidden;
}

.news-hero img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100px;
  background: linear-gradient(to top, #1a1a1a, transparent);
}

.news-title {
  padding: 24px 24px 16px;
  margin: 0;
  font-size: 28px;
  line-height: 1.3;
  color: #fff;
  font-weight: 700;
}

.news-meta {
  padding: 0 24px 20px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ticker-tag {
  background: rgba(66, 153, 225, 0.15);
  color: #63b3ed;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid rgba(66, 153, 225, 0.2);
}

.news-text {
  padding: 0 24px 30px;
  font-size: 16px;
  line-height: 1.7;
  color: #d1d5db;
}

.news-actions {
  padding: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  gap: 16px;
  background: rgba(255, 255, 255, 0.02);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  border: none;
}

.action-btn.primary {
  background: #4299e1;
  color: #fff;
}

.action-btn.primary:hover {
  background: #3182ce;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.05);
  color: #a0aec0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(40px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .news-hero {
    height: 200px;
  }
  
  .news-title {
    font-size: 22px;
  }
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #718096;
  gap: 16px;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.article-content p {
  margin-bottom: 16px;
  line-height: 1.8;
}
</style>
