<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Settings</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <div class="setting-item">
          <label>News Tickers (comma-separated):</label>
          <input v-model="newsTickers" type="text" placeholder="NVDA, GC=F, AAPL" />
        </div>
        <div class="setting-item">
          <label>News Sources (select websites to receive news from):</label>
          <div class="publishers-list">
            <div v-if="loadingPublishers" class="loading">Loading publishers...</div>
            <div v-else class="publisher-checkboxes">
              <label
                v-for="publisher in availablePublishers"
                :key="publisher"
                class="publisher-checkbox"
              >
                <input
                  type="checkbox"
                  :value="publisher"
                  v-model="selectedPublishers"
                />
                <span>{{ publisher || 'Unknown' }}</span>
              </label>
            </div>
            <div v-if="availablePublishers.length === 0 && !loadingPublishers" class="no-publishers">
              No publishers found. Load news first.
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')">Cancel</button>
        <button @click="save" class="save-btn">Save</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const emit = defineEmits(['close', 'save'])

const newsTickers = ref('')
const selectedPublishers = ref([])
const availablePublishers = ref([])
const loadingPublishers = ref(false)

const loadPublishers = async () => {
  loadingPublishers.value = true
  try {
    const response = await api.getNewsPublishers()
    if (response.data && response.data.publishers) {
      availablePublishers.value = response.data.publishers
      // Load saved publishers from localStorage
      const saved = localStorage.getItem('selectedPublishers')
      if (saved) {
        try {
          const savedPublishers = JSON.parse(saved)
          selectedPublishers.value = savedPublishers.filter(p => 
            availablePublishers.value.includes(p)
          )
        } catch (e) {
          console.error('Error loading saved publishers:', e)
        }
      }
    }
  } catch (error) {
    console.error('Error loading publishers:', error)
  } finally {
    loadingPublishers.value = false
  }
}

const save = () => {
  // Save publishers to localStorage
  localStorage.setItem('selectedPublishers', JSON.stringify(selectedPublishers.value))
  
  emit('save', {
    newsTickers: newsTickers.value.split(',').map(t => t.trim()).filter(t => t),
    selectedPublishers: selectedPublishers.value
  })
  emit('close')
}

onMounted(() => {
  // Load saved tickers
  const savedTickers = localStorage.getItem('newsTickers')
  if (savedTickers) {
    try {
      const tickers = JSON.parse(savedTickers)
      newsTickers.value = tickers.join(', ')
    } catch (e) {
      console.error('Error loading saved tickers:', e)
    }
  }
  
  loadPublishers()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-content {
  background-color: #2d2d2d;
  border-radius: 12px;
  width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #444;
}

.close-btn {
  background: none;
  border: none;
  color: #dcdcdc;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
}

.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.setting-item {
  margin-bottom: 20px;
}

.setting-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: bold;
}

.setting-item input {
  width: 100%;
  padding: 8px;
  background-color: #1e1e1e;
  border: 1px solid #444;
  border-radius: 8px;
  color: #dcdcdc;
}

.publishers-list {
  margin-top: 10px;
  max-height: 300px;
  overflow-y: auto;
  background-color: #1e1e1e;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 10px;
}

.publisher-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.publisher-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.publisher-checkbox:hover {
  background-color: #2a2a2a;
}

.publisher-checkbox input[type="checkbox"] {
  width: auto;
  cursor: pointer;
}

.publisher-checkbox span {
  color: #dcdcdc;
  font-size: 14px;
}

.loading, .no-publishers {
  text-align: center;
  padding: 20px;
  color: #888;
  font-size: 14px;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #444;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.modal-footer button {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid #555;
  background-color: #3c3c3c;
  color: #dcdcdc;
  cursor: pointer;
}

.save-btn {
  background-color: #007acc;
  color: #fff;
}
</style>

