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
          <v-sheet class="mr-2" :color="primaryLineColor" height="2" width="12" />
          <span class="font-weight-bold">{{ forecastLabel }}</span>
        </div>
        <div v-if="hasIntervals" class="d-flex align-center">
          <v-sheet
            class="mr-2"
            color="grey-lighten-2"
            height="8"
            style="opacity: 0.5"
            width="12"
          />
          <span>Confidence Range</span>
        </div>
      </div>
    </div>

    <!-- Risk Preference Message -->
    <v-alert
      v-if="riskMessage"
      class="mb-4"
      :color="riskAlertColor"
      density="compact"
      variant="tonal"
    >
      <template #prepend>
        <v-icon :icon="riskIcon" />
      </template>
      {{ riskMessage }}
    </v-alert>

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

  import type { RiskPreference } from '@/types'
  import { useForecastStore } from '@/stores/forecast'

  ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

  const store = useForecastStore()

  // Risk Preference styling
  const riskPreference = computed<RiskPreference>(() => {
    return store.ontology?.risk_preference || 'balanced'
  })

  const primaryLineColor = computed(() => {
    switch (riskPreference.value) {
      case 'under_penalty': { return '#F44336' } // Red for safety stock
      case 'over_penalty': { return '#2196F3' } // Blue for conservative
      default: { return '#1867C0' } // Primary
    }
  })

  const forecastLabel = computed(() => {
    switch (riskPreference.value) {
      case 'under_penalty': { return 'Upper Bound (Safety)' }
      case 'over_penalty': { return 'Lower Bound (Conservative)' }
      default: { return 'Forecast' }
    }
  })

  const riskMessage = computed(() => {
    switch (riskPreference.value) {
      case 'under_penalty': {
        return 'Showing upper bound (P90) to minimize risk of stockouts. Plan for higher inventory levels.'
      }
      case 'over_penalty': {
        return 'Showing lower bound (P10) to minimize waste. Order conservatively to avoid excess.'
      }
      default: { return null }
    }
  })

  const riskAlertColor = computed(() => {
    switch (riskPreference.value) {
      case 'under_penalty': { return 'error' }
      case 'over_penalty': { return 'info' }
      default: { return 'grey' }
    }
  })

  const riskIcon = computed(() => {
    switch (riskPreference.value) {
      case 'under_penalty': { return 'mdi-shield-alert' }
      case 'over_penalty': { return 'mdi-leaf' }
      default: { return 'mdi-scale-balance' }
    }
  })

  const hasIntervals = computed(() => {
    if (store.forecastResults.length === 0) return false
    const firstRow = store.forecastResults[0]
    return firstRow?.lower !== undefined && firstRow?.upper !== undefined
  })

  const chartData = computed(() => {
    if (store.forecastResults.length === 0 || store.historyResults.length === 0) {
      return { labels: [], datasets: [] }
    }

    const timeCol = store.timeCol
    const targetCol = store.targetCol

    // 1. Extract History Vectors
    const historyLabels = store.historyResults.map((row: any) => row[timeCol])
    const historyData = store.historyResults.map((row: any) => row[targetCol])

    // 2. Extract Forecast Vectors (new format with date/mean/lower/upper)
    const forecastLabels = store.forecastResults.map((row: any) => row.date || row[timeCol])
    const meanData = store.forecastResults.map((row: any) => row.mean ?? row[targetCol])
    const lowerData = store.forecastResults.map((row: any) => row.lower)
    const upperData = store.forecastResults.map((row: any) => row.upper)

    // 3. Connection Logic - prepend last history point
    const lastHistoryVal = historyData[historyData.length - 1]

    // 4. Construct combined labels
    const allLabels = [...historyLabels, ...forecastLabels]

    // 5. Build History dataset (values then nulls)
    const plotHistory = [...historyData, ...Array.from({ length: meanData.length }).fill(null)]

    // 6. Build Forecast datasets (nulls then values, with overlap at connection point)
    const nullPrefix = Array.from({ length: historyData.length - 1 }).fill(null)

    // Determine which forecast line to emphasize based on risk preference
    let primaryForecast: (number | null)[]
    switch (riskPreference.value) {
      case 'under_penalty': {
        primaryForecast = [...nullPrefix, lastHistoryVal, ...upperData]
        break
      }
      case 'over_penalty': {
        primaryForecast = [...nullPrefix, lastHistoryVal, ...lowerData]
        break
      }
      default: {
        primaryForecast = [...nullPrefix, lastHistoryVal, ...meanData]
      }
    }

    // Build datasets array
    const datasets: any[] = [
      {
        label: 'Historical',
        borderColor: '#9E9E9E',
        borderWidth: 2,
        pointRadius: 0,
        pointHitRadius: 10,
        data: plotHistory,
        tension: 0.1,
      },
    ]

    // Add confidence interval band if available
    if (hasIntervals.value) {
      const plotUpper = [...nullPrefix, lastHistoryVal, ...upperData]
      const plotLower = [...nullPrefix, lastHistoryVal, ...lowerData]

      datasets.push({
        label: 'Upper Bound',
        borderColor: 'rgba(158, 158, 158, 0.3)',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        data: plotUpper,
        fill: false,
        tension: 0.3,
      }, {
        label: 'Lower Bound',
        borderColor: 'rgba(158, 158, 158, 0.3)',
        borderWidth: 1,
        borderDash: [5, 5],
        pointRadius: 0,
        data: plotLower,
        fill: '-1', // Fill to previous dataset (upper)
        backgroundColor: 'rgba(158, 158, 158, 0.15)',
        tension: 0.3,
      })
    }

    // Add primary forecast line (on top)
    datasets.push({
      label: forecastLabel.value,
      backgroundColor: `${primaryLineColor.value}20`,
      borderColor: primaryLineColor.value,
      borderWidth: 3,
      pointRadius: 3,
      data: primaryForecast,
      fill: false,
      tension: 0.3,
    })

    return {
      labels: allLabels.map(d => new Date(d).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: '2-digit',
      })),
      datasets,
    }
  })

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          maxTicksLimit: 8,
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
