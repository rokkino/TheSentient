<template>
  <div v-if="show" class="modal-overlay" @click="close">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Edit Profile</h2>
        <button class="close-btn" @click="close">×</button>
      </div>
      
      <div class="modal-body">
        <!-- Profile Picture Upload -->
        <div class="form-group">
          <label>Profile Picture</label>
          <div class="profile-picture-section">
            <div class="profile-picture-preview">
              <img 
                v-if="profilePicturePreview || profileData.profile_picture_url" 
                :src="profilePicturePreview || profileData.profile_picture_url" 
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
                v-if="profilePicturePreview || profileData.profile_picture_url" 
                @click="removeProfilePicture" 
                class="btn-remove"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label>First Name</label>
          <input v-model="profileData.first_name" type="text" class="form-input" />
        </div>
        
        <div class="form-group">
          <label>Last Name</label>
          <input v-model="profileData.last_name" type="text" class="form-input" />
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
          <label>Phone</label>
          <input v-model="profileData.phone" type="tel" class="form-input" />
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

const profileData = ref({
  first_name: '',
  last_name: '',
  bio: '',
  phone: '',
  location: '',
  website: '',
  profile_picture_url: ''
})

const userInitials = computed(() => {
  if (props.user) {
    const firstName = props.user.first_name || ''
    const lastName = props.user.last_name || ''
    if (firstName && lastName) {
      return (firstName[0] + lastName[0]).toUpperCase()
    }
    if (props.user.username) {
      return props.user.username.substring(0, 2).toUpperCase()
    }
  }
  return 'U'
})

watch(() => props.user, (newUser) => {
  if (newUser) {
    profileData.value = {
      first_name: newUser.first_name || '',
      last_name: newUser.last_name || '',
      bio: newUser.bio || '',
      phone: newUser.phone || '',
      location: newUser.location || '',
      website: newUser.website || '',
      profile_picture_url: newUser.profile_picture_url || ''
    }
    profilePicturePreview.value = null
    selectedFile.value = null
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
  background-color: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
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
</style>

