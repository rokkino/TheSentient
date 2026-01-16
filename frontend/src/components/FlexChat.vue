<template>
  <div class="flex-chat">
    <div class="chat-header">
      <div class="header-content">
        <div class="header-left">
          <h2>{{ chatTitle }}</h2>
          <div class="chat-info">
            <span class="online-indicator"></span>
            <span class="online-count">{{ onlineUsersCount }} online</span>
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
          <span>{{ getInitials(message.username) }}</span>
        </div>
        <div class="message-content-wrapper">
          <div class="message-header">
            <span class="message-username">{{ message.username }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-bubble">
            <p v-if="message.type === 'text'">{{ message.message }}</p>
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
      <div class="input-wrapper">
        <div class="input-actions">
          <label class="action-btn upload-btn" title="Upload Image">
            <input
              type="file"
              accept="image/*"
              @change="handleImageSelect"
              style="display: none"
            />
            <span class="icon">📷</span>
          </label>
          <label class="action-btn upload-btn" title="Upload Document">
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
          placeholder="Type a message..."
          class="chat-input"
          :disabled="sending"
        />
        
        <button
          @click="sendMessage"
          :disabled="!canSend || sending"
          class="send-btn"
        >
          {{ sending ? '...' : 'Send' }}
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
                v-for="user in availableUsers" 
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
              <input type="checkbox" v-model="config.inviteLlama" @change="updateConfig">
              Invite Llama AI
            </label>
            <p class="setting-hint">If enabled, Llama will read messages and respond when relevant.</p>
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

const props = defineProps({
  tabId: {
    type: Number,
    default: null
  },
  initialConfig: {
    type: Object,
    default: () => ({
      recipientId: null,
      inviteLlama: false
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
const onlineUsersCount = ref(0)
const onlineUsersList = ref([])
const ws = ref(null)
const showSettings = ref(false)

const config = ref({
  recipientId: props.initialConfig?.recipientId || null,
  inviteLlama: props.initialConfig?.inviteLlama || false
})

const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  messageId: null
})

const currentUserId = computed(() => authStore.user?.id)

const availableUsers = computed(() => {
  return onlineUsersList.value
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
  emit('update-config', config.value)
  loadMessages() // Reload messages when switching chat context
}

const sendMessage = async () => {
  if (!canSend.value) return
  
  if (!authStore.isAuthenticated) {
    alert('Please login to send messages')
    return
  }
  
  sending.value = true
  
  try {
    const messageData = {
      message: newMessage.value || (selectedImage.value ? '📷 Image' : ''),
      type: selectedImage.value ? 'image' : 'text',
      image_data: selectedImage.value || null,
      recipient_id: config.value.recipientId,
      invite_llama: config.value.inviteLlama
    }
    
    await api.sendChatMessage(messageData)
    
    newMessage.value = ''
    clearAttachments()
    
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

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// Watch for config changes from parent (if any)
watch(() => props.initialConfig, (newConfig) => {
  if (newConfig) {
    config.value = { ...newConfig }
    loadMessages()
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
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
  font-weight: 700;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
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
  background: rgba(45, 45, 45, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  border-top-left-radius: 4px;
  padding: 12px 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(5px);
  transition: transform 0.2s;
}

.message:hover .message-bubble {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.message.own-message .message-bubble {
  background: linear-gradient(135deg, rgba(66, 153, 225, 0.2) 0%, rgba(49, 130, 206, 0.2) 100%);
  border-color: rgba(66, 153, 225, 0.3);
  border-radius: 16px;
  border-top-right-radius: 4px;
}

.message-bubble p {
  margin: 0;
  color: #e2e8f0;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
  display: block;
}

.message-image:hover {
  transform: scale(1.02);
}

.chat-input-container {
  padding: 20px;
  background: rgba(30, 30, 30, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  gap: 10px;
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
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  transform: scale(1.1);
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
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-right: 4px;
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
