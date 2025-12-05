<template>
  <div class="bot-card">
    <div class="bot-header">
      <div class="bot-avatar">
        <span class="bot-icon">🤖</span>
      </div>
      <div class="bot-info">
        <h3 class="bot-name">{{ bot.name }}</h3>
        <p class="bot-owner">by {{ bot.owner }}</p>
      </div>
      <div class="bot-status" :class="bot.status">
        <span class="status-dot"></span>
        {{ bot.status }}
      </div>
    </div>
    
    <div class="bot-stats">
      <div class="stat-item">
        <span class="stat-label">Win Rate</span>
        <span class="stat-value">{{ bot.winRate }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Total Trades</span>
        <span class="stat-value">{{ bot.totalTrades }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Profit</span>
        <span class="stat-value" :class="bot.profit >= 0 ? 'positive' : 'negative'">
          {{ bot.profit >= 0 ? '+' : '' }}{{ bot.profit.toFixed(2) }}%
        </span>
      </div>
    </div>
    
    <div class="bot-description">
      <p>{{ bot.description }}</p>
    </div>
    
    <div class="bot-actions">
      <button class="action-btn view-btn" @click="$emit('view', bot)">View Details</button>
      <button class="action-btn compete-btn" @click="$emit('compete', bot)">Compete</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  bot: {
    type: Object,
    required: true
  }
})

defineEmits(['view', 'compete'])
</script>

<style scoped>
.bot-card {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
  border: 2px solid #4a5568;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.bot-card:hover {
  transform: translateY(-4px);
  border-color: #718096;
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.4);
}

.bot-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #4a5568;
}

.bot-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bot-icon {
  font-size: 32px;
}

.bot-info {
  flex: 1;
}

.bot-name {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 700;
  color: #e2e8f0;
}

.bot-owner {
  margin: 0;
  font-size: 14px;
  color: #a0aec0;
}

.bot-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.bot-status.active {
  background: #2d5016;
  color: #68d391;
}

.bot-status.inactive {
  background: #4a2a2a;
  color: #fc8181;
}

.bot-status.training {
  background: #4a3a2a;
  color: #f6ad55;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.bot-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: #1a202c;
  border-radius: 8px;
  border: 1px solid #2d3748;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #a0aec0;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #e2e8f0;
}

.stat-value.positive {
  color: #68d391;
}

.stat-value.negative {
  color: #fc8181;
}

.bot-description {
  margin-bottom: 20px;
  padding: 16px;
  background: #1a202c;
  border-radius: 8px;
  border-left: 3px solid #4299e1;
}

.bot-description p {
  margin: 0;
  color: #cbd5e0;
  font-size: 14px;
  line-height: 1.6;
}

.bot-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.view-btn {
  background: #4299e1;
  color: white;
}

.view-btn:hover {
  background: #3182ce;
  transform: translateY(-2px);
}

.compete-btn {
  background: #48bb78;
  color: white;
}

.compete-btn:hover {
  background: #38a169;
  transform: translateY(-2px);
}
</style>

