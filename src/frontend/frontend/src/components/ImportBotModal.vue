<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-content">
      <div class="modal-header">
        <h2>Import Bot</h2>
        <button class="close-btn" @click="close">&times;</button>
      </div>
      
      <div class="modal-body">
        <div class="import-section">
          <p class="help-text">
            Select a bot configuration file (JSON) to import. 
            <span v-if="targetBot">
              This will overwrite the configuration for <strong>{{ targetBot.name }}</strong>.
            </span>
            <span v-else>
              The exported file includes all API credentials, so you can quickly import the complete bot configuration.
            </span>
          </p>
          
          <div class="file-input-wrapper">
            <input
              ref="fileInput"
              type="file"
              accept=".json,application/json"
              @change="handleFileSelect"
              class="file-input"
              id="bot-file-input"
            />
            <label for="bot-file-input" class="file-input-label">
              <span class="file-input-icon">📁</span>
              <span>{{ selectedFile ? selectedFile.name : 'Choose JSON file...' }}</span>
            </label>
          </div>
          
          <div v-if="previewData" class="preview-section">
            <h3>Bot Preview</h3>
            <div class="preview-info">
              <div class="preview-item">
                <span class="preview-label">Name:</span>
                <span class="preview-value">{{ previewData.name }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">Type:</span>
                <span class="preview-value">{{ previewData.bot_type }}</span>
              </div>
              <div v-if="previewData.description" class="preview-item">
                <span class="preview-label">Description:</span>
                <span class="preview-value">{{ previewData.description }}</span>
              </div>
            </div>
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
          @click="importBot" 
          :disabled="!previewData || importing"
        >
          {{ importing ? 'Importing...' : 'Import Bot' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  targetBot: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'imported'])

const fileInput = ref(null)
const selectedFile = ref(null)
const previewData = ref(null)
const importing = ref(false)
const error = ref(null)

watch(() => props.show, (newVal) => {
  if (newVal) {
    // Reset form when modal opens
    selectedFile.value = null
    previewData.value = null
    error.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  }
})

const close = () => {
  emit('close')
}

const handleFileSelect = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  selectedFile.value = file
  error.value = null
  previewData.value = null
  
  try {
    const text = await file.text()
    const data = JSON.parse(text)
    
    // Validate the structure
    if (!data.name || !data.bot_type) {
      throw new Error('Invalid bot file format. Missing required fields: name, bot_type')
    }
    
    previewData.value = {
      name: data.name,
      bot_type: data.bot_type,
      description: data.description || null,
      config: data.config || {}
    }
  } catch (err) {
    error.value = err.message || 'Failed to parse JSON file'
    selectedFile.value = null
    previewData.value = null
  }
}

const importBot = async () => {
  if (!previewData.value) return
  
  importing.value = true
  error.value = null
  
  try {
    if (props.targetBot) {
      await api.importBotConfig(props.targetBot.id, {
        name: previewData.value.name,
        bot_type: previewData.value.bot_type,
        description: previewData.value.description,
        config: previewData.value.config
      })
    } else {
      await api.importBot({
        name: previewData.value.name,
        bot_type: previewData.value.bot_type,
        description: previewData.value.description,
        config: previewData.value.config
      })
    }
    
    // Close modal first
    close()
    
    // Then emit the imported event
    setTimeout(() => {
      emit('imported')
    }, 100)
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to import bot'
  } finally {
    importing.value = false
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
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--glass-bg, rgba(30, 41, 59, 0.5));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-lg, 24px);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-glass, 0 25px 50px -12px rgba(0, 0, 0, 0.5));
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  background: transparent;
}

.modal-header h2 {
  margin: 0;
  color: #e2e8f0;
  font-size: 24px;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary, #94a3b8);
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
  color: var(--text-primary, #e2e8f0);
}

.modal-body {
  padding: 24px;
}

.import-section {
  margin-bottom: 24px;
}

.help-text {
  color: #a0aec0;
  font-size: 14px;
  margin-bottom: 20px;
  line-height: 1.5;
}

.file-input-wrapper {
  margin-bottom: 24px;
}

.file-input {
  display: none;
}

.file-input-label {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 2px dashed var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm, 12px);
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-primary, #e2e8f0);
  font-size: 14px;
}

.file-input-label:hover {
  border-color: var(--accent-primary, #3b82f6);
  background: var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
}

.file-input-icon {
  font-size: 24px;
}

.preview-section {
  margin-top: 24px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm, 12px);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
}

.preview-section h3 {
  margin: 0 0 16px 0;
  color: #e2e8f0;
  font-size: 18px;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-item {
  display: flex;
  gap: 12px;
}

.preview-label {
  color: #a0aec0;
  font-weight: 600;
  min-width: 100px;
}

.preview-value {
  color: #e2e8f0;
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
  border-top: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  background: transparent;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-sm, 12px);
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
  background: transparent;
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  color: var(--text-secondary, #94a3b8);
}

.btn-secondary:hover:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.2);
  color: var(--text-primary, #e2e8f0);
}

.btn-primary {
  background: var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}

.btn-primary:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.25);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.2);
  transform: translateY(-1px);
}
</style>


