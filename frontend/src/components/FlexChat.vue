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
            <span class="icon">🔍</span>
          </button>
          <label class="action-btn upload-btn" title="Upload Image" v-if="!isSearchMode">
            <input
              type="file"
              accept="image/*"
              @change="handleImageSelect"
              style="display: none"
            />
            <span class="icon">📷</span>
          </label>
          <label class="action-btn upload-btn" title="Upload Document" v-if="!isSearchMode">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              @change="handleDocumentSelect"
              style="display: none"
            />
            <span class="icon">📄</span>
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
            <select v-model="config.recipientId" class="form-select" @change="updateConfig">
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

const currentUserId = computed(() => authStore.user?.id)

const visibleOnlineUsers = computed(() => {
  return onlineUsersList.value.filter(user => {
    // Show AI bots only if invited
    if (user.id === -1 || user.id === -2) {
      // If chatting with a specific AI, show only that AI
      if (config.value.recipientId === -1 || config.value.recipientId === -2) {
        return user.id === config.value.recipientId
      }
      // Otherwise, show AI bots only if inviteAi is true
      return config.value.inviteAi
    }
    return true
  })
})

const visibleOnlineCount = computed(() => {
  return visibleOnlineUsers.value.length
})

const availableUsers = computed(() => {
  return visibleOnlineUsers.value
})

const chatTitle = computed(() => {
  if (config.value.recipientId) {
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
  // Custom icons for AI bots
  if (userId === -1) { // Llama
    return 'https://upload.wikimedia.org/wikipedia/commons/1/1b/Meta_Llama_logo.svg'
  }
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

const updateConfig = () => {
  // Check for changes in AI invitation status
  if (config.value.inviteAi !== props.initialConfig.inviteAi) {
    const action = config.value.inviteAi ? 'joined' : 'left'
    // We don't know exactly which AI it is until we send a message, 
    // but we can guess based on provider or just say "AI Agent"
    const provider = authStore.user?.ai_provider || 'gemini'
    const aiName = (provider === 'local' || provider === 'llama') ? 'Llama AI' : 'Gemini AI'
    
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
    const useLlama = config.value.inviteAi && (aiProvider === 'local' || aiProvider === 'llama')
    const useGemini = config.value.inviteAi && (aiProvider !== 'local' && aiProvider !== 'llama')

    const messageData = {
      message: newMessage.value || (selectedImage.value ? '📷 Image' : ''),
      type: selectedImage.value ? 'image' : 'text',
      image_data: selectedImage.value || null,
      recipient_id: config.value.recipientId,
      invite_llama: useLlama,
      invite_gemini: useGemini,
      is_search: isSearchMode.value
    }
    
    await api.sendChatMessage(messageData)
    
    newMessage.value = ''
    clearAttachments()
    if (isSearchMode.value) {
      isSearchMode.value = false // Reset search mode after sending
    }
    
    // Message will be added via WebSocket
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
  const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
  const wsUrl = `${WS_URL}/ws?token=${authStore.token}`
  
  ws.value = new WebSocket(wsUrl)
  
  ws.value.onopen = () => {
    console.log('Chat WebSocket connected')
  }
  
  ws.value.onmessage = (event) => {
    const message = JSON.parse(event.data)
    
    if (message.type === 'chat_message') {
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
.flex-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(30, 30, 30, 0.6);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.chat-header {
  padding: 16px 24px;
  background: rgba(45, 45, 45, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(5px);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.chat-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.chat-info {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.2);
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.settings-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  transition: transform 0.2s;
  padding: 4px;
  border-radius: 50%;
}

.settings-btn:hover {
  transform: rotate(45deg);
  background: rgba(255, 255, 255, 0.1);
}

.online-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #00e676;
  box-shadow: 0 0 8px #00e676;
}

.online-count {
  font-size: 13px;
  color: #e0e0e0;
  font-weight: 500;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  scroll-behavior: smooth;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888;
  gap: 16px;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.message {
  display: flex;
  gap: 16px;
  max-width: 75%;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.own-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
  font-weight: 700;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  overflow: hidden; /* Ensure image stays within rounded corners */
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message.own-message .message-avatar {
  background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
}

.message-content-wrapper {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding: 0 4px;
}

.message-username {
  font-size: 13px;
  font-weight: 600;
  color: #a0aec0;
}

.message.own-message .message-username {
  color: #e2e8f0;
}

.message-time {
  font-size: 11px;
  color: #718096;
}

.message-bubble {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 18px;
  border-top-left-radius: 4px;
  padding: 12px 18px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  transition: all 0.2s;
  position: relative;
}

.message:hover .message-bubble {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.08);
}

.message.own-message .message-bubble {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  border: none;
  border-radius: 18px;
  border-top-right-radius: 4px;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.message.own-message:hover .message-bubble {
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

.message-bubble p {
  margin: 0;
  color: #e2e8f0;
  font-size: 15px;
  line-height: 1.6;
  word-wrap: break-word;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.message-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s;
  display: block;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.message-image:hover {
  transform: scale(1.02);
}

.chat-input-container {
  padding: 20px;
  background: transparent;
  position: relative;
  z-index: 10;
}

.input-wrapper {
  display: flex;
  align-items: center;
  background: rgba(30, 30, 30, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 6px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.input-wrapper:focus-within {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
  background: rgba(40, 40, 40, 0.9);
}

.input-wrapper.search-mode {
  border-color: #4299e1;
  box-shadow: 0 0 15px rgba(66, 153, 225, 0.2);
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  padding: 10px 16px;
  font-size: 15px;
  outline: none;
}

.chat-input::placeholder {
  color: #718096;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #a0aec0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  margin-right: 4px;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  transform: scale(1.1);
}

.action-btn.active {
  color: #4299e1;
  background: rgba(66, 153, 225, 0.1);
}

.send-btn {
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 20px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
  filter: brightness(1.1);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.danger-zone {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.clear-history-btn {
  width: 100%;
  padding: 10px;
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid rgba(220, 38, 38, 0.3);
  color: #ef4444;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.clear-history-btn:hover {
  background: rgba(220, 38, 38, 0.2);
  border-color: #ef4444;
  transform: translateY(-1px);
}


.input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 4px;
  padding-left: 12px;
  transition: all 0.2s;
}

.input-wrapper:focus-within {
  border-color: #4299e1;
  background: rgba(0, 0, 0, 0.4);
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.input-wrapper.search-mode {
  border-color: #9f7aea;
  box-shadow: 0 0 0 1px rgba(159, 122, 234, 0.3);
}

.input-wrapper.search-mode:focus-within {
  box-shadow: 0 0 0 3px rgba(159, 122, 234, 0.2);
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #a0aec0;
  background: transparent;
  border: none;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  transform: scale(1.1);
}

.action-btn.active {
  color: #9f7aea;
  background: rgba(159, 122, 234, 0.1);
}

.action-btn .icon {
  font-size: 18px;
}

.chat-input {
  flex: 1;
  padding: 10px;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 15px;
}

.chat-input:focus {
  outline: none;
  box-shadow: none;
}

.send-btn {
  padding: 8px 20px;
  height: 36px;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: none;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 80px;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.send-btn.search-send-btn {
  background: linear-gradient(135deg, #9f7aea 0%, #805ad5 100%);
}


.preview-area {
  display: flex;
  gap: 10px;
  padding-left: 10px;
}

.preview-item {
  font-size: 12px;
  color: #a0aec0;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  padding: 4px 12px;
  border-radius: 12px;
}

.clear-btn {
  background: none;
  border: none;
  color: #fc8181;
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
  background-color: rgba(0, 0, 0, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  backdrop-filter: blur(5px);
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
  border-radius: 8px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.close-modal {
  position: absolute;
  top: -50px;
  right: -10px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 24px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-modal:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: rotate(90deg);
}

/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(3px);
}

.modal-content {
  background-color: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
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
  border-bottom: 1px solid #333;
}

.modal-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 20px;
}

.setting-group {
  margin-bottom: 20px;
}

.setting-group label {
  display: block;
  color: #ccc;
  margin-bottom: 8px;
  font-size: 14px;
}

.form-select {
  width: 100%;
  padding: 10px;
  background-color: #2d2d2d;
  border: 1px solid #444;
  border-radius: 4px;
  color: #fff;
  font-size: 14px;
}

.form-select:focus {
  outline: none;
  border-color: #4299e1;
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
  accent-color: #4299e1;
}

.setting-hint {
  margin: 4px 0 0 28px;
  font-size: 12px;
  color: #666;
}

/* Context Menu */
.context-menu {
  position: fixed;
  background: #2d2d2d;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 4px 0;
  min-width: 150px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 9999;
}

.context-menu-item {
  padding: 8px 16px;
  font-size: 14px;
  color: #e2e8f0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.context-menu-item:hover {
  background-color: #3a3a3a;
}

.context-menu-item.delete {
  color: #ef5350;
}

.context-menu-item.delete:hover {
  background-color: rgba(239, 83, 80, 0.1);
}
</style>
