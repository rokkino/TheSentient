<template>
  <div 
    ref="paletteRef"
    class="floating-tool-palette" 
    :class="{ expanded: isExpanded }"
    :style="{ left: x + 'px', top: y + 'px' }"
    @mousedown.stop
  >
    <div class="drag-handle" @mousedown="startDrag">
      <span class="drag-icon">⋮⋮</span>
    </div>
    
    <div class="tools-container">
      <!-- Selection Tools -->
      <div 
        class="tool-btn" 
        :class="{ active: currentTool === 'crosshair' || currentTool === null }"
        @click="$emit('set-tool', null)" 
        title="Cursor / Crosshair (Esc)"
      >
        <span class="icon">✛</span>
      </div>

      <div class="separator"></div>

      <!-- Line Tools -->
      <div class="tool-group">
        <div 
          class="tool-btn" 
          :class="{ active: currentTool === 'line' }"
          @click="$emit('set-tool', 'line')" 
          title="Trend Line"
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
          :class="{ active: currentTool === 'ray' }"
          @click="$emit('set-tool', 'ray')" 
          title="Ray (infinite line)"
        >
          <span class="icon">↗</span>
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

        <div 
          class="tool-btn" 
          :class="{ active: currentTool === 'channel' }"
          @click="$emit('set-tool', 'channel')" 
          title="Parallel Channel"
        >
          <span class="icon">⫽</span>
        </div>
      </div>

      <div class="separator"></div>

      <!-- Fibonacci & Analysis Tools -->
      <div class="tool-group">
        <div 
          class="tool-btn special" 
          :class="{ active: currentTool === 'fib' }"
          @click="$emit('set-tool', 'fib')" 
          title="Fibonacci Retracement"
        >
          <span class="icon">𝜑</span>
        </div>

        <div 
          class="tool-btn" 
          :class="{ active: currentTool === 'priceRange' }"
          @click="$emit('set-tool', 'priceRange')" 
          title="Price Range"
        >
          <span class="icon">⇕</span>
        </div>

        <div 
          class="tool-btn" 
          :class="{ active: currentTool === 'measure' }"
          @click="$emit('set-tool', 'measure')" 
          title="Measure Tool"
        >
          <span class="icon">📏</span>
        </div>
      </div>

      <div class="separator"></div>

      <!-- Shape Tools -->
      <div class="tool-group">
        <div 
          class="tool-btn" 
          :class="{ active: currentTool === 'square' }"
          @click="$emit('set-tool', 'square')" 
          title="Rectangle"
        >
          <span class="icon">⬜</span>
        </div>

        <div 
          class="tool-btn" 
          :class="{ active: currentTool === 'circle' }"
          @click="$emit('set-tool', 'circle')" 
          title="Ellipse"
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
      </div>

      <div class="separator"></div>

      <!-- Drawing Tools -->
      <div class="tool-group">
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
          title="Text Annotation"
        >
          <span class="icon">T</span>
        </div>

        <div 
          class="tool-btn" 
          :class="{ active: currentTool === 'callout' }"
          @click="$emit('set-tool', 'callout')" 
          title="Callout"
        >
          <span class="icon">💬</span>
        </div>

        <div 
          class="tool-btn" 
          :class="{ active: currentTool === 'icon' }"
          @click="$emit('set-tool', 'icon')" 
          title="Icon/Emoji"
        >
          <span class="icon">⭐</span>
        </div>
      </div>

      <div class="separator"></div>
      
      <!-- AI Tools -->
      <div 
        class="tool-btn ai-btn" 
        @click="$emit('ai-draw')" 
        title="AI Draw - Let AI add annotations"
      >
        <span class="icon">✨</span>
      </div>

      <div class="separator"></div>

      <!-- Color Picker -->
      <div class="color-picker-wrapper" title="Drawing Color">
        <input 
          type="color" 
          :value="color" 
          @input="$emit('update:color', $event.target.value)"
          class="color-input" 
        />
      </div>

      <!-- Quick Colors -->
      <div class="quick-colors">
        <div 
          v-for="qc in quickColors" 
          :key="qc"
          class="quick-color"
          :style="{ backgroundColor: qc }"
          :class="{ active: color === qc }"
          @click="$emit('update:color', qc)"
          :title="qc"
        ></div>
      </div>

      <div class="separator"></div>
      
      <!-- Actions -->
      <div 
        class="tool-btn" 
        @click="$emit('undo')" 
        title="Undo Last (Ctrl+Z)"
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

      <!-- Expand/Collapse Toggle -->
      <div 
        class="tool-btn toggle-btn" 
        @click="isExpanded = !isExpanded" 
        :title="isExpanded ? 'Collapse' : 'Expand'"
      >
        <span class="icon">{{ isExpanded ? '◀' : '▶' }}</span>
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
const isExpanded = ref(true)

// Quick color presets
const quickColors = [
  '#2196F3', // Blue
  '#26a69a', // Green
  '#ef5350', // Red
  '#ff9800', // Orange
  '#9c27b0', // Purple
  '#ffffff', // White
]

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
  background: linear-gradient(180deg, #1e1e1e 0%, #161616 100%);
  border: 1px solid #333;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05) inset;
  display: flex;
  flex-direction: column;
  padding: 6px;
  width: 82px;
  user-select: none;
  transition: width 0.2s ease, opacity 0.2s ease;
}

.floating-tool-palette:not(.expanded) {
  width: 48px;
}

.floating-tool-palette:not(.expanded) .tool-group,
.floating-tool-palette:not(.expanded) .quick-colors {
  display: none;
}

.drag-handle {
  height: 24px;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #555;
  border-bottom: 1px solid #2a2a2a;
  margin-bottom: 6px;
  transition: color 0.2s;
}

.drag-handle:hover {
  color: #888;
}

.drag-handle:active {
  cursor: grabbing;
  color: #fff;
}

.drag-icon {
  font-size: 12px;
  letter-spacing: 2px;
}

.tools-container {
  display: flex;
  flex-direction: column;
  gap: 3px;
  align-items: center;
}

.tool-group {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
  width: 100%;
}

.tool-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: #888;
  position: relative;
}

.tool-btn:hover {
  background: linear-gradient(180deg, #333 0%, #2a2a2a 100%);
  color: #fff;
  transform: scale(1.05);
}

.tool-btn.active {
  background: linear-gradient(180deg, #2196F3 0%, #1976D2 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.4);
}

.tool-btn.special {
  color: #ffd700;
}

.tool-btn.special:hover {
  color: #fff;
  background: linear-gradient(180deg, #ffd700 0%, #ffb300 100%);
}

.tool-btn.special.active {
  background: linear-gradient(180deg, #ffd700 0%, #ffb300 100%);
  color: #000;
}

.tool-btn.ai-btn {
  background: linear-gradient(135deg, rgba(147, 51, 234, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%);
  border: 1px solid rgba(147, 51, 234, 0.3);
}

.tool-btn.ai-btn:hover {
  background: linear-gradient(135deg, rgba(147, 51, 234, 0.4) 0%, rgba(59, 130, 246, 0.4) 100%);
  border-color: rgba(147, 51, 234, 0.5);
}

.tool-btn.delete:hover {
  background: linear-gradient(180deg, #d32f2f 0%, #b71c1c 100%);
  color: #fff;
}

.tool-btn.toggle-btn {
  margin-top: 4px;
  height: 24px;
  font-size: 10px;
  color: #555;
}

.tool-btn.toggle-btn:hover {
  color: #888;
  background: transparent;
  transform: none;
}

.separator {
  height: 1px;
  width: 100%;
  background: linear-gradient(90deg, transparent 0%, #333 50%, transparent 100%);
  margin: 8px 0;
}

.color-picker-wrapper {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid #444;
  cursor: pointer;
  margin: 4px 0;
  transition: border-color 0.2s, transform 0.2s;
}

.color-picker-wrapper:hover {
  border-color: #666;
  transform: scale(1.1);
}

.color-input {
  width: 150%;
  height: 150%;
  margin: -25%;
  padding: 0;
  border: none;
  cursor: pointer;
}

.quick-colors {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  padding: 4px 0;
}

.quick-color {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  cursor: pointer;
  border: 1px solid rgba(255,255,255,0.1);
  transition: all 0.15s ease;
}

.quick-color:hover {
  transform: scale(1.2);
  border-color: rgba(255,255,255,0.3);
}

.quick-color.active {
  border-color: #fff;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.2);
}

.icon {
  font-size: 15px;
  line-height: 1;
}

/* Mobile Styles */
@media (max-width: 768px) {
  .floating-tool-palette {
    flex-direction: row;
    width: auto !important;
    height: 52px;
    min-height: 52px;
    left: 50% !important;
    top: auto !important;
    bottom: max(16px, env(safe-area-inset-bottom));
    transform: translateX(-50%);
    padding: 0 12px;
    overflow-x: auto;
    max-width: 95vw;
    -webkit-overflow-scrolling: touch;
    border-radius: 26px;
  }

  .tools-container {
    flex-direction: row;
    gap: 8px;
  }

  .tool-group {
    flex-direction: row;
    width: auto;
    gap: 4px;
  }

  .separator {
    width: 1px;
    height: 24px;
    margin: 0 4px;
    background: linear-gradient(180deg, transparent 0%, #333 50%, transparent 100%);
  }

  .drag-handle {
    display: none;
  }
  
  .tool-btn {
    flex-shrink: 0;
  }

  .tool-btn.toggle-btn {
    display: none;
  }

  .quick-colors {
    flex-direction: row;
    flex-wrap: nowrap;
    padding: 0;
  }
}

</style>
