<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Create New Bot</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>
      
      <div class="modal-body">
        <div class="bot-types">
          <h3>Select Bot Type</h3>
          <div class="bot-type-grid">
            <div 
              v-for="botType in botTypes" 
              :key="botType.id"
              :class="['bot-type-card', { selected: selectedBotType === botType.id }]"
              @click="selectedBotType = botType.id"
            >
              <div class="bot-type-icon">{{ botType.icon }}</div>
              <div class="bot-type-name">{{ botType.name }}</div>
              <div class="bot-type-description">{{ botType.description }}</div>
            </div>
          </div>
        </div>
        
        <div class="form-section">
          <div class="form-group">
            <label for="bot-name">Bot Name</label>
            <input
              id="bot-name"
              v-model="botName"
              type="text"
              placeholder="e.g., Earnings Report Genius"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="bot-description">Description (Optional)</label>
            <textarea
              id="bot-description"
              v-model="botDescription"
              placeholder="Describe your bot's strategy..."
              class="form-textarea"
              rows="3"
            ></textarea>
          </div>
        </div>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="close">Cancel</button>
        <button 
          class="btn btn-primary" 
          @click="createBot" 
          :disabled="!canCreate || creating"
        >
          {{ creating ? 'Creating...' : 'Create Bot' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'created'])

const botTypes = [
  {
    id: 'earnings_report_genius',
    name: 'Earnings Report Genius',
    icon: '💰',
    description: 'Monitors earnings reports daily and executes paper trades based on earnings data'
  }
  // Add more bot types here in the future
]

const selectedBotType = ref('earnings_report_genius')
const botName = ref('Earnings Report Genius')
const botDescription = ref('')
const creating = ref(false)
const error = ref(null)

const canCreate = computed(() => {
  return selectedBotType.value && botName.value.trim().length > 0
})

const close = () => {
  emit('close')
  // Reset form
  selectedBotType.value = 'earnings_report_genius'
  botName.value = 'Earnings Report Genius'
  botDescription.value = ''
  error.value = null
}

const createBot = async () => {
  if (!canCreate.value) return
  
  creating.value = true
  error.value = null
  
  try {
    const response = await api.createBot({
      name: botName.value.trim(),
      bot_type: selectedBotType.value,
      description: botDescription.value.trim() || null
    })
    
    console.log('Bot created successfully:', response.data)
    
    // Close modal first
    close()
    
    // Then emit the created event to trigger reload
    // Small delay to ensure modal is closed
    setTimeout(() => {
      emit('created')
    }, 100)
  } catch (err) {
    console.error('Error creating bot:', err)
    error.value = err.response?.data?.detail || err.message || 'Failed to create bot'
  } finally {
    creating.value = false
  }
}
</script>

<style scoped>
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
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #4a5568;
}

.modal-header h2 {
  margin: 0;
  color: #e2e8f0;
  font-size: 24px;
}

.close-btn {
  background: none;
  border: none;
  color: #a0aec0;
  font-size: 32px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #e2e8f0;
}

.modal-body {
  padding: 24px;
}

.bot-types {
  margin-bottom: 32px;
}

.bot-types h3 {
  color: #e2e8f0;
  margin: 0 0 16px 0;
  font-size: 18px;
}

.bot-type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.bot-type-card {
  background: #1a202c;
  border: 2px solid #4a5568;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.bot-type-card:hover {
  border-color: #718096;
  transform: translateY(-2px);
}

.bot-type-card.selected {
  border-color: #4299e1;
  background: #1e3a5f;
}

.bot-type-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.bot-type-name {
  color: #e2e8f0;
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 16px;
}

.bot-type-description {
  color: #a0aec0;
  font-size: 12px;
  line-height: 1.4;
}

.form-section {
  margin-top: 32px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  color: #cbd5e0;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px;
  background: #1a202c;
  border: 1px solid #4a5568;
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #4299e1;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.error-message {
  background: #4a2a2a;
  border: 1px solid #fc8181;
  color: #fc8181;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid #4a5568;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #4a5568;
  color: #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #718096;
}

.btn-primary {
  background: #4299e1;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #3182ce;
}
</style>

