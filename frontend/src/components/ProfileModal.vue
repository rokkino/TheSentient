<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Edit Profile</h2>
        <button class="close-btn" @click="close">×</button>
      </div>
      
      <div class="modal-body">
        <!-- Menu Navigation -->
        <div class="settings-menu">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="['menu-item', { active: activeTab === tab.id }]"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Profile Tab -->
        <div v-if="activeTab === 'profile'" class="tab-content">
          <div class="form-group">
            <label>Profile Picture</label>
            <div class="profile-picture-section">
              <div class="profile-picture-preview">
                <img 
                  v-if="displayPictureUrl" 
                  :src="displayPictureUrl" 
                  alt="Profile"
                  class="profile-picture-img"
                />
                <div v-else class="profile-picture-placeholder">
                  <span>{{ userInitials }}</span>
                </div>
              </div>
              <div class="profile-picture-actions">
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/*"
                  @change="handleFileSelect"
                  style="display: none"
                />
                <button @click="triggerFileInput" class="btn-upload">Choose Image</button>
                <button 
                  v-if="displayPictureUrl" 
                  @click="removeProfilePicture" 
                  class="btn-remove"
                >
                  Remove
                </button>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label>Motto / Bio</label>
            <textarea
              v-model="profileData.bio"
              class="form-textarea"
              rows="3"
              placeholder="Your motto or bio..."
              maxlength="200"
            ></textarea>
            <div class="char-count">{{ profileData.bio?.length || 0 }}/200</div>
          </div>
          
          <div class="form-group">
            <label>Location</label>
            <input v-model="profileData.location" type="text" class="form-input" />
          </div>
          
          <div class="form-group">
            <label>Website</label>
            <input v-model="profileData.website" type="url" class="form-input" placeholder="https://..." />
          </div>
        </div>

        <!-- Accounts Tab -->
        <div v-if="activeTab === 'accounts'" class="tab-content">
          <div class="accounts-header">
            <h3>Connected Accounts</h3>
            <button @click="openAddAccountForm" class="btn-primary btn-sm">Add Account</button>
          </div>

          <!-- Account List -->
          <div v-if="!showAccountForm" class="account-list">
            <div v-if="loadingAccounts" class="loading-state">Loading accounts...</div>
            <div v-else-if="accounts.length === 0" class="empty-state">
              No accounts connected. Add an account to start trading.
            </div>
            <div v-else v-for="account in accounts" :key="account.id" class="account-item">
              <div class="account-info">
                <div class="account-platform-badge">{{ account.platform }}</div>
                <div class="account-details">
                  <span class="account-name">{{ account.name }}</span>
                  <span class="account-status" :class="{ active: account.is_active }">
                    {{ account.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
              </div>
              <div class="account-actions">
                <button @click="editAccount(account)" class="btn-icon" title="Edit">✏️</button>
                <button @click="deleteAccount(account.id)" class="btn-icon text-danger" title="Delete">🗑️</button>
              </div>
            </div>
          </div>

          <!-- Add/Edit Account Form -->
          <div v-else class="account-form">
             <div class="form-header">
               <h4>{{ editingAccount ? 'Edit Account' : 'Add New Account' }}</h4>
               <button @click="cancelAccountEdit" class="close-sub-form">×</button>
             </div>
             
             <div class="form-group">
               <label>Platform</label>
               <select v-model="accountForm.platform" class="form-input form-select" :disabled="editingAccount">
                 <option value="Alpaca">Alpaca</option>
             </select>
             </div>

             <div class="form-group">
               <label>Account Name</label>
               <input v-model="accountForm.name" type="text" class="form-input" placeholder="e.g. My Live Account" />
             </div>

             <!-- Alpaca Specific Fields -->
             <div v-if="accountForm.platform === 'Alpaca'">
               <p class="form-hint">Su Alpaca trovi due valori: <strong>Key</strong> (API Key ID, es. PK...) e <strong>Secret</strong> (mostrata una sola volta alla creazione). Inserisci entrambi. L’Endpoint non serve qui.</p>
               <div class="form-group">
                 <label>API Key ID (su Alpaca: "Key")</label>
                 <input v-model="accountForm.credentials.api_key" type="text" class="form-input" placeholder="es. PK..." />
               </div>
               <div class="form-group">
                 <label>Secret Key (su Alpaca: "Secret", visibile solo alla creazione)</label>
                 <input v-model="accountForm.credentials.secret_key" type="password" class="form-input" placeholder="Inserisci la Secret Key da Alpaca" />
               </div>
               <div class="form-group">
                 <label>Trading Mode</label>
                 <div class="checkbox-group">
                   <input type="checkbox" id="paper-trading" v-model="accountForm.credentials.paper_trading" />
                   <label for="paper-trading">Paper Trading</label>
                 </div>
               </div>
             </div>

             <div class="form-actions">
               <button @click="testNewAccountConnection" class="btn-secondary" :disabled="testingAccount">
                 {{ testingAccount ? 'Testing...' : 'Test Connection' }}
               </button>
               <button @click="saveAccount" class="btn-primary" :disabled="savingAccount">
                 {{ savingAccount ? 'Saving...' : 'Save Account' }}
               </button>
             </div>
             
             <div v-if="accountTestResult" :class="['connection-status', accountTestResult.success ? 'success' : 'error']">
               {{ accountTestResult.message }}
             </div>
          </div>
        </div>

        <!-- AI Settings Tab -->
        <div v-if="activeTab === 'ai'" class="tab-content">
          <div class="form-group">
            <label>Google Gemini API Key</label>
            <div class="api-key-input-group">
              <input 
                v-model="profileData.gemini_api_key" 
                type="password" 
                class="form-input" 
                placeholder="AIza..." 
              />
              <button 
                @click="testConnection('gemini', profileData.gemini_api_key)"
                :disabled="!profileData.gemini_api_key || testingConnections.gemini"
                class="btn-test"
              >
                {{ testingConnections.gemini ? 'Testing...' : 'Test' }}
              </button>
            </div>
            <div class="model-version-row">
              <label class="version-label">Model version</label>
              <select v-model="profileData.gemini_model" class="form-input form-select">
                <option v-for="opt in GEMINI_MODELS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div v-if="connectionStatus.gemini" :class="['connection-status', connectionStatus.gemini.success ? 'success' : 'error']">
              {{ connectionStatus.gemini.message }}
            </div>
            <div class="help-text">
              Required for calling Gemini from chat. Choose which model version to use.
            </div>
          </div>

          <div class="form-group">
            <label>OpenAI API Key</label>
            <div class="api-key-input-group">
              <input 
                v-model="profileData.openai_api_key" 
                type="password" 
                class="form-input" 
                placeholder="sk-..." 
              />
              <button 
                @click="testConnection('openai', profileData.openai_api_key)"
                :disabled="!profileData.openai_api_key || testingConnections.openai"
                class="btn-test"
              >
                {{ testingConnections.openai ? 'Testing...' : 'Test' }}
              </button>
            </div>
            <div class="model-version-row">
              <label class="version-label">Model version</label>
              <select v-model="profileData.openai_model" class="form-input form-select">
                <option v-for="opt in OPENAI_MODELS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div v-if="connectionStatus.openai" :class="['connection-status', connectionStatus.openai.success ? 'success' : 'error']">
              {{ connectionStatus.openai.message }}
            </div>
          </div>

          <div class="form-group">
            <label>Claude API Key (Anthropic)</label>
            <div class="api-key-input-group">
              <input 
                v-model="profileData.anthropic_api_key" 
                type="password" 
                class="form-input" 
                placeholder="sk-ant-..." 
              />
              <button 
                @click="testConnection('anthropic', profileData.anthropic_api_key)"
                :disabled="!profileData.anthropic_api_key || testingConnections.anthropic"
                class="btn-test"
              >
                {{ testingConnections.anthropic ? 'Testing...' : 'Test' }}
              </button>
            </div>
            <div class="model-version-row">
              <label class="version-label">Model version</label>
              <select v-model="profileData.anthropic_model" class="form-input form-select">
                <option v-for="opt in ANTHROPIC_MODELS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div v-if="connectionStatus.anthropic" :class="['connection-status', connectionStatus.anthropic.success ? 'success' : 'error']">
              {{ connectionStatus.anthropic.message }}
            </div>
          </div>

          <div class="form-group">
            <label>DeepSeek API Key</label>
            <div class="api-key-input-group">
              <input 
                v-model="profileData.deepseek_api_key" 
                type="password" 
                class="form-input" 
                placeholder="sk-..." 
              />
              <button 
                @click="testConnection('deepseek', profileData.deepseek_api_key)"
                :disabled="!profileData.deepseek_api_key || testingConnections.deepseek"
                class="btn-test"
              >
                {{ testingConnections.deepseek ? 'Testing...' : 'Test' }}
              </button>
            </div>
            <div class="model-version-row">
              <label class="version-label">Model version</label>
              <select v-model="profileData.deepseek_model" class="form-input form-select">
                <option v-for="opt in DEEPSEEK_MODELS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div v-if="connectionStatus.deepseek" :class="['connection-status', connectionStatus.deepseek.success ? 'success' : 'error']">
              {{ connectionStatus.deepseek.message }}
            </div>
          </div>

          <div class="form-group">
            <label>Llama API Key</label>
            <div class="api-key-input-group">
              <input 
                v-model="profileData.llama_api_key" 
                type="password" 
                class="form-input" 
                placeholder="LA-..." 
              />
              <button 
                @click="testConnection('llama', profileData.llama_api_key)"
                :disabled="!profileData.llama_api_key || testingConnections.llama"
                class="btn-test"
              >
                {{ testingConnections.llama ? 'Testing...' : 'Test' }}
              </button>
            </div>
            <div class="model-version-row">
              <label class="version-label">Model version</label>
              <select v-model="profileData.llama_model" class="form-input form-select">
                <option v-for="opt in LLAMA_MODELS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </div>
            <div v-if="connectionStatus.llama" :class="['connection-status', connectionStatus.llama.success ? 'success' : 'error']">
              {{ connectionStatus.llama.message }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <button @click="close" class="btn-secondary">Cancel</button>
        <button @click="save" class="btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// AI model version options per provider
const GEMINI_MODELS = [
  { value: '', label: 'Default (2.5 Pro → Flash → Lite fallback)' },
  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro (100 RPD free)' },
  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (250 RPD free)' },
  { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite (1000 RPD free)' },
  { value: 'gemini-3-flash-preview', label: 'Gemini 3 Flash Preview (20 RPD free)' },
  { value: 'gemini-3-pro-preview', label: 'Gemini 3 Pro Preview' },
  { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
  { value: 'gemini-2.0-flash-lite', label: 'Gemini 2.0 Flash Lite' },
  { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' }
]
const OPENAI_MODELS = [
  { value: '', label: 'Default (gpt-4o)' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
]
const ANTHROPIC_MODELS = [
  { value: '', label: 'Default (claude-3-5-sonnet)' },
  { value: 'claude-3-5-sonnet-20240620', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-sonnet-4-5', label: 'Claude Sonnet 4.5' },
  { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' }
]
const DEEPSEEK_MODELS = [
  { value: '', label: 'Default (deepseek-chat)' },
  { value: 'deepseek-chat', label: 'DeepSeek Chat' },
  { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner' },
  { value: 'deepseek-coder', label: 'DeepSeek Coder' }
]
const LLAMA_MODELS = [
  { value: '', label: 'Default (llama-3.3-70b-instruct)' },
  { value: 'llama-3.3-70b-instruct', label: 'Llama 3.3 70B Instruct' },
  { value: 'llama-3.1-70b-instruct', label: 'Llama 3.1 70B Instruct' },
  { value: 'llama-3.1-8b-instruct', label: 'Llama 3.1 8B Instruct' },
  { value: 'llama-3.2-3b-instruct', label: 'Llama 3.2 3B Instruct' }
]

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  user: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'saved'])

const authStore = useAuthStore()
const saving = ref(false)
const fileInput = ref(null)
const profilePicturePreview = ref(null)
const selectedFile = ref(null)
const activeTab = ref('profile')

// Account Management Logic
const accounts = ref([])
const loadingAccounts = ref(false)
const showAccountForm = ref(false)
const editingAccount = ref(null)
const savingAccount = ref(false)
const testingAccount = ref(false)
const accountTestResult = ref(null)

const accountForm = ref({
  platform: 'Alpaca',
  name: '',
  credentials: {
    username: '',
    password: '',
    api_key: '',
    secret_key: '',
    account_type: 'DEMO',
    paper_trading: true,
    login_method: 'STANDARD'
  },
  is_active: true
})

const loadAccounts = async () => {
  loadingAccounts.value = true
  try {
    const res = await api.getAccounts()
    accounts.value = res.data.accounts
  } catch (err) {
    console.error("Failed to load accounts", err)
  } finally {
    loadingAccounts.value = false
  }
}

// Watch active tab to load accounts
watch(activeTab, (newTab) => {
  if (newTab === 'accounts') {
    loadAccounts()
  }
})

const openAddAccountForm = () => {
  editingAccount.value = null
  accountForm.value = {
    platform: 'Alpaca',
    name: '',
    credentials: {
      username: '',
      password: '',
      api_key: '',
      secret_key: '',
      account_type: 'DEMO',
      paper_trading: true,
      login_method: 'STANDARD'
    },
    is_active: true
  }
  showAccountForm.value = true
  accountTestResult.value = null
}

const editAccount = (account) => {
  editingAccount.value = account
  // Clone data to form (note: credentials might be empty if not returned by API for security, 
  // currently the API doesn't return them by default in list, but we might need them or just leave blank for update)
  accountForm.value = {
    platform: account.platform,
    name: account.name,
    credentials: { ...accountForm.value.credentials }, // Keep defaults or empty
    is_active: account.is_active
  }
  showAccountForm.value = true
  accountTestResult.value = null
}

const cancelAccountEdit = () => {
  showAccountForm.value = false
  editingAccount.value = null
  accountTestResult.value = null
}

const saveAccount = async () => {
  if (!accountForm.value.name) {
    alert("Please enter an account name")
    return
  }
  
  savingAccount.value = true
  try {
    const data = {
      platform: accountForm.value.platform,
      name: accountForm.value.name,
      credentials: accountForm.value.credentials,
      is_active: accountForm.value.is_active
    }
    
    if (editingAccount.value) {
      await api.updateAccount(editingAccount.value.id, data)
    } else {
      await api.createAccount(data)
    }
    
    await loadAccounts()
    showAccountForm.value = false
  } catch (err) {
    alert("Failed to save account: " + (err.response?.data?.detail || err.message))
  } finally {
    savingAccount.value = false
  }
}

const deleteAccount = async (id) => {
  if (!confirm("Are you sure you want to delete this account? associated bots may stop working.")) return
  try {
    await api.deleteAccount(id)
    await loadAccounts()
  } catch (err) {
    alert("Failed to delete account")
  }
}

const testNewAccountConnection = async () => {
  testingAccount.value = true
  accountTestResult.value = null
  try {
     // For testing a NEW account or updated creds, we might need a specific endpoint that accepts creds payload
     // But `testAccountConnection` in API uses stored ID. 
     // So we'll simulate a test or save-and-test if needed. 
     // Alternatively, the backend could have a /test-creds endpoint. 
     // For now, let's rely on saving first or adding a specific verify endpoint later.
     // EDIT: Actually, for now let's just create a temporary/mock test or implement a proper ad-hoc test endpoint.
     // Given the constraints and the `test_connection` logic in `bot_service`, 
     // I'll assume we verify by saving first or I should add a `testConnection` that takes raw creds. 
     // Let's defer to "Save first then Test" behavior for simplicity unless I add a new endpoint.
     // Wait, I can implement a check here:
     
     // Check validity of current form data
     // Construct a temporary config object
     const config = {} // construct based on platform
     if (accountForm.value.platform === 'IG') {
        config.ig_username = accountForm.value.credentials.username
        config.ig_password = accountForm.value.credentials.password
        config.ig_api_key = accountForm.value.credentials.api_key
        config.ig_acc_type = accountForm.value.credentials.account_type
     } else if (accountForm.value.platform === 'Alpaca') {
        config.alpaca_api_key = accountForm.value.credentials.api_key
        config.alpaca_api_secret = accountForm.value.credentials.secret_key
        config.alpaca_paper = accountForm.value.credentials.paper_trading
     }
     
     const res = await api.testBotConnection({
         broker: accountForm.value.platform,
         config: config
     })
     
     accountTestResult.value = {
         success: res.data.success,
         message: res.data.message
     }
     
  } catch (err) {
    accountTestResult.value = {
        success: false,
        message: err.message || "Test failed"
    }
  } finally {
    testingAccount.value = false
  }
}

const tabs = [
  { id: 'profile', label: 'Profile' },
  { id: 'accounts', label: 'Accounts' },
  { id: 'ai', label: 'AI Settings' }
]

const testingConnections = ref({
  gemini: false,
  openai: false,
  anthropic: false,
  deepseek: false,
  llama: false
})

const connectionStatus = ref({
  gemini: null,
  openai: null,
  anthropic: null,
  deepseek: null,
  llama: null
})

const profileData = ref({
  bio: '',
  location: '',
  website: '',
  profile_picture_url: '',
  gemini_api_key: '',
  openai_api_key: '',
  anthropic_api_key: '',
  deepseek_api_key: '',
  llama_api_key: '',
  gemini_model: '',
  openai_model: '',
  anthropic_model: '',
  deepseek_model: '',
  llama_model: ''
})

const userInitials = computed(() => {
  if (props.user && props.user.username) {
    return props.user.username.substring(0, 2).toUpperCase()
  }
  return 'U'
})

const getFullImageUrl = (url) => {
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

const displayPictureUrl = computed(() => {
  return profilePicturePreview.value || getFullImageUrl(profileData.value.profile_picture_url)
})

watch(() => props.user, (newUser) => {
  if (newUser) {
    profileData.value = {
      bio: newUser.bio || '',
      location: newUser.location || '',
      website: newUser.website || '',
      profile_picture_url: newUser.profile_picture_url || '',
      gemini_api_key: newUser.gemini_api_key || '',
      openai_api_key: newUser.openai_api_key || '',
      anthropic_api_key: newUser.anthropic_api_key || '',
      deepseek_api_key: newUser.deepseek_api_key || '',
      llama_api_key: newUser.llama_api_key || '',
      gemini_model: newUser.gemini_model ?? '',
      openai_model: newUser.openai_model ?? '',
      anthropic_model: newUser.anthropic_model ?? '',
      deepseek_model: newUser.deepseek_model ?? '',
      llama_model: newUser.llama_model ?? ''
    }
    profilePicturePreview.value = null
    selectedFile.value = null
    // Reset connection status when user changes
    connectionStatus.value = {
      gemini: null,
      openai: null,
      anthropic: null,
      deepseek: null,
      llama: null
    }
  }
}, { immediate: true })

const close = () => {
  emit('close')
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('Image size must be less than 5MB')
      return
    }
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }
    selectedFile.value = file
    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      profilePicturePreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const removeProfilePicture = () => {
  selectedFile.value = null
  profilePicturePreview.value = null
  profileData.value.profile_picture_url = ''
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const testConnection = async (provider, apiKey) => {
  if (!apiKey || !apiKey.trim()) {
    return
  }

  testingConnections.value[provider] = true
  connectionStatus.value[provider] = null

  try {
    const response = await api.testAIConnection(provider, apiKey.trim())
    connectionStatus.value[provider] = {
      success: response.data.success,
      message: response.data.message
    }
  } catch (error) {
    connectionStatus.value[provider] = {
      success: false,
      message: error.response?.data?.message || error.message || 'Connection test failed'
    }
  } finally {
    testingConnections.value[provider] = false
  }
}

const save = async () => {
  saving.value = true
  try {
    // Upload image first if selected
    if (selectedFile.value) {
      const formData = new FormData()
      formData.append('file', selectedFile.value)
      const uploadResponse = await api.uploadProfilePicture(formData)
      if (uploadResponse.data?.url) {
        profileData.value.profile_picture_url = uploadResponse.data.url
      }
    }
    
    // Update profile
    const result = await authStore.updateProfile(profileData.value)
    if (result.success) {
      emit('saved')
      close()
    } else {
      alert(result.error || 'Failed to update profile')
    }
  } catch (error) {
    alert('Error updating profile: ' + (error.message || 'Unknown error'))
  } finally {
    saving.value = false
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
  backdrop-filter: blur(2px);
}

.google-login-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  gap: 10px;
}

.btn-google {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: white;
  color: #757575;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px 16px;
  font-family: 'Roboto', sans-serif;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s, box-shadow 0.2s;
  width: 100%;
  max-width: 240px;
}

.btn-google:hover {
  background-color: #f8f9fa;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12);
}

.btn-google .google-icon {
  width: 18px;
  height: 18px;
  margin-right: 12px;
}



.modal-content {
  background-color: #0a0a0a;
  border: 1px solid #222;
  border-radius: 2px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0,0,0,0.8);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 25px;
  border-bottom: 1px solid #222;
  background-color: #0f0f0f;
}

.modal-header h2 {
  margin: 0;
  color: #fff;
  font-size: 18px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 300;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 28px;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 30px;
  flex: 1;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  margin-bottom: 10px;
  color: #666;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.form-hint {
  margin-bottom: 16px;
  padding: 10px 12px;
  background: rgba(100, 120, 180, 0.15);
  border-left: 3px solid #6b7fd7;
  color: #b0b8d0;
  font-size: 13px;
  line-height: 1.4;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px 15px;
  background-color: #111;
  border: 1px solid #333;
  border-radius: 2px;
  color: #fff;
  font-size: 14px;
  font-family: 'Roboto Mono', monospace;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #666;
  background-color: #151515;
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  padding: 25px;
  border-top: 1px solid #222;
  background-color: #0f0f0f;
}

.btn-secondary,
.btn-primary {
  padding: 12px 30px;
  border: none;
  border-radius: 2px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background-color: transparent;
  border: 1px solid #333;
  color: #888;
}

.btn-secondary:hover {
  border-color: #666;
  color: #fff;
}

.btn-primary {
  background-color: #fff;
  color: #000;
}

.btn-primary:hover:not(:disabled) {
  background-color: #e0e0e0;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  background-color: #333;
  color: #666;
  cursor: not-allowed;
}

.profile-picture-section {
  display: flex;
  align-items: center;
  gap: 30px;
}

.profile-picture-preview {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  border: 1px solid #333;
  flex-shrink: 0;
  background-color: #111;
}

.profile-picture-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-picture-placeholder {
  width: 100%;
  height: 100%;
  background: #222;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 48px;
  font-weight: 300;
}

.profile-picture-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.btn-upload, .btn-remove {
  padding: 10px 20px;
  border: none;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-upload {
  background-color: #333;
  color: #fff;
}

.btn-upload:hover {
  background-color: #444;
}

.btn-remove {
  background-color: transparent;
  border: 1px solid #333;
  color: #f44336;
}

.btn-remove:hover {
  border-color: #f44336;
  background-color: rgba(244, 67, 54, 0.1);
}

.char-count {
  font-size: 10px;
  color: #444;
  text-align: right;
  margin-top: 6px;
  font-family: 'Roboto Mono', monospace;
}

.toggle-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #111;
  padding: 12px 15px;
  border-radius: 2px;
  border: 1px solid #333;
}

.toggle-label {
  color: #fff;
  font-size: 14px;
}

.help-text {
  margin-top: 8px;
  font-size: 11px;
  color: #666;
  font-style: italic;
}

.model-version-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.model-version-row .version-label {
  margin: 0;
  min-width: 100px;
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.model-version-row .form-select {
  flex: 1;
  cursor: pointer;
}

/* Toggle Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 20px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #333;
  transition: .4s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 2px;
  bottom: 2px;
  background-color: white;
  transition: .4s;
}

input:checked + .slider {
  background-color: #4CAF50;
}

input:focus + .slider {
  box-shadow: 0 0 1px #4CAF50;
}

input:checked + .slider:before {
  transform: translateX(20px);
}

.slider.round {
  border-radius: 20px;
}

.slider.round:before {
  border-radius: 50%;
}

/* Settings Menu */
.settings-menu {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
  border-bottom: 1px solid #222;
  padding-bottom: 15px;
}

.menu-item {
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #666;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  bottom: -1px;
}

.menu-item:hover {
  color: #fff;
}

.menu-item.active {
  color: #fff;
  border-bottom-color: #fff;
}

.tab-content {
  animation: fadeIn 0.2s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* API Key Input Group */
.api-key-input-group {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.api-key-input-group .form-input {
  flex: 1;
}

.btn-test {
  padding: 12px 20px;
  background-color: #333;
  border: 1px solid #444;
  border-radius: 2px;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.btn-test:hover:not(:disabled) {
  background-color: #444;
  border-color: #555;
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.connection-status {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 2px;
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
}

.connection-status.success {
  background-color: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
  color: #4CAF50;
}

.connection-status.error {
  background-color: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
  color: #f44336;
}

/* Account Styles */
.accounts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #151515;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #333;
}

.account-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.account-platform-badge {
  background: #333;
  color: #fff;
  padding: 4px 8px;
  border-radius: 2px;
  font-size: 10px;
  font-weight: bold;
  text-transform: uppercase;
  min-width: 60px;
  text-align: center;
}

.account-details {
  display: flex;
  flex-direction: column;
}

.account-name {
  font-weight: 600;
  font-size: 14px;
  color: #fff;
}

.account-status {
  font-size: 10px;
  color: #666;
}

.account-status.active {
  color: #4caf50;
}

.account-actions {
  display: flex;
  gap: 10px;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.btn-icon:hover {
  opacity: 1;
}

.text-danger {
  color: #f44336;
}

.empty-state {
  text-align: center;
  color: #666;
  padding: 40px 0;
  font-style: italic;
}

.account-form {
  background: #151515;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #333;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.close-sub-form {
  background: none;
  border: none;
  color: #666;
  font-size: 24px;
  cursor: pointer;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 11px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}




/* Responsive Styles */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 10px;
    max-height: 95vh;
  }
  
  .settings-menu {
    overflow-x: auto;
    white-space: nowrap;
    padding-bottom: 10px;
    margin-bottom: 20px;
    -webkit-overflow-scrolling: touch;
  }
  
  .menu-item {
    font-size: 11px;
    padding: 8px 12px;
  }
  
  .api-key-input-group {
    flex-direction: column;
    gap: 8px;
  }
  
  .api-key-input-group .form-input, 
  .btn-test {
    width: 100%;
  }
  
  .account-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .account-info {
    width: 100%;
  }
  
  .account-actions {
    width: 100%;
    justify-content: flex-end;
    border-top: 1px solid #333;
    padding-top: 8px;
  }
  
  .form-header {
    flex-direction: row;
    align-items: center;
  }
  
  .modal-body {
    padding: 20px;
  }
  
  .modal-footer {
    padding: 20px;
    padding-bottom: max(20px, env(safe-area-inset-bottom));
    flex-direction: column-reverse;
    gap: 10px;
  }
  
  .modal-footer button {
    width: 100%;
    margin: 0;
    min-height: 48px;
  }
}

@media (max-width: 480px) {
  .modal-content {
    width: 100%;
    max-height: 98vh;
    margin: 8px;
  }

  .settings-menu {
    gap: 8px;
  }

  .menu-item {
    font-size: 10px;
    padding: 6px 10px;
  }
}
</style>


