<template>
  <div
    class="flyout-panel"
    :class="{ visible: isVisible }"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
  >
    <div class="flyout-header">
      <h3>Feed Notizie</h3>
      <button class="view-toggle-btn" @click="$emit('view-toggle', 1)">View</button>
    </div>
    <div class="flyout-content">
      <NewsCard
        v-for="item in newsItems"
        :key="item.link"
        :news-item="item"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import NewsCard from './NewsCard.vue'

const props = defineProps({
  newsItems: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['view-toggle'])

const isVisible = ref(false)
let hideTimer = null

const checkMousePosition = (e) => {
  const windowWidth = window.innerWidth
  const mouseX = e.clientX
  const edgeThreshold = 50

  if (mouseX >= windowWidth - edgeThreshold) {
    isVisible.value = true
    if (hideTimer) {
      clearTimeout(hideTimer)
      hideTimer = null
    }
  } else if (mouseX < windowWidth - 300 - edgeThreshold) {
    scheduleHide()
  }
}

const scheduleHide = () => {
  if (hideTimer) clearTimeout(hideTimer)
  hideTimer = setTimeout(() => {
    if (!isVisible.value) return
    isVisible.value = false
  }, 5000)
}

const onMouseEnter = () => {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
}

const onMouseLeave = () => {
  scheduleHide()
}

onMounted(() => {
  window.addEventListener('mousemove', checkMousePosition)
  // Show when new news arrives
  if (props.newsItems.length > 0) {
    isVisible.value = true
    scheduleHide()
  }
})

onUnmounted(() => {
  window.removeEventListener('mousemove', checkMousePosition)
  if (hideTimer) clearTimeout(hideTimer)
})
</script>

<style scoped>
.flyout-panel {
  position: fixed;
  right: -300px;
  top: 0;
  width: 280px;
  height: 100vh;
  background-color: #2d2d2d;
  border-left: 1px solid #444;
  transition: right 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.flyout-panel.visible {
  right: 0;
}

.flyout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 2px solid #444;
}

.flyout-header h3 {
  font-size: 18px;
  font-weight: bold;
}

.view-toggle-btn {
  padding: 6px 12px;
  background-color: #3c3c3c;
  border: 1px solid #555;
  border-radius: 8px;
  color: #dcdcdc;
  cursor: pointer;
  font-size: 12px;
}

.view-toggle-btn:hover {
  background-color: #4a4a4a;
}

.flyout-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}
</style>

