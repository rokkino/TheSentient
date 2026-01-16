<template>
  <div class="bot-list-container">
    <div class="bot-header-section">
      <h2>🤖 Trading Bots Competition</h2>
      <p class="subtitle">Compete with your friends' trading bots</p>
    </div>

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
import { ref, onMounted } from 'vue'
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
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 2px solid #2d3748;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.bot-header-section h2 {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  color: #e2e8f0;
}

.subtitle {
  margin: 0;
  font-size: 16px;
  color: #a0aec0;
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
}
</style>

