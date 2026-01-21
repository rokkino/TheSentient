<template>
  <div class="bot-list-container">
    <div class="bot-header-section">
      <h2>🤖 Trading Bots Competition</h2>
      <p class="subtitle">Compete with your friends' trading bots</p>
    </div>

    <div class="leaderboard-section" v-if="bots.length > 0">
      <div class="leaderboard-header">
        <h3>🏆 Performance Leaderboard</h3>
        <div class="metric-toggles">
          <button 
            :class="{ active: leaderboardMetric === 'winRate' }" 
            @click="leaderboardMetric = 'winRate'"
          >Win Rate</button>
          <button 
            :class="{ active: leaderboardMetric === 'profit' }" 
            @click="leaderboardMetric = 'profit'"
          >Total Profit</button>
        </div>
      </div>
      
      <div class="leaderboard-graph">
        <div v-for="(bot, index) in leaderboardBots" :key="bot.id" class="graph-row">
          <div class="rank">{{ index + 1 }}</div>
          <div class="bot-info">
            <div class="bot-avatar" :style="{ backgroundColor: getBotColor(bot.name) }">
              {{ bot.name.charAt(0).toUpperCase() }}
            </div>
            <span class="bot-name">{{ bot.name }}</span>
          </div>
          <div class="bar-container">
            <div 
              class="bar" 
              :style="{ width: getBarWidth(bot) + '%' }"
              :class="leaderboardMetric"
            >
              <div class="bar-glow"></div>
            </div>
          </div>
          <div class="metric-value">
            {{ formatMetricValue(bot) }}
          </div>
        </div>
      </div>
    </div>

    <div class="section-divider" v-if="bots.length > 0"></div>

    <div v-if="loading" class="loading">Loading bots...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="bots.length === 0" class="no-bots">
      <p>No bots available yet. Create your first bot to get started!</p>
    </div>
    <div v-else class="bots-grid">
      <BotCard
        v-for="bot in bots"
        :key="bot.id"
        :bot="bot"
        @configure="handleConfigureBot"
        @activate="handleActivateBot"
        @deactivate="handleDeactivateBot"
        @import="handleImportBot"
        @export="handleExportBot"
      />
    </div>
    
    <BotConfigModal
      :show="showConfigModal"
      :bot="selectedBot"
      @close="showConfigModal = false"
      @saved="handleConfigSaved"
    />
    
    <CreateBotModal
      :show="showCreateModal"
      @close="showCreateModal = false"
      @created="handleBotCreated"
    />
    
    <ImportBotModal
      :show="showImportModal"
      :target-bot="importTargetBot"
      @close="showImportModal = false"
      @imported="handleBotImported"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import BotCard from './BotCard.vue'
import BotConfigModal from './BotConfigModal.vue'
import CreateBotModal from './CreateBotModal.vue'
import ImportBotModal from './ImportBotModal.vue'
import api from '../services/api'

const emit = defineEmits(['create-bot'])

const showCreateModal = ref(false)
const showImportModal = ref(false)
const importTargetBot = ref(null)

const bots = ref([])
const loading = ref(false)
const error = ref(null)
const selectedBot = ref(null)
const showConfigModal = ref(false)

// Leaderboard Logic
const leaderboardMetric = ref('winRate') // 'winRate' or 'profit'

const leaderboardBots = computed(() => {
  return [...bots.value].sort((a, b) => {
    if (leaderboardMetric.value === 'winRate') {
      return b.winRate - a.winRate
    } else {
      return b.profit - a.profit
    }
  }).slice(0, 5) // Top 5
})

const maxMetricValue = computed(() => {
  if (bots.value.length === 0) return 100
  
  if (leaderboardMetric.value === 'winRate') {
    return 100 // Win rate is always out of 100%
  } else {
    const maxProfit = Math.max(...bots.value.map(b => b.profit))
    return maxProfit > 0 ? maxProfit : 100 // Avoid division by zero
  }
})

const getBarWidth = (bot) => {
  let value = 0
  let max = maxMetricValue.value
  
  if (leaderboardMetric.value === 'winRate') {
    value = bot.winRate
  } else {
    value = bot.profit > 0 ? bot.profit : 0 // Don't show negative bars for now
  }
  
  // Ensure a minimum width for visibility if value > 0
  if (value > 0) {
    const percentage = (value / max) * 100
    return Math.max(percentage, 5) 
  }
  return 0
}

const formatMetricValue = (bot) => {
  if (leaderboardMetric.value === 'winRate') {
    return `${bot.winRate.toFixed(1)}%`
  } else {
    return `$${bot.profit.toFixed(2)}`
  }
}

const getBotColor = (name) => {
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const handleConfigureBot = (bot) => {
  selectedBot.value = bot
  showConfigModal.value = true
}

const handleImportBot = (bot) => {
  importTargetBot.value = bot
  showImportModal.value = true
}

const handleDeactivateBot = async (bot) => {
  try {
    await api.deactivateBot(bot.id)
    await loadBots() // Reload bots to update status
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to deactivate bot'
  }
}

const handleActivateBot = async (bot) => {
  try {
    await api.activateBot(bot.id)
    await loadBots() // Reload bots to update status
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to activate bot'
  }
}

const handleConfigSaved = () => {
  loadBots() // Reload bots after config is saved
}

const handleBotCreated = () => {
  console.log('Bot created, reloading bots...')
  // Small delay to ensure the backend has committed the transaction
  setTimeout(() => {
    loadBots()
  }, 300)
}

const handleExportBot = async (bot) => {
  try {
    const response = await api.exportBot(bot.id)
    const exportData = response.data
    
    // Create a blob and download it
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `bot_${bot.name.replace(/\s+/g, '_')}_${Date.now()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to export bot'
    console.error('Error exporting bot:', err)
  }
}

const handleBotImported = () => {
  console.log('Bot imported, reloading bots...')
  setTimeout(() => {
    loadBots()
  }, 300)
}

const loadBots = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await api.getBots()
    console.log('Bots API response:', response.data)
    
    if (response.data && response.data.bots) {
      bots.value = response.data.bots.map(bot => ({
        ...bot,
        winRate: parseFloat(bot.win_rate) || 0,
        totalTrades: parseInt(bot.total_trades) || 0,
        profit: parseFloat(bot.profit) || 0,
        owner: bot.owner || bot.user?.username || 'You',
        status: bot.status || 'inactive',
        description: bot.description || ''
      }))
      console.log('Bots loaded:', bots.value.length)
    } else {
      console.warn('Unexpected response format:', response.data)
      bots.value = []
    }
  } catch (err) {
    console.error('Error loading bots:', err)
    error.value = err.response?.data?.detail || err.message || 'Failed to load bots'
    bots.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadBots()
})
</script>

<style scoped>
.bot-list-container {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.bot-header-section {
  text-align: center;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.bot-header-section h2 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: #e2e8f0;
}

.subtitle {
  margin: 0;
  font-size: 16px;
  color: #a0aec0;
}

/* Leaderboard Styles */
.leaderboard-section {
  background: #1a202c;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
  border: 1px solid #2d3748;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.leaderboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.leaderboard-header h3 {
  margin: 0;
  font-size: 18px;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric-toggles {
  display: flex;
  background: #2d3748;
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.metric-toggles button {
  background: transparent;
  border: none;
  color: #a0aec0;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.metric-toggles button.active {
  background: #4a5568;
  color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.leaderboard-graph {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.graph-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.rank {
  font-size: 14px;
  font-weight: 700;
  color: #718096;
  width: 20px;
  text-align: center;
}

.graph-row:nth-child(1) .rank { color: #fbbf24; } /* Gold */
.graph-row:nth-child(2) .rank { color: #94a3b8; } /* Silver */
.graph-row:nth-child(3) .rank { color: #b45309; } /* Bronze */

.bot-info {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 180px;
  flex-shrink: 0;
}

.bot-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: white;
  font-size: 14px;
}

.bot-name {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-container {
  flex: 1;
  height: 24px;
  background: #2d3748;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.bar {
  height: 100%;
  border-radius: 6px;
  position: relative;
  transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 4px;
}

.bar.winRate {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}

.bar.profit {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.bar-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transform: skewX(-20deg) translateX(-150%);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  100% { transform: skewX(-20deg) translateX(150%); }
}

.metric-value {
  width: 80px;
  text-align: right;
  font-weight: 700;
  color: #e2e8f0;
  font-size: 14px;
}

.section-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #2d3748, transparent);
  margin: 0 0 32px 0;
}

.loading, .error, .no-bots {
  text-align: center;
  padding: 60px 20px;
  color: #a0aec0;
}

.error {
  color: #fc8181;
}

.no-bots {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.bots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .bots-grid {
    grid-template-columns: 1fr;
  }
  
  .bot-info {
    width: 120px;
  }
  
  .metric-value {
    width: 60px;
    font-size: 12px;
  }
}
</style>

