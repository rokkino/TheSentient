<template>
  <div class="bot-card">
    <div class="bot-header">
      <div class="bot-avatar">
        <span class="bot-icon">🤖</span>
      </div>
      <div class="bot-info">
        <h3 class="bot-name">{{ bot.name }}</h3>
        <p class="bot-owner">by {{ bot.owner || 'You' }}</p>
      </div>
      <div class="bot-status" :class="bot.status?.toLowerCase() || 'inactive'">
        <span class="status-dot"></span>
        {{ (bot.status || 'INACTIVE').toUpperCase() }}
      </div>
    </div>
    
    <div class="bot-stats">
      <div class="stat-item">
        <span class="stat-label">Win Rate</span>
        <span class="stat-value">{{ (bot.winRate || 0).toFixed(0) }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Total Trades</span>
        <span class="stat-value">{{ bot.totalTrades || 0 }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Profit</span>
        <span class="stat-value" :class="(bot.profit || 0) > 0 ? 'positive' : (bot.profit || 0) < 0 ? 'negative' : ''">
          {{ (bot.profit || 0) > 0 ? '+' : '' }}{{ (bot.profit || 0).toFixed(2) }}%
        </span>
      </div>
    </div>
    
    <div v-if="bot.description && bot.description.trim()" class="bot-description">
      <p>{{ bot.description }}</p>
    </div>
    
    <div class="bot-actions">
      <button 
        class="action-btn import-btn" 
        @click="$emit('import', bot)"
        title="Import bot configuration"
      >
        Import
      </button>
      <button 
        class="action-btn export-btn" 
        @click="$emit('export', bot)"
        title="Export bot configuration"
      >
        Export
      </button>
      <button 
        class="action-btn configure-btn" 
        :disabled="bot.status === 'active'"
        @click="$emit('configure', bot)"
      >
        Configure
      </button>
      <button 
        class="action-btn activate-btn" 
        :disabled="!bot.is_configured"
        :class="{ 'active': bot.status === 'active' }"
        @click="bot.status === 'active' ? $emit('deactivate', bot) : $emit('activate', bot)"
      >
        {{ bot.status === 'active' ? 'Active' : 'Activate' }}
      </button>
    </div>
    
    <div class="ai-actions" v-if="bot.status === 'active'">
      <button class="ai-btn llama-btn" @click="callLlama" :disabled="loadingAi">
        🦙 Llama Call
      </button>
      <button class="ai-btn gemini-btn" @click="callGemini" :disabled="loadingAi">
        ✨ Gemini Call
      </button>
    </div>
    
    <!-- AI Explanation Modal -->
    <!-- AI Explanation Modal -->
    <Teleport to="body">
      <div v-if="showAiModal" class="modal-overlay">
        <div class="modal-content">
          <div class="modal-header">
            <h3>{{ aiSource }} Explanation</h3>
            <button class="close-btn" @click="closeAiModal">&times;</button>
          </div>
          <div class="modal-body chat-body" ref="chatContainer">
            <div v-if="chatMessages.length === 0 && loadingAi" class="loading-spinner">
              Thinking...
            </div>
            <div v-else class="chat-messages">
              <div 
                v-for="(msg, index) in chatMessages" 
                :key="index" 
                class="message"
                :class="[msg.role, { error: msg.error }]"
              >
                <div class="message-content">{{ msg.content }}</div>
              </div>
              <div v-if="loadingAi && chatMessages.length > 0" class="message assistant loading">
                <div class="typing-indicator"><span>.</span><span>.</span><span>.</span></div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <div class="chat-input-container">
              <input 
                v-model="userMessage" 
                @keyup.enter="sendMessage"
                placeholder="Ask a follow-up question..."
                :disabled="loadingAi"
                class="chat-input"
              />
              <button @click="sendMessage" :disabled="loadingAi || !userMessage.trim()" class="send-btn">
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>


<script setup>
import { ref, nextTick, watch } from 'vue'
import api from '../services/api'

const props = defineProps({
  bot: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['configure', 'activate', 'deactivate', 'import', 'export'])

const showAiModal = ref(false)
const aiSource = ref('')
const loadingAi = ref(false)
const chatMessages = ref([])
const userMessage = ref('')
const chatContainer = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const callLlama = async () => {
  openAiModal('Llama')
  // Initial explanation
  try {
    const response = await api.callLlama(props.bot.id)
    chatMessages.value.push({
      role: 'assistant',
      content: response.data.explanation
    })
  } catch (err) {
    chatMessages.value.push({
      role: 'assistant',
      content: 'Error calling Llama: ' + (err.response?.data?.detail || err.message),
      error: true
    })
  } finally {
    loadingAi.value = false
    scrollToBottom()
  }
}

const callGemini = async () => {
  openAiModal('Gemini')
  // Initial explanation
  try {
    const response = await api.callGemini(props.bot.id)
    chatMessages.value.push({
      role: 'assistant',
      content: response.data.explanation
    })
  } catch (err) {
    chatMessages.value.push({
      role: 'assistant',
      content: 'Error calling Gemini: ' + (err.response?.data?.detail || err.message),
      error: true
    })
  } finally {
    loadingAi.value = false
    scrollToBottom()
  }
}

const sendMessage = async () => {
  if (!userMessage.value.trim() || loadingAi.value) return
  
  const message = userMessage.value.trim()
  userMessage.value = ''
  
  // Add user message
  chatMessages.value.push({
    role: 'user',
    content: message
  })
  scrollToBottom()
  
  loadingAi.value = true
  
  try {
    // Prepare history for API (exclude error messages)
    const history = chatMessages.value
      .filter(m => !m.error)
      .map(m => ({
        role: m.role,
        content: m.content
      }))
    
    const requestData = {
      prompt: message,
      history: history
    }
    
    let response
    if (aiSource.value === 'Llama') {
      response = await api.callLlama(props.bot.id, requestData)
    } else {
      response = await api.callGemini(props.bot.id, requestData)
    }
    
    chatMessages.value.push({
      role: 'assistant',
      content: response.data.explanation
    })
  } catch (err) {
    chatMessages.value.push({
      role: 'assistant',
      content: `Error calling ${aiSource.value}: ` + (err.response?.data?.detail || err.message),
      error: true
    })
  } finally {
    loadingAi.value = false
    scrollToBottom()
  }
}

const openAiModal = (source) => {
  aiSource.value = source
  chatMessages.value = []
  userMessage.value = ''
  loadingAi.value = true
  showAiModal.value = true
}

const closeAiModal = () => {
  showAiModal.value = false
}
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
  display: flex;
  flex-direction: column;
  min-height: fit-content;
  box-sizing: border-box;
  min-width: 0; /* allow shrink inside CSS grid parents */
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
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.bot-status.active {
  background: rgba(104, 211, 145, 0.2);
  color: #68d391;
  border: 1px solid rgba(104, 211, 145, 0.3);
}

.bot-status.inactive {
  background: rgba(252, 129, 129, 0.2);
  color: #fc8181;
  border: 1px solid rgba(252, 129, 129, 0.3);
}

.bot-status.error {
  background: rgba(252, 129, 129, 0.2);
  color: #fc8181;
  border: 1px solid rgba(252, 129, 129, 0.3);
}

.bot-status.training {
  background: rgba(246, 173, 85, 0.2);
  color: #f6ad55;
  border: 1px solid rgba(246, 173, 85, 0.3);
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
  gap: 12px;
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
  font-size: 24px;
  font-weight: 700;
  color: #e2e8f0;
  line-height: 1.2;
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
  min-height: auto;
}

.bot-description:empty {
  display: none;
}

.bot-description p {
  margin: 0;
  color: #cbd5e0;
  font-size: 14px;
  line-height: 1.6;
}

.bot-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: auto;
  width: 100%;
}

.action-btn {
  flex: 1;
  min-width: 80px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.import-btn {
  background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
  color: white;
}

.import-btn:hover {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.export-btn {
  background: linear-gradient(135deg, #805ad5 0%, #6b46c1 100%);
  color: white;
}

.export-btn:hover {
  background: linear-gradient(135deg, #9f7aea 0%, #805ad5 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.configure-btn {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
}

.configure-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #63b3ed 0%, #4299e1 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.configure-btn:disabled {
  background: #4a5568;
  color: #a0aec0;
  opacity: 0.7;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.activate-btn {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
}

.activate-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #68d391 0%, #48bb78 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.activate-btn:disabled {
  background: #4a5568;
  color: #a0aec0;
  opacity: 0.7;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

.activate-btn.active {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
  color: #68d391;
  border: 1px solid #68d391;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.ai-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #2d3748;
}

.ai-btn {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.1s;
  font-size: 13px;
}

.ai-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.ai-btn:active:not(:disabled) {
  transform: translateY(0);
}

.llama-btn {
  background: #d97706; /* Amber */
  color: white;
}

.gemini-btn {
  background: #805ad5; /* Purple */
  color: white;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #2d3748;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #4a5568;
}

.modal-header h3 {
  margin: 0;
  color: #e2e8f0;
}

.close-btn {
  background: none;
  border: none;
  color: #a0aec0;
  font-size: 24px;
  cursor: pointer;
}

.modal-body {
  padding: 24px;
  min-height: 100px;
  color: #e2e8f0;
  line-height: 1.6;
  white-space: pre-wrap;
}

.loading-spinner {
  text-align: center;
  color: #a0aec0;
  font-style: italic;
}

@media (max-width: 480px) {
  .bot-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}

/* Chat Styles */
.chat-body {
  display: flex;
  flex-direction: column;
  height: 400px;
  overflow-y: auto;
  padding: 20px;
  background: #1a202c;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  background: #3182ce;
  color: white;
  border-radius: 12px 12px 0 12px;
  padding: 10px 14px;
}

.message.assistant {
  align-self: flex-start;
  background: #2d3748;
  color: #e2e8f0;
  border-radius: 12px 12px 12px 0;
  padding: 10px 14px;
  border: 1px solid #4a5568;
}

.message.error {
  background: rgba(252, 129, 129, 0.2);
  color: #fc8181;
  border: 1px solid rgba(252, 129, 129, 0.3);
}

.message-content {
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 14px;
}

.modal-footer {
  padding: 16px;
  border-top: 1px solid #4a5568;
  background: #2d3748;
  border-radius: 0 0 12px 12px;
}

.chat-input-container {
  display: flex;
  gap: 10px;
}

.chat-input {
  flex: 1;
  background: #1a202c;
  border: 1px solid #4a5568;
  border-radius: 8px;
  padding: 10px 14px;
  color: white;
  font-size: 14px;
}

.chat-input:focus {
  outline: none;
  border-color: #4299e1;
}

.send-btn {
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0 20px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #3182ce;
}

.send-btn:disabled {
  background: #4a5568;
  cursor: not-allowed;
  opacity: 0.7;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 8px;
}

.typing-indicator span {
  animation: bounce 1.4s infinite ease-in-out both;
  background-color: #a0aec0;
  border-radius: 50%;
  display: inline-block;
  height: 6px;
  width: 6px;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}</style>

