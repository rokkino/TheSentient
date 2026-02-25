<template>
  <div class="revenue-earnings-chart">
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading financial data...</p>
    </div>
    <div v-else-if="!chartData || chartData.labels.length === 0" class="no-data">
      <p>No financial data available</p>
    </div>
    <div v-else class="chart-container">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const props = defineProps({
  financials: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const chartData = computed(() => {
  if (!props.financials || props.financials.length === 0) {
    return { labels: [], datasets: [] };
  }

  // Sort by date ascending
  const sortedData = [...props.financials].sort((a, b) => new Date(a.date) - new Date(b.date));
  
  // Take last 8 quarters (2 years)
  const recentData = sortedData.slice(-8);

  const labels = recentData.map(item => {
    const date = new Date(item.date);
    return `Q${Math.floor(date.getMonth() / 3) + 1} ${date.getFullYear()}`;
  });

  return {
    labels,
    datasets: [
      {
        label: 'Revenue',
        backgroundColor: '#42a5f5',
        data: recentData.map(item => item.revenue),
        barPercentage: 0.6,
        categoryPercentage: 0.8
      },
      {
        label: 'Earnings',
        backgroundColor: '#ffca28',
        data: recentData.map(item => item.earnings),
        barPercentage: 0.6,
        categoryPercentage: 0.8
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
            label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: "compact", compactDisplay: "short" }).format(context.parsed.y);
          }
          return label;
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: '#333'
      },
      ticks: {
        color: '#aaa',
        callback: function(value) {
          return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(value);
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
.revenue-earnings-chart {
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
  border-top: 3px solid #42a5f5;
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
