<template>
  <div class="tab-hero-card">
    <div class="hero-badge">{{ tag }}</div>
    <h1 class="hero-title">{{ title }}</h1>
    <p class="hero-subtitle">{{ description }}</p>
    <div class="hero-accent"></div>
  </div>
</template>

<script setup>
defineProps({
  tag: {
    type: String,
    default: 'ARENA'
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.tab-hero-card {
  text-align: center;
  margin-bottom: 24px;
  padding: 28px 24px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.6) 0%, transparent 100%);
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.08);
}

.hero-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #64748b;
  padding: 6px 14px;
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 100px;
  margin-bottom: 2px;
}

.hero-title {
  margin: 0;
  font-size: clamp(24px, 3.5vw, 34px);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #f1f5f9;
  line-height: 1.15;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.hero-subtitle {
  margin: 0;
  font-size: 14px;
  font-weight: 400;
  color: #94a3b8;
  max-width: 420px;
  line-height: 1.5;
  letter-spacing: 0.01em;
}

.hero-accent {
  width: 48px;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  border-radius: 2px;
  margin-top: 2px;
}
</style>
