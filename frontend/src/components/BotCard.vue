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
    
    <button 
      class="check-orders-big" 
      @click="openCheckOrdersModal"
      title="Check orders & chat with the bot"
    >
      Check Orders
    </button>
    
    <!-- Check Orders Modal: summary + orders table + chat -->
    <Teleport to="body">
      <div v-if="showOrdersModal" class="modal-overlay check-orders-overlay" @click.self="closeOrdersModal">
        <div class="modal-content check-orders-panel">
          <div class="modal-header">
            <h3>Check Orders – {{ bot.name }}</h3>
            <button class="close-btn" @click="closeOrdersModal">&times;</button>
          </div>

          <div class="check-orders-summary">
            <div class="summary-item">
              <span class="summary-label">P&amp;L</span>
              <span class="summary-value" :class="(profit?.profit_loss_value || 0) >= 0 ? 'positive' : 'negative'">
                {{ formatPct(profit?.profit_loss_percent) }} ({{ formatCur(profit?.profit_loss_value) }})
              </span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Top profit</span>
              <span class="summary-value positive">
                {{ (profit?.profit_loss_value || 0) >= 0 ? formatCur(profit?.profit_loss_value) : '—' }}
              </span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Balance</span>
              <span class="summary-value">{{ formatCur(profit?.total_balance) }}</span>
            </div>
            <div class="summary-item" v-if="profit?.timestamp">
              <span class="summary-label">Updated</span>
              <span class="summary-value muted">{{ profit.timestamp }}</span>
            </div>
            <div class="summary-item" v-if="serverTime">
              <span class="summary-label">Server Time</span>
              <span class="summary-value">{{ serverTime }}</span>
            </div>
          </div>

          <div class="orders-section">
            <div class="orders-toolbar">
              <button class="btn-add-order" @click="showAddOrderForm = true" v-if="!showAddOrderForm">
                + Add order
              </button>
              <div v-if="showAddOrderForm" class="add-order-form">
                <input v-model="newOrder.symbol" placeholder="Symbol" class="add-input" />
                <select v-model="newOrder.decision" class="add-select">
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                  <option value="HOLD">HOLD</option>
                  <option value="WAIT">WAIT</option>
                </select>
                <input v-model="newOrder.execution_time" type="datetime-local" class="add-input" />
                <input v-model="newOrder.reasoning" placeholder="Reasoning" class="add-input" />
                <button class="btn-save" @click="createOrder">Create</button>
                <button class="btn-cancel" @click="cancelAddOrder">Cancel</button>
              </div>
            </div>
            <div v-if="loadingOrders" class="loading-spinner">Loading orders...</div>
            <div v-else-if="!orders.length && !showAddOrderForm" class="orders-empty">
              No planned or executed orders yet. Add one manually.
            </div>
            <div v-else class="orders-table-wrap">
              <table v-if="orders.length > 0" class="orders-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Decision</th>
                    <th>Status</th>
                    <th>Time</th>
                    <th>Reasoning</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="d in orders" 
                    :key="d.id" 
                    class="order-row"
                    :class="d.decision?.toLowerCase()"
                  >
                    <td v-if="editingOrderId !== d.id">
                      <span class="order-symbol">{{ d.symbol || '—' }}</span>
                    </td>
                    <td v-else>
                      <input v-model="editForm.symbol" class="edit-input" />
                    </td>
                    <td v-if="editingOrderId !== d.id">
                      <span class="order-decision">{{ d.decision }}</span>
                    </td>
                    <td v-else>
                      <select v-model="editForm.decision" class="edit-select">
                        <option value="BUY">BUY</option>
                        <option value="SELL">SELL</option>
                        <option value="HOLD">HOLD</option>
                        <option value="WAIT">WAIT</option>
                      </select>
                    </td>
                    <td v-if="editingOrderId !== d.id">
                      <span class="order-status">{{ d.status }}</span>
                    </td>
                    <td v-else>
                      <select v-model="editForm.status" class="edit-select">
                        <option value="PENDING">PENDING</option>
                        <option value="EXECUTED">EXECUTED</option>
                        <option value="CANCELLED">CANCELLED</option>
                        <option value="FAILED">FAILED</option>
                      </select>
                    </td>
                    <td v-if="editingOrderId !== d.id">
                      <span class="order-time">{{ formatOrderTime(d.execution_time || d.created_at) }}</span>
                    </td>
                    <td v-else>
                      <input v-model="editForm.execution_time" type="datetime-local" class="edit-input" />
                    </td>
                    <td v-if="editingOrderId !== d.id">
                      <span class="order-reasoning-cell">{{ d.reasoning || '—' }}</span>
                    </td>
                    <td v-else>
                      <input v-model="editForm.reasoning" class="edit-input" placeholder="Reasoning" />
                    </td>
                    <td class="actions-cell">
                      <template v-if="editingOrderId === d.id">
                        <button class="btn-icon save" @click="saveEdit(d.id)" title="Save">✓</button>
                        <button class="btn-icon cancel" @click="cancelEdit" title="Cancel">✕</button>
                      </template>
                      <template v-else>
                        <button class="btn-icon btn-edit" @click="startEdit(d)" title="Edit">✎</button>
                        <button class="btn-icon btn-del" @click="deleteOrder(d)" title="Delete">⌫</button>
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="check-orders-chat">
            <div class="chat-body" ref="checkOrdersChatRef">
              <div v-if="checkOrdersChatMessages.length === 0 && checkOrdersLoadingAi" class="loading-spinner">Thinking...</div>
              <div v-else class="chat-messages">
                <div 
                  v-for="(msg, index) in checkOrdersChatMessages" 
                  :key="index" 
                  class="message"
                  :class="[msg.role, { error: msg.error }]"
                >
                  <div class="message-content">{{ msg.content }}</div>
                </div>
                <div v-if="checkOrdersLoadingAi && checkOrdersChatMessages.length > 0" class="message assistant loading">
                  <div class="typing-indicator"><span>.</span><span>.</span><span>.</span></div>
                </div>
              </div>
            </div>
            <div class="chat-input-container">
              <button class="btn-clear-history" @click="clearChatHistory" title="Clear History" v-if="checkOrdersChatMessages.length > 0">
                 🗑️
              </button>
              <input 
                v-model="checkOrdersUserMessage" 
                @keyup.enter="sendCheckOrdersChat"
                placeholder="Ask the bot..."
                :disabled="checkOrdersLoadingAi"
                class="chat-input"
              />
              <button @click="sendCheckOrdersChat" :disabled="checkOrdersLoadingAi || !checkOrdersUserMessage.trim()" class="send-btn">
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

const showOrdersModal = ref(false)
const orders = ref([])
const loadingOrders = ref(false)
const profit = ref(null)
const checkOrdersChatMessages = ref([])
const checkOrdersUserMessage = ref('')
const checkOrdersLoadingAi = ref(false)
const checkOrdersChatRef = ref(null)
const editingOrderId = ref(null)
const editForm = ref({ symbol: '', decision: 'BUY', status: 'PENDING', execution_time: '', reasoning: '' })
const showAddOrderForm = ref(false)
const newOrder = ref({ symbol: '', decision: 'BUY', execution_time: '', reasoning: '' })
const serverTime = ref('')

const openCheckOrdersModal = async () => {
  showOrdersModal.value = true
  profit.value = null
  orders.value = []
  loadingOrders.value = true
  showAddOrderForm.value = false
  editingOrderId.value = null
  // checkOrdersChatMessages.value = []
  checkOrdersUserMessage.value = ''
  try {
    const [decRes, profitRes, timeRes] = await Promise.all([
      api.getBotDecisions(100, props.bot.id),
      api.getBotProfit().catch(() => ({ data: null })),
      api.getServerTime().catch(() => ({ data: { server_time_formatted: 'Unknown' } }))
    ])
    orders.value = decRes.data?.decisions ?? []
    profit.value = profitRes?.data ?? null
    serverTime.value = timeRes?.data?.server_time_formatted ?? ''
  } catch (e) {
    orders.value = []
    console.error('Failed to load orders:', e)
  } finally {
    loadingOrders.value = false
  }
  // Removed auto-greeting logic
  scrollCheckOrdersChat()
}

const closeOrdersModal = () => {
  showOrdersModal.value = false
  // checkOrdersChatMessages.value = []
  checkOrdersUserMessage.value = ''
  showAddOrderForm.value = false
  editingOrderId.value = null
}

const scrollCheckOrdersChat = async () => {
  await nextTick()
  if (checkOrdersChatRef.value) {
    checkOrdersChatRef.value.scrollTop = checkOrdersChatRef.value.scrollHeight
  }
}

const formatPct = (v) => {
  if (v == null || v === undefined) return '—'
  const n = Number(v)
  if (isNaN(n)) return '—'
  const s = n >= 0 ? '+' : ''
  return `${s}${n.toFixed(2)}%`
}

const formatCur = (v) => {
  if (v == null || v === undefined) return '—'
  const n = Number(v)
  if (isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(n)
}

const toDatetimeLocal = (iso) => {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${y}-${m}-${day}T${h}:${min}`
  } catch {
    return ''
  }
}

const fromDatetimeLocal = (local) => {
  if (!local) return null
  try {
    return new Date(local).toISOString()
  } catch {
    return null
  }
}

const loadOrders = async () => {
  try {
    const res = await api.getBotDecisions(100, props.bot.id)
    orders.value = res.data?.decisions ?? []
  } catch (e) {
    console.error('Failed to reload orders:', e)
  }
}

const createOrder = async () => {
  const sym = (newOrder.value.symbol || '').trim().toUpperCase()
  if (!sym) return
  try {
    await api.createBotDecision({
      bot_id: props.bot.id,
      symbol: sym,
      decision: newOrder.value.decision || 'BUY',
      execution_time: fromDatetimeLocal(newOrder.value.execution_time) || undefined,
      reasoning: (newOrder.value.reasoning || '').trim() || undefined
    })
    newOrder.value = { symbol: '', decision: 'BUY', execution_time: '', reasoning: '' }
    showAddOrderForm.value = false
    await loadOrders()
  } catch (e) {
    console.error('Create order failed:', e)
  }
}

const cancelAddOrder = () => {
  showAddOrderForm.value = false
  newOrder.value = { symbol: '', decision: 'BUY', execution_time: '', reasoning: '' }
}

const startEdit = (d) => {
  editingOrderId.value = d.id
  editForm.value = {
    symbol: d.symbol || '',
    decision: d.decision || 'BUY',
    status: d.status || 'PENDING',
    execution_time: toDatetimeLocal(d.execution_time || d.created_at),
    reasoning: d.reasoning || ''
  }
}

const saveEdit = async (id) => {
  try {
    await api.updateBotDecision(id, {
      symbol: editForm.value.symbol,
      decision: editForm.value.decision,
      status: editForm.value.status,
      execution_time: fromDatetimeLocal(editForm.value.execution_time) || undefined,
      reasoning: editForm.value.reasoning
    })
    editingOrderId.value = null
    await loadOrders()
  } catch (e) {
    console.error('Update order failed:', e)
  }
}

const cancelEdit = () => {
  editingOrderId.value = null
}

const deleteOrder = async (d) => {
  if (!confirm(`Delete order ${d.symbol} ${d.decision}?`)) return
  try {
    await api.deleteBotDecision(d.id)
    await loadOrders()
  } catch (e) {
    console.error('Delete order failed:', e)
  }
}

const sendCheckOrdersChat = async () => {
  if (!checkOrdersUserMessage.value.trim() || checkOrdersLoadingAi.value) return
  const message = checkOrdersUserMessage.value.trim()
  checkOrdersUserMessage.value = ''
  checkOrdersChatMessages.value.push({ role: 'user', content: message })
  scrollCheckOrdersChat()
  checkOrdersLoadingAi.value = true
  try {
    const history = checkOrdersChatMessages.value
      .filter(m => !m.error)
      .map(m => ({ role: m.role, content: m.content }))
    const res = await api.callGemini(props.bot.id, { prompt: message, history })
    checkOrdersChatMessages.value.push({ role: 'assistant', content: res.data.explanation })
  } catch (err) {
    checkOrdersChatMessages.value.push({
      role: 'assistant',
      content: 'Error: ' + (err.response?.data?.detail || err.message),
      error: true
    })
  } finally {
    checkOrdersLoadingAi.value = false
    scrollCheckOrdersChat()
  }
}

const formatOrderTime = (iso) => {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}


const clearChatHistory = () => {
  checkOrdersChatMessages.value = []
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

.activate-btn.active {
  background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
  color: #68d391;
  border: 1px solid #68d391;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.time-btn {
  background: linear-gradient(135deg, #718096 0%, #4a5568 100%);
  color: white;
}

.time-btn:hover {
  background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.check-orders-big {
  width: 100%;
  margin-top: 16px;
  padding: 16px 24px;
  font-size: 18px;
  font-weight: 700;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(237, 137, 54, 0.3);
  transition: all 0.2s ease;
}

.check-orders-big:hover {
  background: linear-gradient(135deg, #f6ad55 0%, #ed8936 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(237, 137, 54, 0.4);
}

.check-orders-big:active {
  transform: translateY(0);
}

.check-orders-panel {
  width: 90vw !important;
  max-width: 1200px !important;
  height: 85vh !important;
  display: flex !important;
  flex-direction: column;
}

.chat-input-container {
  display: flex;
  gap: 8px;
  padding-top: 10px;
}

.btn-clear-history {
  background: #2d3748;
  border: 1px solid #4a5568;
  color: #a0aec0;
  border-radius: 8px;
  cursor: pointer;
  padding: 0 12px;
  font-size: 16px;
  transition: all 0.2s;
}

.btn-clear-history:hover {
  background: #e53e3e;
  color: white;
  border-color: #e53e3e;
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
}

/* Check Orders panel – larger modal */
.check-orders-overlay .modal-content {
  width: 95vw;
  max-width: 1100px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.check-orders-panel {
  background: #2d3748;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.check-orders-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding: 16px 24px;
  background: #1a202c;
  border-bottom: 1px solid #4a5568;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #a0aec0;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
}

.summary-value.positive { color: #68d391; }
.summary-value.negative { color: #fc8181; }
.summary-value.muted { font-size: 13px; font-weight: 500; color: #718096; }

.orders-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 16px 24px;
  overflow: hidden;
}

.orders-toolbar {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.btn-add-order {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 600;
  background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-add-order:hover {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

.add-order-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.add-input, .add-select {
  padding: 8px 12px;
  font-size: 13px;
  background: #1a202c;
  border: 1px solid #4a5568;
  border-radius: 6px;
  color: #e2e8f0;
}

.add-input { min-width: 100px; }
.add-input[placeholder="Reasoning"] { min-width: 160px; }

.btn-save {
  padding: 8px 14px;
  font-weight: 600;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-save:hover { background: #3182ce; }

.add-order-form .btn-cancel {
  padding: 8px 14px;
  font-weight: 600;
  background: #4a5568;
  color: #e2e8f0;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.add-order-form .btn-cancel:hover { background: #718096; }

.orders-table-wrap {
  flex: 1;
  min-height: 120px;
  overflow: auto;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.orders-table th, .orders-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #2d3748;
}

.orders-table th {
  background: #1a202c;
  color: #a0aec0;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.orders-table tbody tr.order-row { background: #1a202c; }
.orders-table tbody tr.order-row:hover { background: #2d3748; }
.orders-table tbody tr.order-row.buy { border-left: 4px solid #68d391; }
.orders-table tbody tr.order-row.sell { border-left: 4px solid #fc8181; }
.orders-table tbody tr.order-row.hold,
.orders-table tbody tr.order-row.wait { border-left: 4px solid #ecc94b; }

.order-symbol { font-weight: 700; color: #e2e8f0; }
.order-decision { font-weight: 600; text-transform: uppercase; }
.order-row.buy .order-decision { color: #68d391; }
.order-row.sell .order-decision { color: #fc8181; }
.order-row.hold .order-decision, .order-row.wait .order-decision { color: #ecc94b; }
.order-status { color: #a0aec0; }
.order-time { color: #718096; font-size: 12px; }
.order-reasoning-cell { color: #cbd5e0; font-size: 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.edit-input, .edit-select {
  width: 100%;
  min-width: 60px;
  padding: 6px 10px;
  font-size: 13px;
  background: #2d3748;
  border: 1px solid #4a5568;
  border-radius: 4px;
  color: #e2e8f0;
}

.actions-cell { white-space: nowrap; }
.btn-icon {
  padding: 6px 10px;
  margin-right: 4px;
  font-size: 14px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: #4a5568;
  color: #e2e8f0;
}
.btn-icon:hover { background: #718096; }
.btn-icon.save { background: #38a169; color: white; }
.btn-icon.save:hover { background: #48bb78; }
.btn-icon.cancel { background: #4a5568; }
.btn-icon.btn-edit { background: #4299e1; color: white; }
.btn-icon.btn-edit:hover { background: #63b3ed; }
.btn-icon.btn-del { background: #e53e3e; color: white; }
.btn-icon.btn-del:hover { background: #fc8181; }

.orders-empty {
  text-align: center;
  color: #a0aec0;
  padding: 32px 16px;
}

.check-orders-chat {
  border-top: 1px solid #4a5568;
  display: flex;
  flex-direction: column;
  min-height: 220px;
  max-height: 320px;
}

.check-orders-chat .chat-body {
  flex: 1;
  height: 180px;
  overflow-y: auto;
  padding: 12px 24px;
  background: #1a202c;
}

.check-orders-chat .chat-input-container {
  display: flex;
  gap: 10px;
  padding: 12px 24px;
  background: #2d3748;
  border-top: 1px solid #4a5568;
}

.check-orders-chat .chat-input {
  flex: 1;
  padding: 10px 14px;
  background: #1a202c;
  border: 1px solid #4a5568;
  border-radius: 8px;
  color: white;
  font-size: 14px;
}

.check-orders-chat .send-btn {
  padding: 10px 20px;
  font-weight: 600;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.check-orders-chat .send-btn:hover:not(:disabled) { background: #3182ce; }
.check-orders-chat .send-btn:disabled { background: #4a5568; cursor: not-allowed; opacity: 0.7; }
</style>

