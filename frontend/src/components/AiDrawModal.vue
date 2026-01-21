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
import { ref, defineEmits } from 'vue'
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
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal-content {
  background: #1e1e1e;
  padding: 20px;
  border-radius: 8px;
  width: 320px;
  color: #e0e0e0;
}
textarea {
  width: 100%;
  background: #2a2a2a;
  border: 1px solid #444;
  color: #e0e0e0;
  padding: 8px;
  margin-top: 8px;
  border-radius: 4px;
}
.actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
button.primary {
  background: #2196F3;
  color: #fff;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}
button.secondary {
  background: transparent;
  color: #aaa;
  border: 1px solid #555;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}
</style>
