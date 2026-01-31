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

onMounted(() => {
  // Auth e WebSocket in background - non bloccano l'UI
  authStore.checkAuth().catch(() => {})
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
  height: 100dvh;
  min-height: -webkit-fill-available;
  overflow: hidden;
  background: linear-gradient(180deg, #0d0d0f 0%, #08080a 100%);
  pointer-events: auto;
  position: relative;
  z-index: 0;
  padding-top: env(safe-area-inset-top);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  padding-bottom: env(safe-area-inset-bottom);
}

@media (max-width: 768px) {
  #app {
    overflow: auto;
    -webkit-overflow-scrolling: touch;
  }
}

body {
  font-family: 'Helvetica Neue', 'Arial', sans-serif;
  background: #0a0a0c;
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

/* Global button styles - assicurarsi che siano cliccabili */
button {
  font-family: 'Helvetica Neue', 'Arial', sans-serif;
  font-weight: 500;
  letter-spacing: 0.5px;
  cursor: pointer;
  pointer-events: auto;
  touch-action: manipulation;
}
</style>

