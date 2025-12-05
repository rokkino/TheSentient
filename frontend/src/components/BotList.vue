<template>
  <div class="bot-list-container">
    <div class="bot-header-section">
      <h2>🤖 Trading Bots Competition</h2>
      <p class="subtitle">Compete with your friends' trading bots</p>
    </div>

    <div v-if="loading" class="loading">Loading bots...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="bots.length === 0" class="no-bots">
      <p>No bots available yet.</p>
      <button class="create-bot-btn" @click="$emit('create-bot')">Create Your Bot</button>
    </div>
    <div v-else class="bots-grid">
      <BotCard
        v-for="bot in bots"
        :key="bot.id"
        :bot="bot"
        @view="handleViewBot"
        @compete="handleCompete"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import BotCard from './BotCard.vue'

const emit = defineEmits(['view-bot', 'compete', 'create-bot'])

const bots = ref([])
const loading = ref(false)
const error = ref(null)

const handleViewBot = (bot) => {
  emit('view-bot', bot)
}

const handleCompete = (bot) => {
  emit('compete', bot)
}

const loadBots = () => {
  loading.value = true
  error.value = null

  // For now, just show Gianluca's bot as placeholder
  // In the future, this will load from an API
  setTimeout(() => {
    bots.value = [
      {
        id: 1,
        name: "Gianluca's Bot",
        owner: "Gianluca",
        status: "active",
        winRate: 72.5,
        totalTrades: 156,
        profit: 23.4,
        description: "Lyrics:(Trap backing track) Money, (Trap backing track) Money, (Trap backing track) Money, (Trap backing track) Money."
      }
    ]
    loading.value = false
  }, 500)
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

.create-bot-btn {
  padding: 12px 24px;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.create-bot-btn:hover {
  background: #3182ce;
  transform: translateY(-2px);
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

