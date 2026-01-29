<template>
  <v-card class="pa-4 d-flex flex-column h-100" variant="outlined">
    <div class="d-flex justify-space-between align-center mb-4">
      <div class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-chart-line</v-icon>
        <div class="text-subtitle-1 font-weight-bold">Trend Trajectory</div>
      </div>

      <div class="d-flex gap-4 text-caption">
        <div class="d-flex align-center">
          <v-sheet class="mr-2" color="grey" height="2" width="12" />
          <span>Historical Data</span>
        </div>
        <div class="d-flex align-center">
          <v-sheet class="mr-2" color="primary" height="2" width="12" />
          <span class="font-weight-bold">Forecast</span>
        </div>
      </div>
    </div>

    <div class="flex-grow-1 position-relative" style="min-height: 300px;">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </v-card>
</template>

<script setup lang="ts">
  import {
    CategoryScale,
    Chart as ChartJS,
    Filler,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    Title,
    Tooltip,
  } from 'chart.js'
  import { computed } from 'vue'
  import { Line } from 'vue-chartjs'
  import { useForecastStore } from '@/stores/forecast'

  ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

  const store = useForecastStore()

  const chartData = computed(() => {
    if (store.forecastResults.length === 0 || store.historyResults.length === 0) return { labels: [], datasets: [] }

    const timeCol = store.timeCol
    const targetCol = store.targetCol

    // 1. Extract Vectors
    const historyLabels = store.historyResults.map((row: any) => row[timeCol])
    const historyData = store.historyResults.map((row: any) => row[targetCol])

    const forecastLabels = store.forecastResults.map((row: any) => row[timeCol])
    const forecastData = store.forecastResults.map((row: any) => row[targetCol])

    // 2. Connection Logic
    // To make the line continuous, we prepend the last history point to the forecast
    const lastHistoryVal = historyData.at(-1)

    // 3. Construct Datasets
    // We share a single Labels array for the X-axis
    const allLabels = [...historyLabels, ...forecastLabels]

    // Dataset A: History (Values ... Nulls)
    const plotHistory = [...historyData, ...Array.from({ length: forecastData.length }).fill(null)]

    // Dataset B: Forecast (Nulls ... Values)
    // We overlap the last history point so there is no visual gap
    const plotForecast = [
      ...Array.from({ length: historyData.length - 1 }).fill(null),
      lastHistoryVal,
      ...forecastData,
    ]

    return {
      labels: allLabels.map(d => new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' })),
      datasets: [
        {
          label: 'Historical',
          borderColor: '#9E9E9E', // Grey
          borderWidth: 2,
          pointRadius: 0, // Keep history clean (no dots) unless hovered
          pointHitRadius: 10,
          data: plotHistory,
          tension: 0.1,
        },
        {
          label: 'Forecast',
          backgroundColor: 'rgba(24, 103, 192, 0.1)', // Primary opacity
          borderColor: '#1867C0', // Primary Solid
          borderWidth: 3,
          pointRadius: 3, // Show dots for forecast points
          data: plotForecast,
          fill: true,
          tension: 0.3,
        },
      ],
    }
  })

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false }, // Using custom legend
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          maxTicksLimit: 8, // Prevent label crowding
          maxRotation: 0,
        },
      },
      y: {
        border: { display: false },
        grid: { color: '#f0f0f0' },
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  }
</script>
