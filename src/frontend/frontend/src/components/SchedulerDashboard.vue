<template>
  <div class="scheduler-dashboard">
    <div class="dashboard-header">
      <h2>🤖 Auto-Trading Brain</h2>
      <div class="status-badge" :class="{ active: schedulerStatus.running }">
        {{ schedulerStatus.running ? 'SYSTEM ACTIVE' : 'SYSTEM STOPPED' }}
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- Left: Scheduler Status -->
      <div class="card scheduler-card">
        <h3>⏱️ Scheduler Heartbeat</h3>
        <div v-if="loading" class="loading">Loading...</div>
        <div v-else class="jobs-list">
          <div v-for="job in schedulerStatus.jobs" :key="job.id" class="job-item">
            <div class="job-info">
              <div class="job-name">{{ job.name }}</div>
              <div class="job-trigger">{{ job.trigger }}</div>
            </div>
            <div class="job-next">
              <span class="label">Next Run:</span>
              <span class="value">{{ formatTime(job.next_run_time) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Execution Logs -->
      <div class="card logs-card">
        <h3>📜 Activity Log</h3>
        <div class="logs-list">
          <div v-for="(log, index) in schedulerStatus.logs" :key="index" class="log-item" :class="log.status.toLowerCase()">
            <span class="log-time">{{ formatTime(log.timestamp) }}</span>
            <span class="log-job">[{{ log.job_name }}]</span>
            <span class="log-msg">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom: Decisions Table -->
    <div class="card decisions-card">
      <h3>🧠 AI Decisions (Gemini Analysis)</h3>
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Symbol</th>
              <th>Decision</th>
              <th>Execution</th>
              <th>Status</th>
              <th>Reasoning</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="decision in decisions" :key="decision.id">
              <td>{{ formatTime(decision.created_at) }}</td>
              <td class="symbol">{{ decision.symbol }}</td>
              <td :class="['decision-cell', decision.decision.toLowerCase()]">{{ decision.decision }}</td>
              <td>{{ formatTime(decision.execution_time) }}</td>
              <td>
                <span class="status-pill" :class="decision.status.toLowerCase()">
                  {{ decision.status }}
                </span>
              </td>
              <td class="reasoning" :title="decision.reasoning">{{ decision.reasoning }}</td>
            </tr>
            <tr v-if="decisions.length === 0">
              <td colspan="6" class="no-data">No decisions recorded yet</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../services/api'

const schedulerStatus = ref({ running: false, jobs: [], logs: [] })
const decisions = ref([])
const loading = ref(true)
const pollInterval = ref(null)

const fetchData = async () => {
  try {
    const [statusRes, decisionsRes] = await Promise.all([
      api.getSchedulerStatus(),
      api.getBotDecisions()
    ])
    schedulerStatus.value = statusRes.data
    decisions.value = decisionsRes.data.decisions
  } catch (e) {
    console.error("Error fetching scheduler data", e)
  } finally {
    loading.value = false
  }
}

const formatTime = (isoString) => {
  if (!isoString) return '--'
  return new Date(isoString).toLocaleTimeString()
}

onMounted(() => {
  fetchData()
  pollInterval.value = setInterval(fetchData, 5000) // Poll every 5s
})

onUnmounted(() => {
  if (pollInterval.value) clearInterval(pollInterval.value)
})
</script>

<style scoped>
.scheduler-dashboard {
  padding: 20px;
  background: #000;
  color: #e0e0e0;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 15px;
  border-bottom: 1px solid #333;
}

.dashboard-header h2 {
  margin: 0;
  font-size: 24px;
  background: linear-gradient(45deg, #2196F3, #00BCD4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.status-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
  background: #333;
  color: #888;
}

.status-badge.active {
  background: rgba(76, 175, 80, 0.2);
  color: #4CAF50;
  border: 1px solid #4CAF50;
  box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.card {
  background: #111;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 15px;
  display: flex;
  flex-direction: column;
}

.card h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
  color: #aaa;
  border-bottom: 1px solid #222;
  padding-bottom: 10px;
}

.jobs-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.job-item {
  background: #1a1a1a;
  padding: 10px;
  border-radius: 6px;
  border-left: 3px solid #2196F3;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.job-name {
  font-weight: bold;
  color: #fff;
}

.job-trigger {
  font-size: 11px;
  color: #666;
}

.job-next .label {
  color: #666;
  font-size: 11px;
  margin-right: 5px;
}

.job-next .value {
  color: #4CAF50;
  font-weight: bold;
}

.logs-card {
  max-height: 300px;
}

.logs-list {
  overflow-y: auto;
  flex: 1;
  font-family: monospace;
  font-size: 12px;
}

.log-item {
  padding: 4px 0;
  border-bottom: 1px solid #222;
  display: flex;
  gap: 10px;
}

.log-time {
  color: #666;
  min-width: 70px;
}

.log-job {
  color: #2196F3;
  min-width: 120px;
}

.log-msg {
  color: #ddd;
}

.log-item.error .log-msg { color: #F44336; }
.log-item.skipped .log-msg { color: #FF9800; }
.log-item.success .log-msg { color: #4CAF50; }

.decisions-card {
  flex: 1;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th {
  text-align: left;
  padding: 10px;
  color: #888;
  border-bottom: 1px solid #333;
}

td {
  padding: 10px;
  border-bottom: 1px solid #222;
}

.symbol {
  font-weight: bold;
  color: #fff;
}

.decision-cell {
  font-weight: bold;
}

.decision-cell.buy { color: #4CAF50; }
.decision-cell.sell { color: #F44336; }
.decision-cell.wait { color: #FF9800; }

.status-pill {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  text-transform: uppercase;
  background: #333;
}

.status-pill.pending { background: #FF9800; color: #000; }
.status-pill.executed { background: #4CAF50; color: #fff; }
.status-pill.failed { background: #F44336; color: #fff; }
.status-pill.skipped { background: #9E9E9E; color: #000; }

.reasoning {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #aaa;
}

.no-data {
  text-align: center;
  padding: 20px;
  color: #666;
}
</style>
