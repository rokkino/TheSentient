<template>
  <div class="backtesting-panel">
    <div class="backtesting-header">
      <h2>📊 Backtesting - Simulazione Earning Report Genius</h2>
      <p class="subtitle">Simulazione storica massiva (What-If Analysis) su S&P 500 / Nasdaq</p>
      <button class="open-external-btn" @click="openInNewTab" title="Apri in nuova finestra">
        ↗ Apri in nuova finestra
      </button>
    </div>

    <div class="backtesting-content">
      <div class="embed-container">
        <iframe
          :src="streamlitUrl"
          class="backtesting-iframe"
          title="Backtesting Dashboard"
        />
      </div>
      <p class="hint">
        Avvia la dashboard: <code>cd streamlit_app && streamlit run app.py</code>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const streamlitUrl = ref('http://localhost:8501')

const openInNewTab = () => {
  window.open(streamlitUrl.value, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.backtesting-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
}

.backtesting-header {
  padding: 20px 24px;
  border-bottom: 1px solid #222;
  background: #0f0f0f;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.backtesting-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #888;
  flex: 1;
}

.open-external-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #444;
  color: #aaa;
  font-size: 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.open-external-btn:hover {
  border-color: #666;
  color: #fff;
}

.backtesting-content {
  flex: 1;
  min-height: 0;
  padding: 16px;
}

.embed-container {
  height: 100%;
  min-height: 500px;
  background: #111;
  border: 1px solid #222;
  border-radius: 4px;
  overflow: hidden;
}

.backtesting-iframe {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border: none;
}

.hint {
  margin: 12px 0 0 0;
  font-size: 12px;
  color: #666;
}

.hint code {
  background: #222;
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 11px;
}
</style>
