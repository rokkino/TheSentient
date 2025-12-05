<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useWebSocketStore } from './stores/websocket'

const wsStore = useWebSocketStore()

onMounted(() => {
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
}

body {
  font-family: 'Segoe UI', Arial, sans-serif;
  background-color: #1e1e1e;
  color: #dcdcdc;
}
</style>

