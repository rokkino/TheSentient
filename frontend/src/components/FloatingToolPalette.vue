<template>
  <div 
    ref="paletteRef"
    class="floating-tool-palette" 
    :style="{ left: x + 'px', top: y + 'px' }"
    @mousedown.stop
  >
    <div class="drag-handle" @mousedown="startDrag">
      <span class="drag-icon">⋮⋮</span>
    </div>
    
    <div class="tools-container">
      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'crosshair' || currentTool === null }"
        @click="$emit('set-tool', null)" 
        title="Cursor / Crosshair"
      >
        <span class="icon">✛</span>
      </div>

      <div class="separator"></div>

      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'line' }"
        @click="$emit('set-tool', 'line')" 
        title="Line"
      >
        <span class="icon">╱</span>
      </div>
      
      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'arrow' }"
        @click="$emit('set-tool', 'arrow')" 
        title="Arrow"
      >
        <span class="icon">➔</span>
      </div>

      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'hline' }"
        @click="$emit('set-tool', 'hline')" 
        title="Horizontal Line"
      >
        <span class="icon">▬</span>
      </div>

      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'vline' }"
        @click="$emit('set-tool', 'vline')" 
        title="Vertical Line"
      >
        <span class="icon">❙</span>
      </div>

      <div class="separator"></div>

      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'square' }"
        @click="$emit('set-tool', 'square')" 
        title="Square / Rectangle"
      >
        <span class="icon">⬜</span>
      </div>

      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'circle' }"
        @click="$emit('set-tool', 'circle')" 
        title="Circle"
      >
        <span class="icon">⭕</span>
      </div>
      
      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'triangle' }"
        @click="$emit('set-tool', 'triangle')" 
        title="Triangle"
      >
        <span class="icon">🔺</span>
      </div>

      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'polygon' }"
        @click="$emit('set-tool', 'polygon')" 
        title="Polygon"
      >
        <span class="icon">⬠</span>
      </div>

      <div class="separator"></div>

      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'freehand' }"
        @click="$emit('set-tool', 'freehand')" 
        title="Freehand Brush"
      >
        <span class="icon">🖌️</span>
      </div>

      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'text' }"
        @click="$emit('set-tool', 'text')" 
        title="Text"
      >
        <span class="icon">T</span>
      </div>

      <div class="separator"></div>
      
      <div 
        class="tool-btn" 
        @click="$emit('ai-draw')" 
        title="AI Draw"
      >
        <span class="icon">✨</span>
      </div>

      <div class="separator"></div>

      <div class="color-picker-wrapper" title="Color">
        <input 
          type="color" 
          :value="color" 
          @input="$emit('update:color', $event.target.value)"
          class="color-input" 
        />
      </div>

      <div class="separator"></div>
      
      <div 
        class="tool-btn" 
        @click="$emit('undo')" 
        title="Undo Last"
      >
        <span class="icon">↩️</span>
      </div>

      <div 
        class="tool-btn delete" 
        @click="$emit('clear-all')" 
        title="Clear All Drawings"
      >
        <span class="icon">🗑️</span>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  currentTool: {
    type: String,
    default: null
  },
  color: {
    type: String,
    default: '#2196F3'
  }
})

const emit = defineEmits(['set-tool', 'update:color', 'undo', 'clear-all', 'ai-draw'])

// Default: top-left inside chart (like second reference image)
const x = ref(16)
const y = ref(16)
const paletteRef = ref(null)
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

const startDrag = (event) => {
  const container = paletteRef.value?.parentElement
  if (!container) return
  const rect = container.getBoundingClientRect()
  isDragging.value = true
  dragOffset.value = {
    x: event.clientX - (rect.left + x.value),
    y: event.clientY - (rect.top + y.value)
  }
  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', stopDrag)
}

const handleDrag = (event) => {
  if (!isDragging.value) return
  const container = paletteRef.value?.parentElement
  if (!container) return
  const rect = container.getBoundingClientRect()
  const paletteEl = paletteRef.value
  const paletteW = paletteEl?.offsetWidth ?? 52
  const paletteH = paletteEl?.offsetHeight ?? 500

  let localX = (event.clientX - dragOffset.value.x) - rect.left
  let localY = (event.clientY - dragOffset.value.y) - rect.top

  // Clamp to stay inside chart bounds
  localX = Math.max(0, Math.min(localX, rect.width - paletteW))
  localY = Math.max(0, Math.min(localY, rect.height - paletteH))

  x.value = localX
  y.value = localY
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
}

</script>

<style scoped>
.floating-tool-palette {
  position: absolute;
  z-index: 1000;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
  display: flex;
  flex-direction: column;
  padding: 4px;
  width: 44px;
  user-select: none;
}

.drag-handle {
  height: 20px;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  border-bottom: 1px solid #333;
  margin-bottom: 4px;
}

.drag-handle:active {
  cursor: grabbing;
}

.tools-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
  align-items: center;
}

.tool-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  color: #aaa;
}

.tool-btn:hover {
  background: #333;
  color: #fff;
}

.tool-btn.active {
  background: #2196F3;
  color: #fff;
}

.tool-btn.delete:hover {
  background: #d32f2f;
  color: #fff;
}

.separator {
  height: 1px;
  width: 20px;
  background: #333;
  margin: 4px 0;
}

.color-picker-wrapper {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #333;
  cursor: pointer;
  margin: 2px 0;
}

.color-input {
  width: 150%;
  height: 150%;
  margin: -25%;
  padding: 0;
  border: none;
  cursor: pointer;
}


.icon {
  font-size: 16px;
  line-height: 1;
}

@media (max-width: 768px) {
  .floating-tool-palette {
    flex-direction: row;
    width: auto;
    height: 48px;
    min-height: 48px;
    left: 50% !important;
    top: auto !important;
    bottom: max(12px, env(safe-area-inset-bottom));
    transform: translateX(-50%);
    padding: 0 8px;
    overflow-x: auto;
    max-width: 95vw;
    -webkit-overflow-scrolling: touch;
  }

  .tools-container {
    flex-direction: row;
    gap: 6px;
  }

  .separator {
    width: 1px;
    height: 20px;
    margin: 0 2px;
  }

  .drag-handle {
    display: none;
  }
  
  .tool-btn {
    flex-shrink: 0;
  }
}

</style>
