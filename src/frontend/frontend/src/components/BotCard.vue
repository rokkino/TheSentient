<template>
  <div class="bot-card">
    <div class="bot-header">
      <div class="bot-avatar">
        <img src="../assets/bot_icon.jpg" alt="Bot Icon" class="bot-icon-img" />
      </div>
      <div class="bot-info">
        <h3 class="bot-name">{{ bot.name }}</h3>
        <p class="bot-owner">by {{ bot.owner || 'You' }}</p>
      </div>
      <div class="bot-status-row">
        <div class="bot-status" :class="bot.status?.toLowerCase() || 'inactive'">
          <span class="status-dot"></span>
          {{ (bot.status || 'INACTIVE').toUpperCase() }}
        </div>
        <div v-if="(bot.status === 'active') && (bot.activatedAt || bot.activated_at)" class="bot-active-since" :title="formatActiveSince(bot.activatedAt || bot.activated_at)">
          <span class="start-flag-icon" aria-hidden="true">🏁</span>
          <span>Attivo dal {{ formatActiveSince(bot.activatedAt || bot.activated_at) }}</span>
        </div>
      </div>
      <div class="menu-container header-menu" ref="menuContainer">
        <button 
          class="action-btn menu-btn" 
          @click.stop="toggleMenu"
          title="More options"
        >
          <Menu :size="18" />
        </button>
        <Transition name="fade">
          <div v-if="showMenu" class="dropdown-menu">
            <div class="dropdown-item" @click="handleAction('import')">
              <Download :size="16" />
              <span>Import</span>
            </div>
            <div class="dropdown-item" @click="handleAction('export')">
              <Upload :size="16" />
              <span>Export</span>
            </div>
          </div>
        </Transition>
      </div>
    </div>
    
    <div class="bot-stats">
      <div class="stat-item">
        <span class="stat-label">Win Rate</span>
        <span class="stat-value">{{ (bot.win_rate || 0).toFixed(0) }}%</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">Total Trades</span>
        <span class="stat-value">{{ bot.total_trades || 0 }}</span>
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
          </div>

          <div class="orders-section">
            <div class="orders-toolbar">
              <button class="btn-add-order" @click="openAddOrderForm" v-if="!showAddOrderForm">
                + Add order
              </button>
              <div v-if="showAddOrderForm" class="add-order-form">
                <div class="symbol-input-wrapper">
                  <input 
                    :value="newOrder.symbol"
                    @input="handleSymbolSearch"
                    @blur="closeSearch"
                    placeholder="Symbol" 
                    class="add-input symbol-input" 
                    autocomplete="off"
                  />
                  <div v-if="showSearchResults" class="search-results">
                    <div 
                      v-for="asset in searchResults" 
                      :key="asset.symbol" 
                      class="search-result-item"
                      @click="selectAsset(asset)"
                    >
                      <span class="result-symbol">{{ asset.symbol }}</span>
                      <span class="result-name">{{ asset.name }}</span>
                    </div>
                  </div>
                </div>
                <select v-model="newOrder.decision" class="add-select">
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                  <option value="HOLD">HOLD</option>
                  <option value="WAIT">WAIT</option>
                </select>
                <div class="datetime-row">
                  <input v-model="newOrder.execution_time" type="datetime-local" class="add-input datetime-input" />
                  <div class="time-quick-btns">
                    <button type="button" class="time-btn" @click="setNewOrderTimeNow" title="Ora attuale">Ora</button>
                    <button type="button" class="time-btn" @click="addMinutesToNewOrder(15)">+15 min</button>
                    <button type="button" class="time-btn" @click="addMinutesToNewOrder(60)">+1 h</button>
                  </div>
                </div>
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
              <div class="orders-table-container">
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
                      v-for="d in paginatedOrders" 
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
                        <div class="datetime-row edit-datetime">
                          <input v-model="editForm.execution_time" type="datetime-local" class="edit-input datetime-input" />
                          <div class="time-quick-btns">
                            <button type="button" class="time-btn" @click="setEditFormTimeNow" title="Ora attuale">Ora</button>
                            <button type="button" class="time-btn" @click="addMinutesToEditForm(15)">+15 min</button>
                            <button type="button" class="time-btn" @click="addMinutesToEditForm(60)">+1 h</button>
                          </div>
                        </div>
                      </td>
                      <td v-if="editingOrderId !== d.id">
                        <div class="order-reasoning-cell" :title="d.reasoning">{{ d.reasoning || '—' }}</div>
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
                           <button 
                            class="btn-icon btn-exec" 
                            v-if="d.status === 'PENDING' || d.status === 'FAILED'"
                            @click="executeOrder(d)" 
                            title="Execute Now (Real Order)"
                          >
                            🚀
                          </button>
                          <button class="btn-icon btn-edit" @click="startEdit(d)" title="Edit">✎</button>
                          <button class="btn-icon btn-del" @click="deleteOrder(d)" title="Delete">⌫</button>
                        </template>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <div v-if="totalPages > 1" class="pagination-controls">
                <button 
                  class="page-btn" 
                  :disabled="currentPage === 1" 
                  @click="currentPage--"
                >
                  &lt; Prev
                </button>
                <span class="page-info">Page {{ currentPage }} of {{ totalPages }}</span>
                <button 
                  class="page-btn" 
                  :disabled="currentPage === totalPages" 
                  @click="currentPage++"
                >
                  Next &gt;
                </button>
              </div>
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
import { ref, nextTick, computed } from 'vue'
import api from '../services/api'
import { Menu, Download, Upload } from 'lucide-vue-next'
import { onClickOutside } from '@vueuse/core'

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
const showMenu = ref(false) 
const menuContainer = ref(null)

const toggleMenu = () => {
    showMenu.value = !showMenu.value
}

const closeMenu = () => {
    showMenu.value = false
}

const handleAction = (action) => {
    emit(action, props.bot)
    closeMenu()
}

onClickOutside(menuContainer, () => {
  showMenu.value = false
})

const serverTime = ref('')

const currentPage = ref(1)
const itemsPerPage = 8

const totalPages = computed(() => {
  return Math.ceil(orders.value.length / itemsPerPage) || 1
})

const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return orders.value.slice(start, end)
})
// Autocomplete state
const searchResults = ref([])
const showSearchResults = ref(false)
const searchLoading = ref(false)
let searchTimeout = null

const handleSymbolSearch = (e) => {
  const query = e.target.value
  newOrder.value.symbol = query // update model
  
  if (searchTimeout) clearTimeout(searchTimeout)
  if (!query || query.length < 1) {
    searchResults.value = []
    showSearchResults.value = false
    return
  }
  
  searchTimeout = setTimeout(async () => {
    searchLoading.value = true
    try {
      console.log(`Searching for: ${query}`)
      const res = await api.searchAlpacaAssets(query)
      console.log('Search results:', res.data)
      searchResults.value = res.data?.results || []
      showSearchResults.value = searchResults.value.length > 0
      if (searchResults.value.length === 0) {
        console.warn('No results found. Check backend logs or Alpaca configuration.')
      }
    } catch (e) {
      console.error('Search failed', e)
    } finally {
      searchLoading.value = false
    }
  }, 300)
}

const selectAsset = (asset) => {
  newOrder.value.symbol = asset.symbol
  showSearchResults.value = false
  searchResults.value = []
}

// Close search results when clicking outside
const closeSearch = () => {
  // Delay to allow click event on result item to trigger first
  setTimeout(() => {
    showSearchResults.value = false
  }, 200)
}

const openCheckOrdersModal = async () => {
  showOrdersModal.value = true
  profit.value = null
  orders.value = []
  loadingOrders.value = true
  showAddOrderForm.value = false
  editingOrderId.value = null
  currentPage.value = 1
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

const formatActiveSince = (dateStr) => {
  if (!dateStr) return '—'
  const d = typeof dateStr === 'string' ? new Date(dateStr) : dateStr
  if (isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
}

const getNowDatetimeLocal = () => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day}T${h}:${min}`
}

const addMinutesToDatetimeLocal = (localStr, minutes) => {
  const base = localStr && localStr.length >= 16 ? new Date(localStr) : new Date()
  base.setMinutes(base.getMinutes() + minutes)
  const d = base
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day}T${h}:${min}`
}

const openAddOrderForm = () => {
  showAddOrderForm.value = true
  newOrder.value.execution_time = getNowDatetimeLocal()
}

const setNewOrderTimeNow = () => {
  newOrder.value.execution_time = getNowDatetimeLocal()
}
const addMinutesToNewOrder = (minutes) => {
  newOrder.value.execution_time = addMinutesToDatetimeLocal(newOrder.value.execution_time, minutes)
}

const setEditFormTimeNow = () => {
  editForm.value.execution_time = getNowDatetimeLocal()
}
const addMinutesToEditForm = (minutes) => {
  editForm.value.execution_time = addMinutesToDatetimeLocal(editForm.value.execution_time, minutes)
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
  let sym = (newOrder.value.symbol || '').trim().toUpperCase()
  if (!sym) {
    alert('Please enter a symbol')
    return
  }
  
  // Symbol normalization - map common alternatives to official tickers
  const symbolMap = {
    'GOLD': 'GLD', 'XAU': 'GLD', 'XAUUSD': 'GLD',
    'SILVER': 'SLV', 'XAG': 'SLV', 'XAGUSD': 'SLV',
    'OIL': 'USO', 'CRUDE': 'USO', 'WTI': 'USO',
    'BITCOIN': 'BITO', 'BTC': 'BITO', 'BTCUSD': 'BITO',
    'ETHEREUM': 'ETHE', 'ETH': 'ETHE', 'ETHUSD': 'ETHE',
    'NVIDIA': 'NVDA', 'NV': 'NVDA',  // Add NVIDIA mapping
    'APPLE': 'AAPL',
    'TESLA': 'TSLA',
    'MICROSOFT': 'MSFT', 'MS': 'MSFT',
    'GOOGLE': 'GOOGL',
    'AMAZON': 'AMZN',
    'META': 'META', 'FACEBOOK': 'META', 'FB': 'META'
  }
  
  const originalSym = sym
  if (symbolMap[sym]) {
    sym = symbolMap[sym]
    console.log(`Symbol normalized: ${originalSym} → ${sym}`)
  }
  
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
    let detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      detail = detail.map((x) => (x.msg || x.message || JSON.stringify(x))).join('; ')
    } else if (typeof detail !== 'string') {
      detail = detail || e.message || String(e)
    }
    alert(`Failed to create order: ${detail}`)
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

const executeOrder = async (d) => {
  console.log('executeOrder called with:', d)
  if (!d || !d.id) {
    console.error('Invalid decision object:', d)
    alert('Error: Invalid order data (missing ID)')
    return
  }

  if (!confirm(`Are you sure you want to EXECUTE ${d.decision} ${d.symbol} for an estimated $1000?`)) return
  if (d.status === 'EXECUTED') return
  
  // Optimistic update
  const originalStatus = d.status
  d.status = 'EXECUTING...'
  
  try {
    console.log(`Executing order ID: ${d.id}`)
    const res = await api.executeBotDecision(d.id)
    console.log('Order executed:', res.data)
    alert(`Order executed successfully! ID: ${res.data.id}`)
    await loadOrders()
    // Refresh profit display
    try {
       const profitRes = await api.getBotProfit()
       profit.value = profitRes.data
    } catch(e) {}
  } catch (e) {
    console.error('Execute order failed:', e)
    const detail = e.response?.data?.detail || e.message || ''
    const s = typeof detail === 'string' ? detail.toLowerCase() : ''
    let message
    if (s.includes('alpaca library not installed') || s.includes('alpaca-py'))
      message = 'Backend non aggiornato: chiudi TUTTE le finestre del backend, poi esegui restart-backend.bat (o: cd backend && python main.py). Poi ricarica la pagina e riprova.'
    else if (s.includes('unauthorized') || s.includes('credenziali non valide'))
      message = 'Alpaca: credenziali non valide. Vai nel profilo del bot, verifica API Key e Secret (Paper o Live) e che l\'account Alpaca sia attivo.'
    else
      message = `Execution Failed: ${detail}`
    alert(message)
    d.status = originalStatus
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
  flex-wrap: wrap;
}

.bot-header .menu-container.header-menu {
  margin-left: auto;
}

.bot-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: white; /* Changed from gradient to white for image background if transparent, though image is jpg */
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  border: 2px solid #4a5568;
}

.bot-icon-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Removed old bot-icon style */

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

.bot-status-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
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

.bot-active-since {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #a0aec0;
  font-weight: 500;
}

.bot-active-since .start-flag-icon {
  font-size: 14px;
  line-height: 1;
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

.menu-container {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 5px;
  background: #2d3748;
  border: 1px solid #4a5568;
  border-radius: 8px;
  padding: 5px;
  z-index: 10;
  min-width: 120px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dropdown-item {
  background: transparent;
  border: none;
  color: #e2e8f0;
  padding: 8px 12px;
  text-align: left;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s;
  width: 100%;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.1);
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

.symbol-input-wrapper {
  position: relative;
  width: 120px;
}

.symbol-input {
  width: 100%;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  width: 300px;
  max-height: 200px;
  overflow-y: auto;
  background: #2d3748;
  border: 1px solid #4a5568;
  border-radius: 4px;
  z-index: 1000;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid #4a5568;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background: #4a5568;
}

.result-symbol {
  font-weight: bold;
  color: #e2e8f0;
}

.result-name {
  color: #a0aec0;
  font-size: 0.9em;
  margin-left: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  width: 95vw !important;
  max-width: 1000px !important;
  height: auto !important;
  max-height: 90vh !important;
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

@media (max-width: 768px) {
  .bot-card {
    padding: 18px;
    border-radius: 14px;
  }

  .bot-header {
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
  }

  .bot-avatar {
    width: 48px;
    height: 48px;
  }

  .bot-name {
    font-size: 18px;
  }

  .bot-owner {
    font-size: 13px;
  }

  .bot-status-row {
    width: 100%;
  }

  .bot-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .stat-item {
    padding: 10px;
  }

  .stat-label {
    font-size: 10px;
  }

  .stat-value {
    font-size: 20px;
  }

  .bot-actions {
    gap: 10px;
  }

  .action-btn {
    min-height: 40px;
  }

  .check-orders-panel {
    max-height: 92vh;
  }

  .check-orders-summary {
    padding: 10px 16px;
    gap: 12px;
  }

  .orders-section {
    padding: 12px 16px;
  }

  .orders-table th,
  .orders-table td {
    font-size: 12px;
    padding: 6px 8px;
  }

  .check-orders-chat .chat-body {
    padding: 12px 16px;
  }

  .check-orders-chat .chat-input-container {
    padding: 10px 16px;
  }
}

@media (max-width: 480px) {
  .bot-card {
    padding: 16px;
  }

  .bot-stats {
    grid-template-columns: 1fr 1fr;
  }

  .bot-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .check-orders-summary {
    flex-direction: column;
  }

  .orders-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-add-order {
    width: 100%;
  }

  .add-order-form {
    flex-direction: column;
    align-items: stretch;
  }

  .add-input,
  .add-select,
  .datetime-input {
    width: 100%;
    min-width: 0;
  }

  .time-quick-btns {
    width: 100%;
    justify-content: space-between;
  }

  .orders-table-container {
    border-radius: 10px;
  }

  .orders-table {
    font-size: 12px;
  }

  .orders-table th,
  .orders-table td {
    white-space: nowrap;
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
  max-width: 1000px;
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
  padding: 12px 24px;
  background: #1a202c;
  border-bottom: 1px solid #4a5568;
  flex-shrink: 0;
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
  flex-shrink: 0;
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

.datetime-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.datetime-input {
  min-width: 180px;
}
.time-quick-btns {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.datetime-row.edit-datetime {
  flex-direction: column;
  align-items: flex-start;
}
.datetime-row.edit-datetime .time-quick-btns {
  margin-top: 4px;
}

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
  min-height: 0;
  overflow: hidden; /* Changed from auto to hidden, inner container scrolls */
  display: flex;
  flex-direction: column;
}

.orders-table-container {
  flex: 1;
  overflow: auto;
}

.orders-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.orders-table th, .orders-table td {
  padding: 8px 10px; /* Condensed padding */
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
.order-reasoning-cell { 
  color: #cbd5e0; 
  font-size: 12px; 
  max-width: 300px; 
  overflow: hidden; 
  text-overflow: ellipsis; 
  white-space: nowrap; 
}

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
  height: 200px; /* Fixed smaller height */
  flex-shrink: 0;
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

.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: #1a202c;
  border-top: 1px solid #2d3748;
  margin-top: auto;
}

.page-btn {
  padding: 4px 12px;
  background: #2d3748;
  border: 1px solid #4a5568;
  border-radius: 6px;
  color: #e2e8f0;
  cursor: pointer;
  font-size: 12px;
}

.page-btn:hover:not(:disabled) {
  background: #4a5568;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 12px;
  color: #a0aec0;
}

/* Search Autocomplete Styles */
.symbol-input-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #2d3748;
  border: 1px solid #4a5568;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 9999; /* High z-index to ensure visibility */
  margin-top: 4px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.3);
}

.search-result-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #4a5568;
  gap: 8px;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background: #4a5568;
}

.result-symbol { 
  font-weight: bold; 
  color: #e2e8f0; 
  font-size: 13px;
}

.result-name { 
  font-size: 11px; 
  color: #a0aec0; 
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

/* Premium Menu Styles */

.menu-container {
  position: relative;
  z-index: 20;
}

/* Override .action-btn styles for the menu button to look like a ghost button */
.action-btn.menu-btn {
  width: 36px;
  height: 36px;
  min-width: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid transparent; /* Ghost style default */
  color: #a0aec0;
  box-shadow: none;
  flex: 0 0 auto;
  transition: all 0.2s ease;
}

.action-btn.menu-btn:hover {
  background: rgba(255, 255, 255, 0.08); /* Subtle hover bg */
  color: #e2e8f0;
  border-color: rgba(255, 255, 255, 0.1);
  transform: none; /* No lift for ghost buttons generally, or subtle */
}

/* Dropdown Menu */
.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: #2d3748; /* Matching card or slightly darker diff */
  border: 1px solid #4a5568;
  border-radius: 8px;
  padding: 6px;
  min-width: 140px;
  box-shadow: 
    0 10px 15px -3px rgba(0, 0, 0, 0.5), /* Deep shadow */
    0 4px 6px -2px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 50;
  transform-origin: top right;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.dropdown-item:hover {
  background: rgba(66, 153, 225, 0.15); /* Tint of blue on hover */
  color: #63b3ed; /* Active blue color text */
}

.dropdown-item span {
  flex: 1;
}

/* Vue Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
</style>