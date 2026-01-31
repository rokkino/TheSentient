<template>
  <div class="flex-chat">
    <div class="chat-header">
      <div class="header-content">
        <div class="header-left">
          <h2>{{ chatTitle }}</h2>
          <div class="chat-info">
            <span class="online-indicator"></span>
            <span class="online-count">{{ visibleOnlineCount }} online</span>
          </div>
        </div>
        <button class="settings-btn" @click="showSettings = true" title="Chat Settings">
          ⚙️
        </button>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>Loading chat history...</span>
      </div>
      
      <div
        v-else
        v-for="message in messages"
        :key="message.id"
        :class="['message', { 'own-message': message.user_id === currentUserId }]"
        @contextmenu.prevent="showContextMenu($event, message)"
      >
        <div class="message-avatar">
          <img 
            v-if="message.profile_picture_url" 
            :src="getProfilePictureUrl(message.profile_picture_url, message.user_id)" 
            :alt="message.username"
            class="avatar-image"
          />
          <span v-else>{{ getInitials(message.username) }}</span>
        </div>
        <div class="message-content-wrapper">
          <div class="message-header">
            <span class="message-username">{{ message.username }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-bubble">
            <p v-if="message.type === 'text'" style="white-space: pre-wrap;">{{ message.message }}</p>
            <img
              v-else-if="message.type === 'image' && message.image_data"
              :src="`data:image/jpeg;base64,${message.image_data}`"
              alt="Shared image"
              class="message-image"
              @click="openImageModal(message.image_data)"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-container">
      <div class="input-wrapper" :class="{ 'search-mode': isSearchMode }">
        <div class="input-actions">
          <button 
            class="action-btn search-btn" 
            :class="{ active: isSearchMode }"
            @click="toggleSearchMode"
            title="Toggle Web Search"
          >
            <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <path d="m21 21-4.35-4.35"/>
            </svg>
          </button>
          <div class="action-divider" v-if="!isSearchMode"></div>
          <label class="action-btn upload-btn" title="Upload Image" v-if="!isSearchMode">
            <input
              type="file"
              accept="image/*"
              @change="handleImageSelect"
              style="display: none"
            />
            <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
              <circle cx="12" cy="13" r="3"/>
            </svg>
          </label>
          <label class="action-btn upload-btn" title="Upload Document" v-if="!isSearchMode">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              @change="handleDocumentSelect"
              style="display: none"
            />
            <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </label>
        </div>
        
        <input
          v-model="newMessage"
          @keydown.enter.prevent="sendMessage"
          :placeholder="isSearchMode ? 'Search the web...' : 'Type a message...'"
          class="chat-input"
          :disabled="sending"
        />
        
        <button
          @click="sendMessage"
          :disabled="!canSend || sending"
          class="send-btn"
          :class="{ 'search-send-btn': isSearchMode }"
        >
          {{ sending ? '...' : (isSearchMode ? 'Search' : 'Send') }}
        </button>
      </div>
      
      <div v-if="selectedImage || selectedDocument" class="preview-area">
        <span v-if="selectedImage" class="preview-item">
          📷 Image selected
          <button @click="clearAttachments" class="clear-btn">×</button>
        </span>
        <span v-if="selectedDocument" class="preview-item">
          📄 {{ selectedDocument.name }}
          <button @click="clearAttachments" class="clear-btn">×</button>
        </span>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <div v-if="imageModalOpen" class="image-modal" @click="imageModalOpen = false">
      <div class="image-modal-content" @click.stop>
        <button class="close-modal" @click="imageModalOpen = false">×</button>
        <img :src="`data:image/jpeg;base64,${modalImageData}`" alt="Full size image" />
      </div>
    </div>

    <!-- Settings Modal -->
    <div v-if="showSettings" class="modal-overlay" @click="showSettings = false">
      <div class="modal-content settings-modal" @click.stop>
        <div class="modal-header">
          <h3>Chat Settings</h3>
          <button class="close-btn" @click="showSettings = false">×</button>
        </div>
        <div class="modal-body">
          <div class="setting-group">
            <label>Chat With:</label>
            <select v-model="config.recipientId" class="form-select" @change="onRecipientSelectChange">
              <option :value="null">Everyone (Public)</option>
              <option 
                v-for="user in visibleOnlineUsers" 
                :key="user.id" 
                :value="user.id"
                v-show="user.id !== currentUserId"
              >
                {{ user.username }}
              </option>
            </select>
          </div>
          <div class="setting-group">
            <label>Chat privata – inserisci username:</label>
            <div class="private-chat-input-row">
              <input
                v-model="privateChatUsername"
                type="text"
                class="form-input private-chat-input"
                placeholder="es. mario, lucy"
                @keydown.enter="openPrivateChatByUsername"
              />
              <button type="button" class="btn-private-chat" @click="openPrivateChatByUsername">
                Apri chat
              </button>
            </div>
            <p v-if="privateChatError" class="setting-hint error-hint">{{ privateChatError }}</p>
          </div>
          
            <div class="setting-group checkbox-group">
              <label class="checkbox-label">
                <input type="checkbox" v-model="config.inviteAi" @change="updateConfig">
                Invite AI Agent
              </label>
              <p class="setting-hint">If enabled, AI will read messages and respond when relevant.</p>
            </div>
            
            <div class="setting-group danger-zone">
              <label>Danger Zone</label>
              <button class="clear-history-btn" @click="clearHistory">
                🗑️ Clear Chat History
              </button>
            </div>
        </div>
      </div>
    </div>

    <!-- Context Menu -->
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }"
      @click.stop
    >
      <div class="context-menu-item delete" @click="deleteMessage(contextMenu.messageId)">
        Delete Message
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const props = defineProps({
  tabId: {
    type: Number,
    default: null
  },
  initialConfig: {
    type: Object,
    default: () => ({
      recipientId: null,
      inviteAi: false
    })
  }
})

const emit = defineEmits(['update-config'])

const authStore = useAuthStore()

const messages = ref([])
const newMessage = ref('')
const selectedImage = ref(null)
const selectedDocument = ref(null)
const sending = ref(false)
const loading = ref(true)
const messagesContainer = ref(null)
const imageModalOpen = ref(false)
const modalImageData = ref(null)
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  messageId: null
})

const onlineUsersList = ref([])
const onlineUsersCount = ref(0)
const ws = ref(null)
const showSettings = ref(false)
const config = ref({ ...props.initialConfig })
const isSearchMode = ref(false)
const privateChatUsername = ref('')
const privateChatError = ref('')
const recipientUsernameOverride = ref(null)

const currentUserId = computed(() => authStore.user?.id)

const visibleOnlineUsers = computed(() => {
  const real = onlineUsersList.value.filter(user => typeof user.id === 'number' && user.id > 0)
  if (!config.value.inviteAi && config.value.recipientId !== -2) {
    return real
  }
  return [...real, { id: -2, username: 'Gemini AI' }]
})

const visibleOnlineCount = computed(() => {
  return visibleOnlineUsers.value.length
})

const availableUsers = computed(() => {
  return visibleOnlineUsers.value
})

const chatTitle = computed(() => {
  if (config.value.recipientId) {
    if (recipientUsernameOverride.value) return `Chat with ${recipientUsernameOverride.value}`
    const user = onlineUsersList.value.find(u => u.id === config.value.recipientId)
    return user ? `Chat with ${user.username}` : 'Private Chat'
  }
  return 'Chat'
})

const canSend = computed(() => {
  return (newMessage.value.trim().length > 0 || selectedImage.value || selectedDocument.value) && !sending.value
})

const getInitials = (username) => {
  if (!username) return 'GU'
  return username.substring(0, 2).toUpperCase()
}

const getProfilePictureUrl = (url, userId) => {
  // Custom icons for AI bots (Llama removed)
  if (userId === -2) { // Gemini
    return 'https://upload.wikimedia.org/wikipedia/commons/8/8a/Google_Gemini_logo.svg'
  }

  if (!url) return null
  // If it's already a full URL, return as is
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  // If it's a relative URL, prepend the API base URL
  if (url.startsWith('/')) {
    return `${API_URL}${url}`
  }
  return url
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return 'just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const handleImageSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (!file.type.startsWith('image/')) {
    alert('Please select an image file')
    return
  }
  
  if (file.size > 5 * 1024 * 1024) { // 5MB limit
    alert('Image size must be less than 5MB')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    // Convert to base64
    const base64 = e.target.result.split(',')[1] // Remove data:image/...;base64, prefix
    selectedImage.value = base64
  }
  reader.readAsDataURL(file)
}

const toggleSearchMode = () => {
  isSearchMode.value = !isSearchMode.value
  if (isSearchMode.value) {
    clearAttachments()
  }
}

const handleDocumentSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // Basic validation
  if (file.size > 10 * 1024 * 1024) { // 10MB limit
    alert('Document size must be less than 10MB')
    return
  }
  
  selectedDocument.value = {
    name: file.name,
    file: file
  }
  // Note: Actual document upload implementation would go here
  // For now we just show the UI state
}

const clearAttachments = () => {
  selectedImage.value = null
  selectedDocument.value = null
}

const onRecipientSelectChange = () => {
  recipientUsernameOverride.value = null
  privateChatError.value = ''
  updateConfig()
}

const openPrivateChatByUsername = async () => {
  const username = (privateChatUsername.value || '').trim()
  if (!username) {
    privateChatError.value = 'Inserisci un username.'
    return
  }
  privateChatError.value = ''
  try {
    const { data } = await api.getUserByUsername(username)
    if (data && data.id) {
      config.value.recipientId = data.id
      recipientUsernameOverride.value = data.username
      privateChatUsername.value = ''
      emit('update-config', config.value)
      loadMessages()
      showSettings.value = false
    }
  } catch (err) {
    const msg = err.response?.data?.detail || err.message
    privateChatError.value = typeof msg === 'string' ? msg : 'Utente non trovato.'
  }
}

const updateConfig = () => {
  // Check for changes in AI invitation status
  if (config.value.inviteAi !== props.initialConfig.inviteAi) {
    const action = config.value.inviteAi ? 'joined' : 'left'
    // We don't know exactly which AI it is until we send a message, 
    // but we can guess based on provider or just say "AI Agent"
    const provider = authStore.user?.ai_provider || 'gemini'
    const aiName = 'Gemini AI'
    
    messages.value.push({
      id: Date.now(),
      user_id: -99, // System message
      username: 'System',
      message: `${aiName} has ${action} the chat`,
      type: 'text',
      timestamp: new Date().toISOString()
    })
  }

  emit('update-config', config.value)
  
  // Only reload messages if switching chat context
  if (config.value.recipientId !== props.initialConfig.recipientId) {
    loadMessages()
  }
  scrollToBottom()
}

const sendMessage = async () => {
  if (!canSend.value) return
  
  if (!authStore.isAuthenticated) {
    alert('Please login to send messages')
    return
  }
  
  sending.value = true
  
  try {
    // Determine which AI to invite based on user settings
    const aiProvider = authStore.user?.ai_provider || 'gemini'
    const useGemini = config.value.inviteAi && (aiProvider !== 'local' && aiProvider !== 'llama')

    const messageData = {
      message: newMessage.value || (selectedImage.value ? '📷 Image' : ''),
      type: selectedImage.value ? 'image' : 'text',
      image_data: selectedImage.value || null,
      recipient_id: config.value.recipientId,
      invite_llama: false,
      invite_gemini: useGemini,
      is_search: isSearchMode.value
    }
    
    const response = await api.sendChatMessage(messageData)
    
    newMessage.value = ''
    clearAttachments()
    if (isSearchMode.value) {
      isSearchMode.value = false // Reset search mode after sending
    }
    
    // Mostra subito il messaggio dalla risposta API
    const sentMsg = response?.data?.message
    if (sentMsg && !messages.value.some(m => m.id === sentMsg.id)) {
      messages.value.push(sentMsg)
      scrollToBottom()
    } else {
      // Fallback: ricarica messaggi se la risposta ha struttura diversa
      loadMessages()
    }
  } catch (error) {
    console.error('Error sending message:', error)
    alert('Failed to send message: ' + (error.response?.data?.detail || error.message))
  } finally {
    sending.value = false
  }
}

const loadMessages = async () => {
  loading.value = true
  try {
    const response = await api.getChatMessages(100, config.value.recipientId)
    messages.value = response.data.messages || []
    scrollToBottom()
  } catch (error) {
    console.error('Error loading messages:', error)
  } finally {
    loading.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const connectWebSocket = () => {
  // Usa stessa origine della pagina (funziona con proxy Vite in dev e nginx in prod)
  const WS_BASE = import.meta.env.VITE_WS_URL || (
    (typeof window !== 'undefined' && window.location)
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
      : 'ws://localhost:8000'
  )
  const wsUrl = `${WS_BASE}?token=${authStore.token || ''}`
  
  ws.value = new WebSocket(wsUrl)
  
  ws.value.onopen = () => {
    console.log('Chat WebSocket connected')
  }
  
  ws.value.onmessage = (event) => {
    const message = JSON.parse(event.data)
    
    if (message.type === 'chat_message') {
      // Evita duplicati (messaggio già mostrato dalla risposta API)
      if (messages.value.some(m => m.id === message.data?.id)) return
      
      // Filter messages if in private chat mode
      if (config.value.recipientId) {
        // Only show if it matches the conversation (either from me to them, or them to me)
        const isRelated = (message.data.user_id === config.value.recipientId && message.data.recipient_id === currentUserId.value) ||
                          (message.data.user_id === currentUserId.value && message.data.recipient_id === config.value.recipientId)
        
        if (isRelated) {
          messages.value.push(message.data)
          scrollToBottom()
        }
      } else {
        // Public chat: only show public messages
        if (!message.data.recipient_id) {
          messages.value.push(message.data)
          scrollToBottom()
        }
      }
    } else if (message.type === 'online_users') {
      onlineUsersCount.value = message.count || 0
      if (message.users) {
        onlineUsersList.value = message.users
      }
    } else if (message.type === 'message_deleted') {
      messages.value = messages.value.filter(m => m.id !== message.message_id)
    } else if (message.type === 'history_cleared') {
      // If public chat cleared (recipient_id is null) or private chat cleared (matches current recipient)
      if (message.recipient_id === config.value.recipientId) {
        messages.value = []
      }
    }
  }
  
  ws.value.onerror = (error) => {
    console.error('Chat WebSocket error:', error)
  }
  
  ws.value.onclose = () => {
    console.log('Chat WebSocket disconnected')
    // Reconnect after 3 seconds
    setTimeout(() => connectWebSocket(), 3000)
  }
}

const openImageModal = (imageData) => {
  modalImageData.value = imageData
  imageModalOpen.value = true
}

const showContextMenu = (event, message) => {
  // Only allow deleting own messages
  if (message.user_id !== currentUserId.value) return
  
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    messageId: message.id
  }
  
  // Close menu on click outside
  const closeMenu = () => {
    contextMenu.value.visible = false
    document.removeEventListener('click', closeMenu)
  }
  document.addEventListener('click', closeMenu)
}

const deleteMessage = async (messageId) => {
  if (!confirm('Are you sure you want to delete this message?')) return
  
  try {
    await api.deleteChatMessage(messageId)
    // Message removal will be handled by WebSocket event
  } catch (error) {
    console.error('Error deleting message:', error)
    alert('Failed to delete message')
  }
}

const clearHistory = async () => {
  if (!confirm('Are you sure you want to delete ALL messages in this chat? This cannot be undone.')) return
  
  try {
    await api.clearChatHistory(config.value.recipientId)
    showSettings.value = false
    // Clearing will be handled by WebSocket event
  } catch (error) {
    console.error('Error clearing history:', error)
    alert('Failed to clear history: ' + (error.response?.data?.detail || error.message))
  }
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// Watch for config changes from parent (if any)
// Watch for config changes from parent (if any)
watch(() => props.initialConfig, (newConfig, oldConfig) => {
  if (newConfig) {
    config.value = { ...newConfig }
    // Only reload messages if the recipient (chat room) changed
    if (newConfig.recipientId !== oldConfig?.recipientId) {
      loadMessages()
    }
  }
}, { deep: true })

onMounted(async () => {
  await loadMessages()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style scoped>
/* --- Palette: slate dark, accent blue #2563eb, no purple --- */
.flex-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0f172a;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.chat-header {
  padding: 14px 20px;
  background: #1e293b;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header h2 {
  font-size: 17px;
  font-weight: 600;
  color: #f8fafc;
  margin: 0;
  letter-spacing: -0.02em;
}

.chat-info {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.04);
  padding: 5px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.settings-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  transition: background-color 0.2s;
  padding: 6px;
  border-radius: 8px;
  opacity: 0.85;
}

.settings-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  opacity: 1;
}

.online-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #22c55e;
}

.online-count {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
  background: #0f172a;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #64748b;
  gap: 12px;
  font-size: 14px;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 2px solid rgba(255, 255, 255, 0.08);
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.message {
  display: flex;
  gap: 12px;
  max-width: 75%;
  animation: fadeIn 0.25s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.own-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 600;
  color: #cbd5e1;
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message.own-message .message-avatar {
  background: #1e40af;
  color: #fff;
}

.message-content-wrapper {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  padding: 0 2px;
}

.message-username {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}

.message.own-message .message-username {
  color: #cbd5e1;
}

.message-time {
  font-size: 11px;
  color: #64748b;
}

.message-bubble {
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  border-top-left-radius: 4px;
  padding: 12px 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
  position: relative;
}

.message:hover .message-bubble {
  border-color: rgba(255, 255, 255, 0.1);
}

.message.own-message .message-bubble {
  background: #1e40af;
  border-color: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border-top-right-radius: 4px;
}

.message.own-message:hover .message-bubble {
  background: #1d4ed8;
}

.message-bubble p {
  margin: 0;
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.55;
  word-wrap: break-word;
}

.message.own-message .message-bubble p {
  color: #f8fafc;
}

.message-image {
  max-width: 100%;
  max-height: 280px;
  border-radius: 10px;
  cursor: pointer;
  transition: opacity 0.2s;
  display: block;
}

.message-image:hover {
  opacity: 0.95;
}

/* --- Input bar: single surface, clean, professional --- */
.chat-input-container {
  padding: 16px 20px 20px;
  background: #0f172a;
  position: relative;
  z-index: 10;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 6px 10px 6px 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: rgba(37, 99, 235, 0.5);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.input-wrapper.search-mode {
  border-color: rgba(37, 99, 235, 0.6);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #f8fafc;
  padding: 10px 8px;
  font-size: 14px;
  outline: none;
}

.chat-input::placeholder {
  color: #64748b;
}

.send-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.15s;
  min-width: 76px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  background: #1d4ed8;
  transform: none;
}

.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.danger-zone {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.clear-history-btn {
  width: 100%;
  padding: 10px 14px;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.25);
  color: #f87171;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: background 0.2s, border-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.clear-history-btn:hover {
  background: rgba(248, 113, 113, 0.12);
  border-color: rgba(248, 113, 113, 0.4);
}


.input-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.action-divider {
  width: 1px;
  height: 18px;
  background: rgba(255, 255, 255, 0.1);
  margin: 0 2px;
}

.action-btn {
  cursor: pointer;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s, background-color 0.2s;
  color: #64748b;
  background: transparent;
  border: none;
}

.action-btn:hover {
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.06);
}

.action-btn:active {
  background: rgba(255, 255, 255, 0.08);
}

.action-btn.search-btn.active {
  color: #2563eb;
  background: rgba(37, 99, 235, 0.12);
}

.action-btn.search-btn.active .icon-svg {
  opacity: 1;
}

.icon-svg {
  width: 18px;
  height: 18px;
  position: relative;
  z-index: 1;
}

.send-btn.search-send-btn {
  background: #2563eb;
}


.preview-area {
  display: flex;
  gap: 10px;
  padding-left: 10px;
}

.preview-item {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.04);
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.clear-btn {
  background: none;
  border: none;
  color: #f87171;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(15, 23, 42, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(8px);
}

.image-modal-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
  animation: zoomIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes zoomIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.image-modal-content img {
  max-width: 100%;
  max-height: 90vh;
  border-radius: 10px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
}

.close-modal {
  position: absolute;
  top: -48px;
  right: 0;
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #f8fafc;
  font-size: 22px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-modal:hover {
  background: #334155;
}

/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(15, 23, 42, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(6px);
}

.modal-content {
  background-color: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-header h3 {
  margin: 0;
  color: #f8fafc;
  font-size: 17px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #64748b;
  font-size: 22px;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  border-radius: 6px;
  transition: color 0.2s, background 0.2s;
}

.close-btn:hover {
  color: #f8fafc;
  background: rgba(255, 255, 255, 0.06);
}

.modal-body {
  padding: 20px;
}

.setting-group {
  margin-bottom: 20px;
}

.setting-group label {
  display: block;
  color: #94a3b8;
  margin-bottom: 8px;
  font-size: 14px;
}

.form-select {
  width: 100%;
  padding: 10px 12px;
  background-color: #0f172a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #f8fafc;
  font-size: 14px;
}

.form-select:focus {
  outline: none;
  border-color: #2563eb;
}

.private-chat-input-row {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

.private-chat-input {
  flex: 1;
  padding: 10px 12px;
  background-color: #0f172a;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #f8fafc;
  font-size: 14px;
}

.private-chat-input:focus {
  outline: none;
  border-color: #2563eb;
}

.private-chat-input::placeholder {
  color: #64748b;
}

.btn-private-chat {
  padding: 10px 14px;
  background: #2563eb;
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.btn-private-chat:hover {
  background: #1d4ed8;
}

.setting-hint.error-hint {
  color: #f87171;
  margin-left: 0;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #2563eb;
}

.setting-hint {
  margin: 4px 0 0 28px;
  font-size: 12px;
  color: #64748b;
}

/* Context Menu */
.context-menu {
  position: fixed;
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 4px 0;
  min-width: 160px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  z-index: 9999;
}

.context-menu-item {
  padding: 10px 16px;
  font-size: 14px;
  color: #e2e8f0;
  cursor: pointer;
  transition: background-color 0.15s;
}

.context-menu-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.context-menu-item.delete {
  color: #f87171;
}

.context-menu-item.delete:hover {
  background: rgba(248, 113, 113, 0.1);
}

/* Mobile */
@media (max-width: 768px) {
  .flex-chat {
    border-radius: 0;
  }

  .chat-header {
    padding: 12px 16px;
  }

  .chat-header h2 {
    font-size: 15px;
  }

  .chat-info {
    padding: 4px 8px;
  }

  .online-count {
    font-size: 11px;
  }

  .chat-messages {
    padding: 12px 16px;
    gap: 12px;
    -webkit-overflow-scrolling: touch;
  }

  .message {
    max-width: 90%;
  }

  .message-avatar {
    width: 32px;
    height: 32px;
    font-size: 12px;
  }

  .message-bubble {
    padding: 10px 14px;
  }

  .message-bubble p {
    font-size: 13px;
  }

  .chat-input-container {
    padding: 12px 16px;
    padding-bottom: max(12px, env(safe-area-inset-bottom));
  }

  .input-wrapper {
    padding: 6px 8px 6px 12px;
  }

  .chat-input {
    font-size: 16px; /* Avoid zoom on iOS */
  }

  .send-btn {
    min-width: 64px;
    padding: 10px 14px;
    font-size: 13px;
  }

  .action-btn {
    width: 40px;
    height: 40px;
  }

  .modal-content.settings-modal {
    width: 95%;
    max-width: none;
    max-height: 85vh;
  }

  .modal-body {
    padding: 16px;
  }

  .context-menu {
    max-width: min(200px, calc(100vw - 24px));
  }
}

@media (max-width: 480px) {
  .chat-header {
    padding: 10px 12px;
  }

  .chat-header h2 {
    font-size: 14px;
  }

  .chat-messages {
    padding: 10px 12px;
  }

  .message-avatar {
    width: 28px;
    height: 28px;
    font-size: 10px;
  }

  .message-bubble p {
    font-size: 12px;
  }

  .chat-input-container {
    padding: 10px 12px;
  }
}
</style>
