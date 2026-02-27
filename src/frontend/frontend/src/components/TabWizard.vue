<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Add New Tab</h2>
        <button class="close-btn" @click="close">×</button>
      </div>
      
      <div class="modal-body">
        <div class="wizard-step">
          <h3>Choose Tab Type</h3>
          
          <div v-for="category in categories" :key="category" class="preset-category">
            <h4 class="category-title">{{ category }}</h4>
            <div class="presets-grid">
              <div
                v-for="preset in tabPresets.filter(p => p.category === category)"
                :key="preset.type"
                class="preset-card"
                :class="{ selected: selectedPreset?.type === preset.type, coming: ['portfolio', 'screener', 'alerts', 'heatmap', 'calendar'].includes(preset.type) }"
                @click="selectPreset(preset)"
              >
                <div class="preset-icon">{{ preset.icon }}</div>
                <div class="preset-name">{{ preset.name }}</div>
                <div class="preset-description">{{ preset.description }}</div>
                <div v-if="['portfolio', 'screener', 'alerts', 'heatmap', 'calendar'].includes(preset.type)" class="coming-soon-badge">Coming Soon</div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="selectedPreset" class="wizard-step">
          <h3>Tab Name</h3>
          <input
            v-model="tabName"
            type="text"
            class="form-input"
            :placeholder="selectedPreset.defaultName"
            maxlength="20"
          />
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="close" class="btn-secondary">Cancel</button>
        <button
          @click="createTab"
          class="btn-primary"
          :disabled="!selectedPreset || !tabName.trim()"
        >
          Create Tab
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'create'])

const tabPresets = [
  {
    type: 'stocks',
    name: 'Charts',
    description: 'Stock charts with full technical analysis',
    icon: '📈',
    defaultName: 'Charts',
    category: 'Analysis'
  },
  {
    type: 'earnings',
    name: 'Earnings',
    description: 'Earnings calendar and reports',
    icon: '💰',
    defaultName: 'Earnings',
    category: 'Analysis'
  },
  {
    type: 'news',
    name: 'News',
    description: 'Real-time financial news feed',
    icon: '📰',
    defaultName: 'News',
    category: 'Information'
  },
  {
    type: 'bot',
    name: 'Trading Bot',
    description: 'Automated trading bots',
    icon: '🤖',
    defaultName: 'Bot',
    category: 'Trading'
  },
  {
    type: 'chat',
    name: 'AI Chat',
    description: 'Chat with AI assistant',
    icon: '💬',
    defaultName: 'Chat',
    category: 'Tools'
  },
  {
    type: 'strategy',
    name: 'Strategy Builder',
    description: 'Create and backtest strategies',
    icon: '♟️',
    defaultName: 'Strategy',
    category: 'Trading'
  },
  {
    type: 'backtesting',
    name: 'Backtesting',
    description: 'Historical simulation engine',
    icon: '📊',
    defaultName: 'Backtesting',
    category: 'Trading'
  },
  {
    type: 'portfolio',
    name: 'Portfolio',
    description: 'Track your investments',
    icon: '💼',
    defaultName: 'Portfolio',
    category: 'Trading'
  },
  {
    type: 'screener',
    name: 'Screener',
    description: 'Find stocks with filters',
    icon: '🔍',
    defaultName: 'Screener',
    category: 'Analysis'
  },
  {
    type: 'alerts',
    name: 'Price Alerts',
    description: 'Set and manage price alerts',
    icon: '🔔',
    defaultName: 'Alerts',
    category: 'Tools'
  },
  {
    type: 'heatmap',
    name: 'Market Heatmap',
    description: 'Visual market overview',
    icon: '🗺️',
    defaultName: 'Heatmap',
    category: 'Analysis'
  },
  {
    type: 'calendar',
    name: 'Economic Calendar',
    description: 'Economic events and releases',
    icon: '📅',
    defaultName: 'Calendar',
    category: 'Information'
  }
]

const categories = ['Analysis', 'Trading', 'Information', 'Tools']

const selectedPreset = ref(null)
const tabName = ref('')

watch(() => props.show, (newValue) => {
  if (newValue) {
    selectedPreset.value = null
    tabName.value = ''
  }
})

const selectPreset = (preset) => {
  selectedPreset.value = preset
  if (!tabName.value) {
    tabName.value = preset.defaultName
  }
}

const createTab = () => {
  if (!selectedPreset.value || !tabName.value.trim()) {
    return
  }
  
  emit('create', {
    name: tabName.value.trim(),
    type: selectedPreset.value.type,
    ...getDefaultTabConfig(selectedPreset.value.type)
  })
  close()
}

const getDefaultTabConfig = (type) => {
  const baseConfig = {
    selectedTicker: null,
    chartInfo: {
      symbol: '',
      name: '',
      price: null,
      change: null,
      changePercent: null,
      volume: null
    }
  }
  
  if (type === 'stocks') {
    return {
      ...baseConfig,
      timeframe: '1y',
      chartType: 'Candle',
      indicators: {
        rsi: true,
        ma13: false,
        ma50: false,
        ma200: false,
        ma800: false,
        bullRun: true
      }
    }
  }
  
  return baseConfig
}

const close = () => {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.modal-content {
  background: var(--glass-bg, rgba(30, 41, 59, 0.5));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-lg, 24px);
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-glass, 0 25px 50px -12px rgba(0, 0, 0, 0.5));
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 25px;
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  background: transparent;
}

.modal-header h2 {
  margin: 0;
  color: #fff;
  font-size: 18px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 300;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary, #94a3b8);
  font-size: 28px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text-primary, #e2e8f0);
}

.modal-body {
  padding: 30px;
  flex: 1;
  overflow-y: auto;
}

.wizard-step {
  margin-bottom: 30px;
}

.wizard-step h3 {
  color: var(--text-secondary, #94a3b8);
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 20px;
}

.preset-category {
  margin-bottom: 24px;
}

.preset-category:last-child {
  margin-bottom: 0;
}

.category-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: var(--accent-primary, #3b82f6);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.preset-card {
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm, 12px);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.preset-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.preset-card.selected {
  background: var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
  border-color: var(--accent-primary, #3b82f6);
  box-shadow: 0 0 0 1px var(--accent-primary, #3b82f6), 0 4px 12px rgba(0,0,0,0.3);
}

.preset-card.coming {
  opacity: 0.6;
  cursor: not-allowed;
}

.preset-card.coming:hover {
  transform: none;
  border-color: #333;
}

.coming-soon-badge {
  position: absolute;
  top: 8px;
  right: -24px;
  background: linear-gradient(135deg, #ff9800 0%, #ff5722 100%);
  color: #000;
  font-size: 8px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 28px;
  transform: rotate(45deg);
}

.preset-icon {
  font-size: 28px;
  margin-bottom: 8px;
  transition: transform 0.2s;
}

.preset-card:hover .preset-icon {
  transform: scale(1.1);
}

.preset-name {
  color: var(--text-primary, #e2e8f0);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
  letter-spacing: 0.3px;
}

.preset-description {
  color: var(--text-secondary, #94a3b8);
  font-size: 11px;
  line-height: 1.4;
}

.form-input {
  width: 100%;
  padding: 12px 15px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm, 12px);
  color: var(--text-primary, #e2e8f0);
  font-size: 14px;
  font-family: 'Roboto Mono', monospace;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--accent-primary, #3b82f6);
  box-shadow: 0 0 0 3px var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  padding: 25px;
  border-top: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  background: transparent;
}

.btn-secondary,
.btn-primary {
  padding: 12px 30px;
  border: none;
  border-radius: var(--radius-sm, 12px);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background-color: transparent;
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  color: var(--text-secondary, #94a3b8);
}

.btn-secondary:hover {
  border-color: rgba(255, 255, 255, 0.2);
  color: var(--text-primary, #e2e8f0);
}

.btn-primary {
  background: var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}

.btn-primary:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.25);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.2);
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>


