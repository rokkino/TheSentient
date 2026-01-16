<template>
  <div class="strategy-builder">
    <div class="builder-split">
      <!-- Left Panel: Chat Interface -->
      <div class="chat-panel">
        <div class="panel-header">
          <h3>Strategy Assistant</h3>
          <p>Describe your strategy to generate rules</p>
        </div>
        <div class="chat-messages" ref="chatContainer">
          <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role">
            <div class="message-content">{{ msg.content }}</div>
          </div>
          <div v-if="isGenerating" class="message assistant">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
        <div class="chat-input">
          <textarea 
            v-model="prompt" 
            placeholder="e.g., Buy when RSI is below 30 and sell when RSI is above 70..."
            @keydown.enter.prevent="sendMessage"
          ></textarea>
          <button @click="sendMessage" :disabled="!prompt.trim() || isGenerating">
            <span v-if="!isGenerating">Generate</span>
            <span v-else>...</span>
          </button>
        </div>
      </div>

      <!-- Right Panel: Strategy Editor -->
      <div class="editor-panel">
        <div class="panel-header">
          <div class="header-left">
            <input v-model="strategy.name" class="strategy-name-input" placeholder="Strategy Name" />
          </div>
          <div class="header-actions">
            <button class="action-btn" @click="saveStrategy" :disabled="isSaving">
              {{ isSaving ? 'Saving...' : 'Save' }}
            </button>
            <button class="action-btn secondary" @click="simulateStrategy">
              Simulate
            </button>
          </div>
        </div>
        
        <div class="json-editor-container">
          <textarea 
            v-model="strategyJsonString" 
            class="json-editor" 
            spellcheck="false"
            @input="updateStrategyFromJson"
          ></textarea>
        </div>
        
        <div class="visual-preview">
          <h4>Rules Summary</h4>
          <div class="rules-list">
            <div class="rule-section">
              <h5>Entry Rules</h5>
              <div v-if="strategy.entry_rules?.length" class="rules-tags">
                <span v-for="(rule, i) in strategy.entry_rules" :key="i" class="rule-tag entry">
                  {{ rule.indicator }} {{ rule.condition }} {{ rule.value }}
                </span>
              </div>
              <div v-else class="empty-rules">No entry rules defined</div>
            </div>
            
            <div class="rule-section">
              <h5>Exit Rules</h5>
              <div v-if="strategy.exit_rules?.length" class="rules-tags">
                <span v-for="(rule, i) in strategy.exit_rules" :key="i" class="rule-tag exit">
                  {{ rule.indicator }} {{ rule.condition }} {{ rule.value }}
                </span>
              </div>
              <div v-else class="empty-rules">No exit rules defined</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, nextTick, onMounted } from 'vue'
import api from '../services/api'

const props = defineProps({
  initialStrategy: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['save'])

const prompt = ref('')
const isGenerating = ref(false)
const isSaving = ref(false)
const chatContainer = ref(null)

const messages = ref([
  { role: 'assistant', content: 'Hello! I can help you build a trading strategy. Just describe what you want, for example: "Buy when RSI < 30 and Price is above 200 SMA".' }
])

const strategy = reactive({
  name: 'New Strategy',
  description: '',
  entry_rules: [],
  exit_rules: [],
  risk_management: {
    stop_loss_pct: 2.0,
    take_profit_pct: 4.0
  }
})

const strategyJsonString = ref(JSON.stringify(strategy, null, 2))

onMounted(() => {
  if (props.initialStrategy) {
    Object.assign(strategy, props.initialStrategy)
    strategyJsonString.value = JSON.stringify(strategy, null, 2)
  }
})

const sendMessage = async () => {
  if (!prompt.value.trim() || isGenerating.value) return
  
  const userMsg = prompt.value
  messages.value.push({ role: 'user', content: userMsg })
  prompt.value = ''
  isGenerating.value = true
  scrollToBottom()

  try {
    const response = await api.generateStrategy(userMsg)
    const generatedStrategy = response.data.strategy
    
    // Merge generated strategy
    if (generatedStrategy) {
      if (generatedStrategy.name) strategy.name = generatedStrategy.name
      if (generatedStrategy.description) strategy.description = generatedStrategy.description
      if (generatedStrategy.entry_rules) strategy.entry_rules = generatedStrategy.entry_rules
      if (generatedStrategy.exit_rules) strategy.exit_rules = generatedStrategy.exit_rules
      if (generatedStrategy.risk_management) strategy.risk_management = generatedStrategy.risk_management
      
      // Update JSON view
      strategyJsonString.value = JSON.stringify(strategy, null, 2)
      
      messages.value.push({ 
        role: 'assistant', 
        content: `I've updated the strategy based on your request. You can see the new rules in the editor.` 
      })
    } else {
      messages.value.push({ role: 'assistant', content: "I couldn't generate a valid strategy from that description. Please try being more specific." })
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `Error: ${e.message || 'Failed to generate strategy'}` })
  } finally {
    isGenerating.value = false
    scrollToBottom()
  }
}

const updateStrategyFromJson = () => {
  try {
    const parsed = JSON.parse(strategyJsonString.value)
    Object.assign(strategy, parsed)
  } catch (e) {
    // Invalid JSON, ignore update
  }
}

const saveStrategy = async () => {
  isSaving.value = true
  try {
    const strategyData = {
      name: strategy.name,
      description: strategy.description,
      definition: strategy
    }
    
    await api.createStrategy(strategyData)
    emit('save', strategyData)
    alert('Strategy saved successfully!')
  } catch (e) {
    alert('Failed to save strategy: ' + e.message)
  } finally {
    isSaving.value = false
  }
}

const simulateStrategy = () => {
  alert('Simulation feature coming soon!')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.strategy-builder {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
  color: #e0e0e0;
}

.builder-split {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Chat Panel */
.chat-panel {
  width: 350px;
  border-right: 1px solid #333;
  display: flex;
  flex-direction: column;
  background: #111;
}

.panel-header {
  padding: 15px 20px;
  border-bottom: 1px solid #333;
  background: #161616;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #fff;
}

.panel-header p {
  margin: 5px 0 0;
  font-size: 12px;
  color: #888;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.message {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.4;
}

.message.user {
  align-self: flex-end;
  background: #2b6cb0;
  color: #fff;
  border-bottom-right-radius: 2px;
}

.message.assistant {
  align-self: flex-start;
  background: #2d3748;
  color: #e2e8f0;
  border-bottom-left-radius: 2px;
}

.chat-input {
  padding: 15px;
  border-top: 1px solid #333;
  display: flex;
  gap: 10px;
  background: #161616;
}

.chat-input textarea {
  flex: 1;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  padding: 10px;
  font-family: inherit;
  resize: none;
  height: 60px;
  font-size: 13px;
}

.chat-input textarea:focus {
  outline: none;
  border-color: #4299e1;
}

.chat-input button {
  background: #4299e1;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0 15px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}

.chat-input button:hover:not(:disabled) {
  background: #3182ce;
}

.chat-input button:disabled {
  background: #333;
  color: #666;
  cursor: not-allowed;
}

/* Editor Panel */
.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #0f0f0f;
}

.editor-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-name-input {
  background: transparent;
  border: none;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  width: 300px;
}

.strategy-name-input:focus {
  outline: none;
  border-bottom: 1px solid #4299e1;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  background: #28a745;
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.action-btn.secondary {
  background: #4a5568;
}

.action-btn:hover {
  opacity: 0.9;
}

.json-editor-container {
  flex: 2;
  border-bottom: 1px solid #333;
  position: relative;
}

.json-editor {
  width: 100%;
  height: 100%;
  background: #0a0a0a;
  border: none;
  color: #a0aec0;
  font-family: 'Roboto Mono', monospace;
  font-size: 13px;
  padding: 20px;
  resize: none;
  line-height: 1.5;
}

.json-editor:focus {
  outline: none;
}

.visual-preview {
  flex: 1;
  padding: 20px;
  background: #111;
  overflow-y: auto;
}

.visual-preview h4 {
  margin: 0 0 15px 0;
  color: #fff;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.rules-list {
  display: flex;
  gap: 30px;
}

.rule-section {
  flex: 1;
}

.rule-section h5 {
  margin: 0 0 10px 0;
  color: #888;
  font-size: 12px;
  text-transform: uppercase;
}

.rules-tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-tag {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Roboto Mono', monospace;
  background: #2d3748;
  border: 1px solid #4a5568;
}

.rule-tag.entry {
  border-left: 3px solid #48bb78;
}

.rule-tag.exit {
  border-left: 3px solid #f56565;
}

.empty-rules {
  color: #555;
  font-style: italic;
  font-size: 13px;
}

.typing-indicator span {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: #a0aec0;
  border-radius: 50%;
  margin: 0 2px;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
