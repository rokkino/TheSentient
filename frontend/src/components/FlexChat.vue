<template>
  <div class="flex-chat">
    <div class="chat-header">
      <h2>Flex Chat</h2>
      <div class="chat-info">
        <span class="online-count">{{ onlineUsers }} online</span>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div
        v-for="message in messages"
        :key="message.id"
        :class="['message', { 'own-message': message.user_id === currentUserId }]"
      >
        <div class="message-avatar">
          <span>{{ getInitials(message.username) }}</span>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-username">{{ message.username }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-body">
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
      <div class="input-actions">
        <label class="image-upload-btn">
          <input
            type="file"
            accept="image/*"
            @change="handleImageSelect"
            style="display: none"
          />
          📷
        </label>
        <span v-if="selectedImage" class="image-preview-info">
          Image selected
          <button @click="clearImage" class="clear-image-btn">×</button>
        </span>
      </div>
      <div class="input-wrapper">
        <input
          v-model="newMessage"
          @keypress.enter="sendMessage"
          placeholder="Type a message..."
          class="chat-input"
          :disabled="sending"
        />
        <button
          @click="sendMessage"
          :disabled="!canSend || sending"
          class="send-btn"
        >
          {{ sending ? 'Sending...' : 'Send' }}
        </button>
      </div>
    </div>

    <!-- Image Preview Modal -->
    <div v-if="imageModalOpen" class="image-modal" @click="imageModalOpen = false">
      <div class="image-modal-content" @click.stop>
        <button class="close-modal" @click="imageModalOpen = false">×</button>
        <img :src="`data:image/jpeg;base64,${modalImageData}`" alt="Full size image" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import api from '../services/api'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const messages = ref([])
const newMessage = ref('')
const selectedImage = ref(null)
const sending = ref(false)
const messagesContainer = ref(null)
const imageModalOpen = ref(false)
const modalImageData = ref(null)
const onlineUsers = ref(0)
const ws = ref(null)

const currentUserId = computed(() => authStore.user?.id)

const canSend = computed(() => {
  return (newMessage.value.trim().length > 0 || selectedImage.value) && !sending.value
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

const clearImage = () => {
  selectedImage.value = null
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
      image_data: selectedImage.value || null
    }
    
    await api.sendChatMessage(messageData)
    
    newMessage.value = ''
    selectedImage.value = null
    
    // Message will be added via WebSocket
  } catch (error) {
    console.error('Error sending message:', error)
    alert('Failed to send message: ' + (error.response?.data?.detail || error.message))
  } finally {
    sending.value = false
  }
}

const loadMessages = async () => {
  try {
    const response = await api.getChatMessages(100)
    messages.value = response.data.messages || []
    scrollToBottom()
  } catch (error) {
    console.error('Error loading messages:', error)
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
  const wsUrl = `${WS_URL}/ws`
  
  ws.value = new WebSocket(wsUrl)
  
  ws.value.onopen = () => {
    console.log('Chat WebSocket connected')
  }
  
  ws.value.onmessage = (event) => {
    const message = JSON.parse(event.data)
    
    if (message.type === 'chat_message') {
      messages.value.push(message.data)
      scrollToBottom()
    } else if (message.type === 'online_users') {
      onlineUsers.value = message.count || 0
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

watch(messages, () => {
  scrollToBottom()
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
  background-color: #1e1e1e;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: #2d2d2d;
  border-bottom: 1px solid #444;
}

.chat-header h2 {
  font-size: 20px;
  color: #e2e8f0;
  margin: 0;
}

.chat-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.online-count {
  font-size: 14px;
  color: #26a69a;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 70%;
}

.message.own-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.message-content {
  flex: 1;
  background-color: #2d2d2d;
  border: 1px solid #444;
  border-radius: 12px;
  padding: 12px;
}

.message.own-message .message-content {
  background-color: #4299e1;
  border-color: #3182ce;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.message-username {
  font-size: 14px;
  font-weight: 600;
  color: #4299e1;
}

.message.own-message .message-username {
  color: white;
}

.message-time {
  font-size: 11px;
  color: #888;
}

.message.own-message .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.message-body {
  color: #dcdcdc;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message.own-message .message-body {
  color: white;
}

.message-image {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.message-image:hover {
  transform: scale(1.02);
}

.chat-input-container {
  padding: 16px 20px;
  background-color: #2d2d2d;
  border-top: 1px solid #444;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.image-upload-btn {
  cursor: pointer;
  font-size: 20px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.image-upload-btn:hover {
  background-color: #3a3a3a;
}

.image-preview-info {
  font-size: 12px;
  color: #888;
  display: flex;
  align-items: center;
  gap: 8px;
}

.clear-image-btn {
  background: none;
  border: none;
  color: #ef5350;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-wrapper {
  display: flex;
  gap: 8px;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  background-color: #1e1e1e;
  border: 1px solid #444;
  border-radius: 8px;
  color: #dcdcdc;
  font-size: 14px;
}

.chat-input:focus {
  outline: none;
  border-color: #4299e1;
}

.chat-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.image-modal-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
}

.image-modal-content img {
  max-width: 100%;
  max-height: 90vh;
  border-radius: 8px;
}

.close-modal {
  position: absolute;
  top: -40px;
  right: 0;
  background: none;
  border: none;
  color: white;
  font-size: 32px;
  cursor: pointer;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-modal:hover {
  color: #ef5350;
}
</style>

