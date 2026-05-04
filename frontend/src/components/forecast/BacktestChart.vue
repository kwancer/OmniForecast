<template>
  <v-card class="pa-4" variant="outlined">
    <div class="d-flex align-center mb-4">
      <v-icon class="mr-2" color="success">mdi-history</v-icon>
      <div class="text-subtitle-1 font-weight-bold">Model Backtest (Winning Model)</div>
      <v-tooltip location="top">
        <template #activator="{ props: tooltipProps }">
          <v-icon v-bind="tooltipProps" class="ml-2" color="grey" size="small">mdi-help-circle-outline</v-icon>
        </template>
        This chart shows how the selected model performed on the most recent 20% of your historical data, which it had never seen before.
      </v-tooltip>
    </div>

    <div style="height: 300px;">
      <Line :data="chartData" :options="chartOptions" />
    </div>

    <div class="d-flex justify-center gap-6 mt-4 text-caption">
      <div class="d-flex align-center">
        <v-sheet class="mr-2" color="grey" height="2" width="12" />
        <span>Actual Observations</span>
      </div>
      <div class="d-flex align-center">
        <v-sheet
          class="mr-2"
          color="primary"
          height="2"
          style="border-top: 2px dashed"
          width="12"
        />
        <span>Model "Blind" Prediction</span>
      </div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
  import type { BacktestPoint } from '@/types'
  import {
    Chart as ChartJS,
    Decimation,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    TimeScale,
    Title,
    Tooltip,
  } from 'chart.js'
  import { computed } from 'vue'
  import { Line } from 'vue-chartjs'
  import 'chartjs-adapter-date-fns'

  ChartJS.register(
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    TimeScale,
    Decimation,
  )

  const props = defineProps<{
    data: BacktestPoint[]
  }>()

  const chartData = computed(() => ({
    datasets: [
      {
        label: 'Actual',
        borderColor: '#9E9E9E',
        backgroundColor: '#9E9E9E',
        borderWidth: 2,
        pointRadius: 3,
        data: props.data.map(p => ({ x: new Date(p.date).getTime(), y: p.actual })),
        tension: 0.1,
        parsing: false as const,
        normalized: true,
      },
      {
        label: 'Prediction',
        borderColor: '#1867C0',
        backgroundColor: '#1867C0',
        borderWidth: 2,
        borderDash: [5, 5],
        pointRadius: 3,
        data: props.data.map(p => ({ x: new Date(p.date).getTime(), y: p.prediction })),
        tension: 0.1,
        parsing: false as const,
        normalized: true,
      },
    ],
  }))

  const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
      decimation: {
        enabled: true,
        algorithm: 'lttb' as const,
        samples: 200,
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'day' as any,
          displayFormats: {
            day: 'MMM d',
          },
        },
        grid: { display: false },
      },
      y: {
        beginAtZero: false,
        grid: { color: '#f0f0f0' },
      },
    },
  }))
</script>
