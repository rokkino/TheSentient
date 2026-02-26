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

:root {
  /* ── Glass Design System ── */
  --glass-bg: rgba(30, 41, 59, 0.5);
  --glass-bg-strong: rgba(15, 23, 42, 0.8);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-border-hover: rgba(255, 255, 255, 0.2);
  --glass-blur: blur(16px);
  --glass-blur-strong: blur(24px);

  /* ── Radii ── */
  --radius-sm: 8px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-full: 9999px;

  /* ── Shadows ── */
  --shadow-glass: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.35);
  --shadow-glow-gain: 0 0 30px rgba(52, 211, 153, 0.15);
  --shadow-glow-loss: 0 0 30px rgba(244, 63, 94, 0.15);

  /* ── Accent Colors ── */
  --accent-gain: #34d399;
  --accent-loss: #f43f5e;
  --accent-gain-bg: rgba(52, 211, 153, 0.15);
  --accent-loss-bg: rgba(244, 63, 94, 0.15);
  --accent-primary: #3b82f6;
  --accent-primary-bg: rgba(59, 130, 246, 0.15);

  /* ── Text ── */
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --text-white: #ffffff;

  /* ── Surfaces ── */
  --surface-0: #0b0e14;
  --surface-1: #0f172a;
  --surface-2: rgba(30, 41, 59, 0.5);
  --surface-3: rgba(51, 65, 85, 0.4);

  /* ── Transitions ── */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
  --transition-smooth: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

#app {
  width: 100%;
  height: 100vh;
  height: 100dvh;
  min-height: -webkit-fill-available;
  overflow: hidden;
  background: linear-gradient(160deg, #0b0e14 0%, #070a10 100%);
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
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--surface-0);
  color: var(--text-primary);
  letter-spacing: -0.01em;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.35);
}

/* Global button styles */
button {
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  font-weight: 500;
  letter-spacing: -0.01em;
  cursor: pointer;
  pointer-events: auto;
  touch-action: manipulation;
}
</style>

