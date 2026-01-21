<template>
  <div class="eps-history-chart">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading EPS data...</p>
    </div>
    <div v-else-if="!chartData || chartData.labels.length === 0" class="no-data">
      <p>No EPS history available</p>
    </div>
    <div v-else class="chart-container">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { Line } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale);

const props = defineProps({
  history: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const chartData = computed(() => {
  if (!props.history || props.history.length === 0) {
    return { labels: [], datasets: [] };
  }

  // Sort by date ascending
  const sortedData = [...props.history].sort((a, b) => new Date(a.date) - new Date(b.date));
  
  // Take last 8 quarters
  const recentData = sortedData.slice(-8);

  const labels = recentData.map(item => {
    const date = new Date(item.date);
    return `Q${Math.floor(date.getMonth() / 3) + 1} ${date.getFullYear()}`;
  });

  return {
    labels,
    datasets: [
      {
        label: 'EPS Estimate',
        borderColor: '#757575',
        backgroundColor: '#757575',
        data: recentData.map(item => item.estimate),
        tension: 0.1,
        pointStyle: 'circle',
        pointRadius: 6,
        borderDash: [5, 5]
      },
      {
        label: 'EPS Actual',
        borderColor: '#00e676', // Green for actual
        backgroundColor: '#00e676',
        data: recentData.map(item => item.actual),
        tension: 0.1,
        pointStyle: 'circle',
        pointRadius: 8
      }
    ]
  };
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        color: '#e0e0e0'
      }
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: function(context) {
          let label = context.dataset.label || '';
          if (label) {
            label += ': ';
          }
          if (context.parsed.y !== null) {
            label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
          }
          
          // Add surprise info if available
          const dataIndex = context.dataIndex;
          const item = props.history[props.history.length - 8 + dataIndex]; // Adjust index for slice
          if (item && item.surprise && context.datasetIndex === 1) { // Only on Actual dataset
             label += ` (Surprise: ${item.surprise}%)`;
          }
          
          return label;
        }
      }
    }
  },
  scales: {
    y: {
      grid: {
        color: '#333'
      },
      ticks: {
        color: '#aaa',
        callback: function(value) {
          return '$' + value;
        }
      }
    },
    x: {
      grid: {
        display: false
      },
      ticks: {
        color: '#aaa'
      }
    }
  }
};
</script>

<style scoped>
.eps-history-chart {
  height: 300px;
  width: 100%;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
}

.chart-container {
  height: 100%;
  width: 100%;
}

.loading-state, .no-data {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #888;
}

.spinner {
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top: 3px solid #00e676;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
