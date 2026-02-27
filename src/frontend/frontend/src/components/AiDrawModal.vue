<template>
  <div class="ai-draw-modal overlay">
    <div class="modal-content">
      <h3>AI Draw</h3>
      <textarea v-model="prompt" placeholder="Describe what you want to draw..." rows="4"></textarea>
      <div class="actions">
        <button @click="submit" class="primary">Generate</button>
        <button @click="close" class="secondary">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../services/api'

const props = defineProps({
  chartData: {
    type: Array,
    default: () => []
  },
  selectedColor: {
    type: String,
    default: '#2196F3'
  }
})

const emit = defineEmits(['close', 'drawing-added'])
const prompt = ref('')
const loading = ref(false)

const close = () => {
  emit('close')
}

const submit = async () => {
  if (!prompt.value.trim()) return
  loading.value = true
  try {
    const response = await api.post('/api/ai/draw', {
      prompt: prompt.value,
      color: props.selectedColor,
      chartData: props.chartData
    })
    // Expect response to contain a drawing object compatible with our drawing format
    if (response.data && response.data.drawing) {
      emit('drawing-added', response.data.drawing)
    }
  } catch (e) {
    console.error('AI draw error:', e)
  } finally {
    loading.value = false
    close()
  }
}
</script>

<style scoped>
.ai-draw-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal-content {
  background: var(--glass-bg, rgba(30, 41, 59, 0.5));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-lg, 24px);
  padding: 24px;
  width: 360px;
  color: var(--text-primary, #e2e8f0);
  box-shadow: var(--shadow-glass, 0 25px 50px -12px rgba(0, 0, 0, 0.5));
}
textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm, 12px);
  color: var(--text-primary, #e2e8f0);
  padding: 12px;
  margin-top: 12px;
  font-family: inherit;
  transition: all 0.2s;
  resize: vertical;
}

textarea:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--accent-primary, #3b82f6);
  box-shadow: 0 0 0 3px var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
}
.actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
button.primary {
  background: var(--accent-primary-bg, rgba(59, 130, 246, 0.15));
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
  padding: 8px 16px;
  border-radius: var(--radius-sm, 12px);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

button.primary:hover {
  background: rgba(59, 130, 246, 0.25);
  transform: translateY(-1px);
}

button.secondary {
  background: transparent;
  color: var(--text-secondary, #94a3b8);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  padding: 8px 16px;
  border-radius: var(--radius-sm, 12px);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

button.secondary:hover {
  border-color: rgba(255, 255, 255, 0.2);
  color: var(--text-primary, #e2e8f0);
}
</style>
