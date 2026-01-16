<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>Settings</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>
      <div class="modal-body">
        <div class="placeholder">
          <div class="placeholder-icon">⚙️</div>
          <p class="placeholder-text">Settings coming soon...</p>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')" class="close-button">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const emit = defineEmits(['close'])
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
  backdrop-filter: blur(4px);
}

.modal-content {
  background-color: #1a1a1a;
  border-radius: 12px;
  width: 400px;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  border: 1px solid #333;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #333;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5px;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
  background-color: #333;
}

.modal-body {
  padding: 60px 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.placeholder {
  text-align: center;
}

.placeholder-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.placeholder-text {
  color: #888;
  font-size: 16px;
  margin: 0;
  letter-spacing: 0.3px;
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid #333;
  display: flex;
  justify-content: flex-end;
}

.close-button {
  padding: 10px 24px;
  border-radius: 6px;
  border: 1px solid #444;
  background-color: #2a2a2a;
  color: #dcdcdc;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  letter-spacing: 0.3px;
}

.close-button:hover {
  background-color: #333;
  border-color: #555;
  color: #fff;
}
</style>
