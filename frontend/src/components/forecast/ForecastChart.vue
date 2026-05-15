<template>
  <v-card class="pa-4 d-flex flex-column h-100" variant="outlined">
    <div class="d-flex justify-space-between align-center mb-4">
      <div class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-chart-line</v-icon>
        <div class="text-subtitle-1 font-weight-bold">Forecast Path</div>
      </div>

      <div class="d-flex align-center gap-4">
        <!-- Risk View Toggle -->
        <v-btn-toggle
          v-model="riskView"
          density="comfortable"
          mandatory
          selected-class="bg-primary text-white"
        >
          <v-btn size="small" value="off">Standard</v-btn>
          <v-btn size="small" value="on">Risk View</v-btn>
        </v-btn-toggle>

        <!-- Action Buttons -->
        <div class="d-flex align-center gap-2">
          <v-btn
            icon="mdi-content-copy"
            size="small"
            title="Copy Image"
            variant="text"
            @click="copyImage"
          />
          <v-btn
            icon="mdi-camera"
            size="small"
            title="Save as Image"
            variant="text"
            @click="exportImage"
          />
          <v-btn
            v-if="isZoomed"
            class="ml-2"
            color="primary"
            prepend-icon="mdi-restore"
            size="small"
            title="Reset Zoom"
            variant="tonal"
            @click="resetZoom"
          >
            Reset Zoom
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Legend Bar -->
    <div class="d-flex justify-center gap-6 mb-4 text-caption">
      <!-- Standard Legend -->
      <template v-if="riskView === 'off'">
        <div class="d-flex align-center">
          <v-sheet class="mr-2" color="grey" height="2" width="12" />
          <span>Historical</span>
        </div>
        <div class="d-flex align-center">
          <v-sheet class="mr-2" :color="primaryLineColor" height="2" width="12" />
          <span>Forecast</span>
        </div>
        <div v-if="hasIntervals" class="d-flex align-center">
          <v-sheet
            class="mr-2"
            color="blue-darken-2"
            height="12"
            style="opacity: 0.1"
            width="12"
          />
          <span>Prediction Range</span>
        </div>
      </template>

      <!-- Fan Chart Key (Risk View) -->
      <template v-else>
        <div class="d-flex align-center">
          <v-sheet
            class="mr-2 rounded-sm"
            color="blue-lighten-4"
            height="12"
            style="opacity: 0.6"
            width="12"
          />
          <span>80% Prediction (Outer)</span>
        </div>
        <div class="d-flex align-center">
          <v-sheet
            class="mr-2 rounded-sm"
            color="blue-lighten-2"
            height="12"
            style="opacity: 0.6"
            width="12"
          />
          <span>60% Prediction (Middle)</span>
        </div>
        <div class="d-flex align-center">
          <v-sheet
            class="mr-2 rounded-sm"
            color="blue-darken-2"
            height="12"
            style="opacity: 0.8"
            width="12"
          />
          <span>30% Prediction (Inner)</span>
        </div>
      </template>
    </div>

    <!-- Risk Preference Message -->
    <v-alert
      v-if="riskMessage && riskView === 'off'"
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

    <div class="flex-grow-1 position-relative" style="min-height: 350px;">
      <Line id="forecast-chart" :data="chartData" :options="chartOptions" />
    </div>

    <!-- Chart zoom hint -->
    <div class="d-flex justify-center mt-2">
      <span class="text-caption text-medium-emphasis">Scroll or pinch to zoom, drag to pan</span>
    </div>
  </v-card>
</template>

<script setup lang="ts">
  import type { RiskPreference } from '@/types'

  import {
    Chart as ChartJS,
    Decimation,
    Filler,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    TimeScale,
    Title,
    Tooltip,
  } from 'chart.js'
  import zoomPlugin from 'chartjs-plugin-zoom'
  import { computed, ref, watch } from 'vue'
  import { Line } from 'vue-chartjs'

  import { useAppStore } from '@/stores/app'
  import { useForecastStore } from '@/stores/forecast'
  import { formatNumber } from '@/utils/formatters'
  import 'chartjs-adapter-date-fns'

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
    Decimation,
  )

  const store = useForecastStore()
  const appStore = useAppStore()
  const isZoomed = ref(false)
  const riskView = ref('off')

  // Range Selector State
  const rangeMin = ref<number | null>(null)
  const rangeMax = ref<number | null>(null)

  // Auto-zoom to ensure forecast is at least 10% of visible area
  watch(
    () => store.forecastResults,
    () => {
      if (!store.historyResults?.length || !store.forecastResults?.length) {
        rangeMin.value = null
        rangeMax.value = null
        isZoomed.value = false
        return
      }

      const timeCol = store.timeCol
      const historyTimes = store.historyResults.map((r: any) => parseDate(r[timeCol])).filter((t: number) => !Number.isNaN(t))
      const forecastTimes = store.forecastResults.map((r: any) => parseDate(r.date || r.year || r[timeCol])).filter((t: number) => !Number.isNaN(t))

      if (historyTimes.length === 0 || forecastTimes.length === 0) return

      const minHist = historyTimes[0]
      const maxHist = historyTimes.at(-1)
      const minFore = forecastTimes[0]
      const maxFore = forecastTimes.at(-1)

      if (minHist === undefined || maxHist === undefined || minFore === undefined || maxFore === undefined) return

      const forecastDuration = maxFore - minFore
      const effectiveForecastDuration = forecastDuration > 0 ? forecastDuration : Math.max(0, maxFore - maxHist)
      const totalDuration = maxFore - minHist

      if (effectiveForecastDuration > 0 && effectiveForecastDuration < totalDuration * 0.1) {
        const visibleWindow = effectiveForecastDuration * 10
        rangeMin.value = Math.max(minHist, maxFore - visibleWindow)
        rangeMax.value = maxFore
        isZoomed.value = true
      }
    },
    { immediate: true },
  )

  // Shared Date Parsing Logic
  function parseDate (d: any): number {
    if (d === null || d === undefined) return Number.NaN
    // Handle 4-digit years (as numbers or strings)
    const num = Number(d)
    if (!Number.isNaN(num) && num > 1100 && num < 2500) {
      return new Date(num, 0, 1).getTime()
    }
    return new Date(d).getTime()
  }

  // Risk Preference styling
  const riskPreference = computed<RiskPreference>(() => {
    return store.ontology?.risk_preference || 'balanced'
  })

  const primaryLineColor = computed(() => {
    switch (riskPreference.value) {
      case 'under_penalty': { return '#F44336' }
      case 'over_penalty': { return '#2196F3' }
      default: { return '#1867C0' }
    }
  })

  const riskMessage = computed(() => {
    switch (riskPreference.value) {
      case 'under_penalty': {
        return 'Showing upper bound (P90) to minimize risk of stockouts.'
      }
      case 'over_penalty': {
        return 'Showing lower bound (P10) to minimize waste.'
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
    const row = store.forecastResults[0]
    if (!row) return false
    return row.conf_80_upper !== undefined || (row.lower !== undefined && row.upper !== undefined)
  })

  const chartData = computed(() => {
    if (store.forecastResults.length === 0 || store.historyResults.length === 0) {
      return { datasets: [] }
    }

    const timeCol = store.timeCol
    const targetCol = store.targetCol

    const historyPoints = store.historyResults.map((row: any) => ({
      x: parseDate(row[timeCol]),
      y: row[targetCol],
    }))

    const lastHistoryPoint = historyPoints.at(-1)

    // Build the foreground/background datasets based on Risk View toggle
    if (riskView.value === 'on') {
      const forecastData = store.forecastResults.map((row: any) => ({
        x: parseDate(row.date || row.year || row[timeCol]),
        median: row.median_forecast ?? row.mean ?? row[targetCol],
        p10: row.conf_80_lower,
        p90: row.conf_80_upper,
        p20: row.conf_60_lower,
        p80: row.conf_80_upper,
        p35: row.conf_30_lower,
        p65: row.conf_30_upper,
      }))

      // Connector point with range info (all range points start from the same history point)
      const connect = (y: number, upper?: number) => ({ x: lastHistoryPoint?.x, y, upper })

      const datasets = [
        {
          label: 'Historical',
          borderColor: '#9E9E9E',
          borderWidth: 2,
          pointRadius: 0,
          data: historyPoints,
          tension: 0.1,
        },
        // 80% Band (Outer)
        {
          label: '80% Upper',
          data: [connect(lastHistoryPoint?.y), ...forecastData.map(p => ({ x: p.x, y: p.p90 }))],
          borderColor: 'transparent',
          pointRadius: 0,
          fill: false,
          tension: 0.3,
        },
        {
          label: '80% Prediction',
          data: [connect(lastHistoryPoint?.y, lastHistoryPoint?.y), ...forecastData.map(p => ({ x: p.x, y: p.p10, upper: p.p90 }))],
          borderColor: 'transparent',
          backgroundColor: 'rgba(187, 222, 251, 0.2)', // Light Blue
          fill: '-1',
          pointRadius: 0,
          tension: 0.3,
        },
        // 60% Band (Middle)
        {
          label: '60% Upper',
          data: [connect(lastHistoryPoint?.y), ...forecastData.map(p => ({ x: p.x, y: p.p80 }))],
          borderColor: 'transparent',
          pointRadius: 0,
          fill: false,
          tension: 0.3,
        },
        {
          label: '60% Prediction',
          data: [connect(lastHistoryPoint?.y, lastHistoryPoint?.y), ...forecastData.map(p => ({ x: p.x, y: p.p20, upper: p.p80 }))],
          borderColor: 'transparent',
          backgroundColor: 'rgba(100, 181, 246, 0.4)', // Medium Blue
          fill: '-1',
          pointRadius: 0,
          tension: 0.3,
        },
        // 30% Band (Inner)
        {
          label: '30% Upper',
          data: [connect(lastHistoryPoint?.y), ...forecastData.map(p => ({ x: p.x, y: p.p65 }))],
          borderColor: 'transparent',
          pointRadius: 0,
          fill: false,
          tension: 0.3,
        },
        {
          label: '30% Prediction',
          data: [connect(lastHistoryPoint?.y, lastHistoryPoint?.y), ...forecastData.map(p => ({ x: p.x, y: p.p35, upper: p.p65 }))],
          borderColor: 'transparent',
          backgroundColor: 'rgba(25, 118, 210, 0.6)', // Dark Blue
          fill: '-1',
          pointRadius: 0,
          tension: 0.3,
        },
        // Median Line
        {
          label: 'Median Forecast',
          borderColor: '#0D47A1',
          borderWidth: 3,
          data: [connect(lastHistoryPoint?.y), ...forecastData.map(p => ({ x: p.x, y: p.median }))],
          pointRadius: 3,
          fill: false,
          tension: 0.3,
        },
      ]

      return {
        datasets: datasets.map(ds => ({ ...ds, parsing: false, normalized: true })),
      }
    } else {
      // Standard View
      const forecastPoints = store.forecastResults.map((row: any) => ({
        x: parseDate(row.date || row.year || row[timeCol]),
        median: row.median_forecast ?? row.mean ?? row[targetCol],
        lower: row.lower,
        upper: row.upper,
      }))

      const connect = (y: number, upper?: number) => ({ x: lastHistoryPoint?.x, y, upper })

      const datasets: any[] = [
        {
          label: 'Historical',
          borderColor: '#9E9E9E',
          borderWidth: 2,
          pointRadius: 0,
          data: historyPoints,
          tension: 0.1,
        },
      ]

      if (hasIntervals.value) {
        datasets.push(
          {
            label: 'Forecast Upper',
            borderColor: 'transparent',
            pointRadius: 0,
            data: [connect(lastHistoryPoint?.y), ...forecastPoints.map(p => ({ x: p.x, y: p.upper }))],
            fill: false,
            tension: 0.3,
          },
          {
            label: 'Prediction Range',
            borderColor: 'transparent',
            backgroundColor: 'rgba(24, 103, 192, 0.1)',
            fill: '-1',
            pointRadius: 0,
            data: [connect(lastHistoryPoint?.y, lastHistoryPoint?.y), ...forecastPoints.map(p => ({ x: p.x, y: p.lower, upper: p.upper }))],
            tension: 0.3,
          },
        )
      }

      datasets.push({
        label: 'Forecast',
        borderColor: primaryLineColor.value,
        borderWidth: 3,
        pointRadius: 3,
        data: [connect(lastHistoryPoint?.y), ...forecastPoints.map(p => ({ x: p.x, y: p.median }))],
        fill: false,
        tension: 0.3,
      })

      return { datasets: datasets.map(ds => ({ ...ds, parsing: false, normalized: true })) }
    }
  })

  function resetZoom () {
    const chart = ChartJS.getChart('forecast-chart')
    if (chart) {
      chart.resetZoom()
      isZoomed.value = false
      rangeMin.value = null
      rangeMax.value = null
    }
  }

  function exportImage () {
    const chart = ChartJS.getChart('forecast-chart')
    if (chart && chart.canvas) {
      const url = (chart.canvas as HTMLCanvasElement).toDataURL('image/png')
      const link = document.createElement('a')
      link.download = `forecast_export_${new Date().toISOString().split('T')[0]}.png`
      link.href = url
      link.click()
      appStore.notify('Chart image saved', 'success')
    } else {
      appStore.notify('Could not export chart image', 'error')
    }
  }

  async function copyImage () {
    const chart = ChartJS.getChart('forecast-chart')
    if (!chart || !chart.canvas) {
      appStore.notify('Could not copy chart image', 'error')
      return
    }
    const canvas = chart.canvas as HTMLCanvasElement
    try {
      // Try modern Clipboard API first
      if (typeof ClipboardItem !== 'undefined') {
        const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
        if (!blob) throw new Error('No blob')
        await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })])
        appStore.notify('Chart image copied to clipboard', 'success')
        return
      }
      // Fallback: copy data URL as text
      const dataUrl = canvas.toDataURL('image/png')
      await navigator.clipboard.writeText(dataUrl)
      appStore.notify('Chart image URL copied to clipboard', 'success')
    } catch {
      appStore.notify('Failed to copy chart image', 'error')
    }
  }

  const suggestedUnit = computed(() => {
    const minUnit = (store.ontology?.problem.granularity.unit as any) || 'day'
    if (store.forecastResults.length === 0 && store.historyResults.length === 0) return minUnit

    const historyTimes = store.historyResults.map((r: any) => parseDate(r[store.timeCol]))
    const forecastTimes = store.forecastResults.map((r: any) => parseDate(r.date || r.year || r[store.timeCol]))
    const allTimes = [...historyTimes, ...forecastTimes].filter(t => !Number.isNaN(t))

    if (allTimes.length < 2) return minUnit
    const rangeMs = Math.max(...allTimes) - Math.min(...allTimes)
    const yearMs = 365 * 24 * 60 * 60 * 1000

    if (rangeMs > 5 * yearMs && ['minute', 'second'].includes(minUnit)) return 'month'
    if (rangeMs > yearMs && ['minute', 'second'].includes(minUnit)) return 'day'
    if (rangeMs > 50 * yearMs) return 'year'

    return minUnit
  })

  const chartOptions = computed<any>(() => ({
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        bottom: 10,
        left: 5,
        right: 15,
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'nearest' as const,
        axis: 'x' as const,
        intersect: false,
        callbacks: {
          label: (context: any) => {
            const dataset = context.dataset
            if (dataset.label?.includes('Upper')) return null // Hide helper datasets

            let label = dataset.label || ''
            if (label) label += ': '

            const raw = dataset.data[context.dataIndex]
            const y = context.parsed.y
            if (y === null) return label

            // Show range if upper bound is present in data point
            if (raw && typeof raw === 'object' && raw.upper !== undefined) {
              return `${label}${formatNumber(y)} - ${formatNumber(raw.upper)}`
            }
            return `${label}${formatNumber(y)}`
          },
        },
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
          wheel: { enabled: true, speed: 0.1 },
          pinch: { enabled: true },
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
      decimation: {
        enabled: true,
        algorithm: 'lttb' as const,
        samples: 500, // Reduced from thousands to 500 points for clear trajectory
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        min: rangeMin.value ?? undefined,
        max: rangeMax.value ?? undefined,
        time: {
          unit: suggestedUnit.value,
          displayFormats: {
            day: 'MMM d',
            month: 'MMM yyyy',
            year: 'yyyy',
          },
          tooltipFormat: 'PP',
        },
        grid: { display: false },
        ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 8 },
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
  }))

  // Zoom state is tracked via isZoomed and managed by the main chart's wheel/pinch zoom
</script>
