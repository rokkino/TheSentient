<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useWebSocketStore } from './stores/websocket'
import { useAuthStore } from './stores/auth'

const wsStore = useWebSocketStore()
const authStore = useAuthStore()

onMounted(async () => {
  // Check authentication on app start
  await authStore.checkAuth()
  wsStore.connect()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
  background-color: #000000;
}

body {
  font-family: 'Helvetica Neue', 'Arial', sans-serif;
  background-color: #000000;
  color: #e0e0e0;
  letter-spacing: 0.5px;
}

/* Scrollbar styling for a sleeker look */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #0a0a0a;
}

::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Global button styles override */
button {
  font-family: 'Helvetica Neue', 'Arial', sans-serif;
  font-weight: 500;
  letter-spacing: 0.5px;
}
</style>

