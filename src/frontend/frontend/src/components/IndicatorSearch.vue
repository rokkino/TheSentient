<template>
  <div class="indicator-search" ref="containerRef">
    <div class="search-wrapper" :class="{ focused: isFocused }">
      <div class="selected-indicators" v-if="selectedIndicators.length > 0">
        <span 
          v-for="(indicator, index) in selectedIndicators" 
          :key="index" 
          class="indicator-chip"
        >
          {{ indicator.label }}
          <button @click.stop="removeIndicator(index)" class="remove-chip">×</button>
        </span>
      </div>
      
      <input
        ref="inputRef"
        v-model="query"
        @focus="handleFocus"
        @blur="handleBlur"
        @input="handleInput"
        @keydown.down.prevent="navigateResults(1)"
        @keydown.up.prevent="navigateResults(-1)"
        @keydown.enter.prevent="handleEnter"
        @keydown.backspace="handleBackspace"
        :placeholder="selectedIndicators.length === 0 ? 'Search indicators (RSI, MACD) or ask AI...' : 'Add more...'"
        class="search-input"
        :disabled="loading"
      />
      
      <div v-if="loading" class="loading-spinner"></div>
      <div v-else-if="query.length > 0" class="ai-hint" @click="triggerAI">
        <span>✨ Ask AI</span>
      </div>
    </div>

    <!-- Dropdown Menu -->
    <div v-if="showDropdown" class="dropdown-menu">
      <div v-if="filteredIndicators.length === 0" class="no-results">
        <div class="ai-option" :class="{ active: selectedIndex === 0 }" @click="triggerAI">
          <span class="ai-icon">✨</span>
          <div class="ai-text">
            <span class="ai-title">Ask AI to analyze</span>
            <span class="ai-query">"{{ query }}"</span>
          </div>
        </div>
      </div>
      
      <div v-else class="results-list">
        <div 
          v-for="(item, index) in filteredIndicators" 
          :key="item.value"
          class="result-item"
          :class="{ active: index === selectedIndex }"
          @click="selectIndicator(item)"
          @mouseenter="selectedIndex = index"
        >
          <span class="item-label">{{ item.label }}</span>
          <span class="item-desc">{{ item.description }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['analyze', 'add-indicator'])

const containerRef = ref(null)
const inputRef = ref(null)
const query = ref('')
const isFocused = ref(false)
const showDropdown = ref(false)
const selectedIndex = ref(0)
const selectedIndicators = ref([])

const commonIndicators = [
  { label: 'RSI', value: 'RSI', description: 'Relative Strength Index' },
  { label: 'MACD', value: 'MACD', description: 'Moving Average Convergence Divergence' },
  { label: 'Bollinger Bands', value: 'BB', description: 'Volatility bands' },
  { label: 'SMA', value: 'SMA', description: 'Simple Moving Average' },
  { label: 'EMA', value: 'EMA', description: 'Exponential Moving Average' },
  { label: 'Volume', value: 'VOL', description: 'Trading Volume' },
  { label: 'Stochastic', value: 'STOCH', description: 'Stochastic Oscillator' }
]

const filteredIndicators = computed(() => {
  if (!query.value) return commonIndicators
  const q = query.value.toLowerCase()
  return commonIndicators.filter(i => 
    i.label.toLowerCase().includes(q) || 
    i.description.toLowerCase().includes(q)
  )
})

const handleFocus = () => {
  isFocused.value = true
  showDropdown.value = true
}

const handleBlur = () => {
  // Delay hiding to allow click events to process
  setTimeout(() => {
    isFocused.value = false
    showDropdown.value = false
  }, 200)
}

const handleInput = () => {
  showDropdown.value = true
  selectedIndex.value = 0
}

const navigateResults = (direction) => {
  if (!showDropdown.value) {
    showDropdown.value = true
    return
  }
  
  const maxIndex = filteredIndicators.value.length > 0 
    ? filteredIndicators.value.length - 1 
    : 0 // For AI option
    
  let newIndex = selectedIndex.value + direction
  if (newIndex < 0) newIndex = maxIndex
  if (newIndex > maxIndex) newIndex = 0
  
  selectedIndex.value = newIndex
}

const handleEnter = () => {
  if (filteredIndicators.value.length > 0) {
    selectIndicator(filteredIndicators.value[selectedIndex.value])
  } else {
    triggerAI()
  }
}

const handleBackspace = (e) => {
  if (query.value === '' && selectedIndicators.value.length > 0) {
    selectedIndicators.value.pop()
  }
}

const selectIndicator = (indicator) => {
  // Add to local selection
  selectedIndicators.value.push(indicator)
  query.value = ''
  inputRef.value.focus()
  
  // Emit event to add specific indicator immediately if desired, 
  // or wait for a "Apply" action. For now, let's emit immediately.
  // Actually, for the AI flow, we might want to batch them.
  // But the current backend expects a natural language query OR we can construct one.
  
  // Let's construct a synthetic query for the selected indicators
  // Or better, emit a specific event for known indicators
  // But to keep it compatible with the existing AI endpoint, we can just send "Add RSI" etc.
  
  // However, the requirement is to support "pull down menu".
  // If we select from menu, we should probably just add it directly if we can, 
  // but the backend logic is tied to "analyze".
  
  // Let's trigger analysis for the added indicator
  emit('analyze', `Add ${indicator.value}`)
}

const removeIndicator = (index) => {
  selectedIndicators.value.splice(index, 1)
}

const triggerAI = () => {
  if (!query.value.trim()) return
  emit('analyze', query.value)
  query.value = ''
  showDropdown.value = false
}

// Close dropdown when clicking outside
const handleClickOutside = (e) => {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.indicator-search {
  position: relative;
  width: 100%;
  font-family: 'Roboto Mono', monospace;
}

.search-wrapper {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
  background-color: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  padding: 4px 8px;
  min-height: 36px;
  transition: border-color 0.2s;
}

.search-wrapper.focused {
  border-color: #2196F3;
}

.selected-indicators {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.indicator-chip {
  display: flex;
  align-items: center;
  background-color: #2c3e50;
  color: #fff;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid #34495e;
}

.remove-chip {
  background: none;
  border: none;
  color: #95a5a6;
  margin-left: 4px;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0;
}

.remove-chip:hover {
  color: #e74c3c;
}

.search-input {
  flex: 1;
  min-width: 120px;
  background: none;
  border: none;
  color: #fff;
  font-size: 12px;
  outline: none;
  padding: 4px 0;
}

.search-input::placeholder {
  color: #666;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #333;
  border-top-color: #2196F3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.ai-hint {
  cursor: pointer;
  color: #2196F3;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  background-color: rgba(33, 150, 243, 0.1);
}

.ai-hint:hover {
  background-color: rgba(33, 150, 243, 0.2);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  margin-top: 4px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.result-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-item:hover, .result-item.active {
  background-color: #2c3e50;
}

.item-label {
  color: #fff;
  font-weight: 600;
  font-size: 12px;
}

.item-desc {
  color: #888;
  font-size: 10px;
}

.ai-option {
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #2196F3;
}

.ai-option:hover, .ai-option.active {
  background-color: rgba(33, 150, 243, 0.1);
}

.ai-text {
  display: flex;
  flex-direction: column;
}

.ai-title {
  font-weight: 600;
  font-size: 12px;
}

.ai-query {
  font-size: 11px;
  color: #888;
  font-style: italic;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
