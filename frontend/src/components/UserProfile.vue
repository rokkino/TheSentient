<template>
  <div class="user-profile">
    <div class="profile-trigger" @click="toggleMenu">
      <div class="profile-avatar">
        <img 
          v-if="profilePictureUrl" 
          :src="profilePictureUrl" 
          alt="Profile" 
          class="avatar-img"
        />
        <span v-else class="avatar-icon">{{ userInitials }}</span>
      </div>
      <span class="profile-name">{{ username || 'Guest' }}</span>
      <span class="dropdown-arrow" :class="{ open: showMenu }">▼</span>
    </div>
    
    <div v-if="showMenu" class="profile-menu" @click.stop>
      <div class="menu-header">
        <div class="menu-avatar">
          <img 
            v-if="profilePictureUrl" 
            :src="profilePictureUrl" 
            alt="Profile" 
            class="avatar-img-large"
          />
          <span v-else class="avatar-icon-large">{{ userInitials }}</span>
        </div>
        <div class="menu-info">
          <div class="menu-username">{{ username || 'Guest' }}</div>
          <div class="menu-email">{{ email || 'Not logged in' }}</div>
        </div>
      </div>
      
      <div class="menu-divider"></div>
      
      <div class="menu-items">
        <button v-if="!isLoggedIn" @click="showLogin" class="menu-item">
          <span class="menu-icon">🔐</span>
          Login
        </button>
        <button v-if="!isLoggedIn" @click="showRegister" class="menu-item">
          <span class="menu-icon">📝</span>
          Register
        </button>
        <button v-if="isLoggedIn" @click="viewProfile" class="menu-item">
          <span class="menu-icon">👤</span>
          Profile
        </button>
        <button v-if="isLoggedIn" @click="viewSettings" class="menu-item">
          <span class="menu-icon">⚙️</span>
          Settings
        </button>
        <button v-if="isLoggedIn" @click="logout" class="menu-item logout">
          <span class="menu-icon">🚪</span>
          Logout
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  username: {
    type: String,
    default: null
  },
  email: {
    type: String,
    default: null
  },
  isLoggedIn: {
    type: Boolean,
    default: false
  },
  profilePictureUrl: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['login', 'register', 'logout', 'profile', 'settings'])

const showMenu = ref(false)

const userInitials = computed(() => {
  if (props.username) {
    return props.username.substring(0, 2).toUpperCase()
  }
  return 'GU'
})

const toggleMenu = () => {
  showMenu.value = !showMenu.value
}

const closeMenu = () => {
  showMenu.value = false
}

const showLogin = () => {
  emit('login')
  closeMenu()
}

const showRegister = () => {
  emit('register')
  closeMenu()
}

const viewProfile = () => {
  emit('profile')
  closeMenu()
}

const viewSettings = () => {
  emit('settings')
  closeMenu()
}

const logout = () => {
  emit('logout')
  closeMenu()
}

// Close menu when clicking outside
onMounted(() => {
  document.addEventListener('click', closeMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
})
</script>

<style scoped>
.user-profile {
  position: relative;
  margin-left: auto;
}

.profile-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background-color: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.profile-trigger:hover {
  background-color: #1a1a1a;
}

.profile-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-icon {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 1px;
}

.profile-name {
  font-size: 13px;
  color: #e0e0e0;
  font-weight: 600;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dropdown-arrow {
  font-size: 8px;
  color: #666;
  transition: transform 0.2s;
}

.dropdown-arrow.open {
  transform: rotate(180deg);
}

.profile-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  background-color: #0a0a0a;
  border: 1px solid #333;
  border-radius: 2px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  min-width: 260px;
  z-index: 1000;
  overflow: hidden;
}

.menu-header {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background-color: #111;
  border-bottom: 1px solid #222;
}

.menu-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #222;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-img-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-icon-large {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.menu-info {
  flex: 1;
  min-width: 0;
}

.menu-username {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.menu-email {
  font-size: 11px;
  color: #888;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'Roboto Mono', monospace;
}

.menu-divider {
  height: 1px;
  background-color: #222;
  margin: 0;
}

.menu-items {
  padding: 8px 0;
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px 20px;
  background: none;
  border: none;
  color: #ccc;
  font-size: 13px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}

.menu-item:hover {
  background-color: #1a1a1a;
  color: #fff;
}

.menu-item.logout {
  color: #888;
  margin-top: 8px;
  border-top: 1px solid #222;
  padding-top: 16px;
}

.menu-item.logout:hover {
  background-color: #1a1a1a;
  color: #f44336;
}

.menu-icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
  color: #666;
}

.menu-item:hover .menu-icon {
  color: #fff;
}
</style>

