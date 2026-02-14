<template>
  <v-card class="pa-4 d-flex flex-column h-100" variant="outlined">
    <div class="d-flex justify-space-between align-center mb-4">
      <div class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-chart-line</v-icon>
        <div class="text-subtitle-1 font-weight-bold">Trend Trajectory</div>
      </div>

      <div class="d-flex align-center gap-4">
        <!-- Zoom Reset Button -->
        <v-btn
          v-if="isZoomed"
          color="primary"
          prepend-icon="mdi-restore"
          size="small"
          variant="outlined"
          @click="resetZoom"
        >
          Reset Zoom
        </v-btn>

        <!-- Legend -->
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
      <Line id="forecast-chart" :data="chartData" :options="chartOptions" />
    </div>
  </v-card>
</template>

<script setup lang="ts">
  import type { RiskPreference } from '@/types'

  import {
    Chart as ChartJS,
    Filler,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    TimeScale, // Import TimeScale
    Title,
    Tooltip,
  } from 'chart.js'
  import zoomPlugin from 'chartjs-plugin-zoom'
  import { computed, ref } from 'vue'
  import { Line } from 'vue-chartjs'

  import { useForecastStore } from '@/stores/forecast'
  import 'chartjs-adapter-date-fns' // Import date adapter

  // Register TimeScale instead of just CategoryScale
  ChartJS.register(
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
    TimeScale,
    zoomPlugin,
  )

  const store = useForecastStore()
  const isZoomed = ref(false)

  // Risk Preference styling
  const riskPreference = computed<RiskPreference>(() => {
    return store.ontology?.risk_preference || 'balanced'
  })

  // ... (color and label logic remains same)
  const primaryLineColor = computed(() => {
    switch (riskPreference.value) {
      case 'under_penalty': { return '#F44336' }
      case 'over_penalty': { return '#2196F3' }
      default: { return '#1867C0' }
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
      return { datasets: [] }
    }

    const timeCol = store.timeCol
    const targetCol = store.targetCol

    // Helper to parse dates simply
    const parseDate = (d: any) => new Date(d).getTime()

    // 1. Prepare History Data Points {x, y}
    const historyPoints = store.historyResults.map((row: any) => ({
      x: parseDate(row[timeCol]),
      y: row[targetCol],
    }))

    // 2. Prepare Forecast Data Points {x, y, lower, upper}
    // We treat them as points now, not parallel arrays
    const forecastPoints = store.forecastResults.map((row: any) => ({
      x: parseDate(row.date || row[timeCol]),
      y: row.mean ?? row[targetCol],
      lower: row.lower,
      upper: row.upper,
    }))

    // 3. Connect History to Forecast
    // To make a continuous line, the forecast should start where history ends
    // or we verify if there's a gap. Usually we just append.
    // For the "mean" line, we might want a visually distinct line, so we keep them separate datasets usually.
    // But to connect them visually without a gap, we add the last history point to the forecast dataset.
    const lastHistoryPoint = historyPoints.at(-1)

    // Forecast Main Line
    const forecastMainPoints = [lastHistoryPoint, ...forecastPoints.map((p: any) => ({ x: p.x, y: p.y }))]

    // Forecast Intervals (if needed)
    const upperPoints = hasIntervals.value
      ? [lastHistoryPoint, ...forecastPoints.map((p: any) => ({ x: p.x, y: p.upper }))]
      : []
    const lowerPoints = hasIntervals.value
      ? [lastHistoryPoint, ...forecastPoints.map((p: any) => ({ x: p.x, y: p.lower }))]
      : []

    // 4. Select Primary Forecast based on Risk
    let primaryPoints
    switch (riskPreference.value) {
      case 'under_penalty': {
        primaryPoints = upperPoints.length > 0 ? upperPoints : forecastMainPoints
        break
      }
      case 'over_penalty': {
        primaryPoints = lowerPoints.length > 0 ? lowerPoints : forecastMainPoints
        break
      }
      default: {
        primaryPoints = forecastMainPoints
      }
    }

    const datasets: any[] = [
      {
        label: 'Historical',
        borderColor: '#9E9E9E',
        borderWidth: 2,
        pointRadius: 0,
        pointHitRadius: 10,
        data: historyPoints,
        tension: 0.1,
      },
    ]

    if (hasIntervals.value) {
      datasets.push(
        {
          label: 'Upper Bound',
          borderColor: 'rgba(158, 158, 158, 0.3)',
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          data: upperPoints,
          fill: false,
          tension: 0.3,
        },
        {
          label: 'Lower Bound',
          borderColor: 'rgba(158, 158, 158, 0.3)',
          borderWidth: 1,
          borderDash: [5, 5],
          pointRadius: 0,
          data: lowerPoints,
          fill: '-1', // Fill to previous dataset (upper)
          backgroundColor: 'rgba(158, 158, 158, 0.15)',
          tension: 0.3,
        },
      )
    }

    datasets.push({
      label: forecastLabel.value,
      backgroundColor: `${primaryLineColor.value}20`,
      borderColor: primaryLineColor.value,
      borderWidth: 3,
      pointRadius: 3,
      data: primaryPoints,
      fill: false,
      tension: 0.3,
    })

    return { datasets }
  })

  function resetZoom () {
    const chart = ChartJS.getChart('forecast-chart')
    if (chart) {
      chart.resetZoom()
      isZoomed.value = false
    }
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
      zoom: {
        pan: {
          enabled: true,
          mode: 'x' as const,
          onPan: () => {
            isZoomed.value = true
          },
        },
        zoom: {
          wheel: {
            enabled: true,
            speed: 0.1,
          },
          pinch: {
            enabled: true,
          },
          mode: 'x' as const,
          onZoom: () => {
            isZoomed.value = true
          },
        },
        limits: {
          x: { min: 'original' as const, max: 'original' as const },
          y: { min: 'original' as const, max: 'original' as const },
        },
      },
    },
    scales: {
      x: {
        type: 'time' as const, // Use Time Scale
        time: {
          unit: 'day' as const, // Provide a default unit, but it auto-scales
          displayFormats: {
            day: 'MMM d',
            month: 'MMM yyyy',
          },
          tooltipFormat: 'PP',
        },
        grid: { display: false },
        ticks: {
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 8,
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
