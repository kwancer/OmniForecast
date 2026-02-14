<template>
  <v-card
    v-if="dataHealthReport"
    class="mb-4 pa-4"
    :class="borderColorClass"
    variant="outlined"
  >
    <div class="d-flex align-center justify-space-between mb-3">
      <div class="flex-grow-1">
        <div class="text-overline text-medium-emphasis mb-1">
          Data Predictability
        </div>
        <div class="d-flex align-center">
          <span class="text-h3 font-weight-bold" :class="textColorClass">
            {{ dataHealthReport.score }}
          </span>
          <span class="text-h6 text-medium-emphasis ml-1">/100</span>
          <v-chip
            :color="chipColor"
            class="ml-3"
            size="small"
            variant="flat"
          >
            {{ dataHealthReport.rating }}
          </v-chip>
        </div>
      </div>

      <!-- Circular Gauge -->
      <div class="gauge-container">
        <svg width="80" height="80" viewBox="0 0 80 80">
          <!-- Background Circle -->
          <circle
            cx="40"
            cy="40"
            r="32"
            fill="none"
            stroke="#e0e0e0"
            stroke-width="8"
          />
          <!-- Progress Circle -->
          <circle
            cx="40"
            cy="40"
            r="32"
            fill="none"
            :stroke="gaugeColor"
            stroke-width="8"
            stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="progressOffset"
            transform="rotate(-90 40 40)"
          />
          <!-- Center Text -->
          <text
            x="40"
            y="45"
            text-anchor="middle"
            class="gauge-text"
            :fill="gaugeColor"
          >
            {{ dataHealthReport.score }}
          </text>
        </svg>
      </div>
    </div>

    <p class="text-body-2 text-medium-emphasis mb-0">
      {{ dataHealthReport.explanation }}
    </p>

    <!-- Low Score Warning -->
    <v-alert
      v-if="dataHealthReport.score <= 30"
      class="mt-3"
      color="warning"
      density="compact"
      icon="mdi-alert-circle"
      variant="tonal"
    >
      <div class="text-body-2">
        <strong>⚠️ Why is the forecast conservative?</strong>
        <br>
        Your data is highly random, so a flat or simple forecast is statistically the most accurate prediction.
      </div>
    </v-alert>

    <!-- Strength Details (Optional) -->
    <div
      v-if="dataHealthReport.strengths"
      class="mt-3 d-flex gap-3"
    >
      <div class="flex-1">
        <div class="text-caption text-medium-emphasis">Trend Strength</div>
        <v-progress-linear
          :model-value="dataHealthReport.strengths.trend * 100"
          color="primary"
          height="6"
          rounded
        />
      </div>
      <div class="flex-1">
        <div class="text-caption text-medium-emphasis">Seasonality Strength</div>
        <v-progress-linear
          :model-value="dataHealthReport.strengths.seasonality * 100"
          color="secondary"
          height="6"
          rounded
        />
      </div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
  import type { DataHealthReport } from '@/types'
  import { computed } from 'vue'

  const props = defineProps<{
    dataHealthReport: DataHealthReport | null
  }>()

  const borderColorClass = computed(() => {
    if (!props.dataHealthReport) return ''
    const score = props.dataHealthReport.score
    if (score >= 70) return 'border-s-4 border-success'
    if (score <= 30) return 'border-s-4 border-error'
    return 'border-s-4 border-warning'
  })

  const textColorClass = computed(() => {
    if (!props.dataHealthReport) return ''
    const score = props.dataHealthReport.score
    if (score >= 70) return 'text-success'
    if (score <= 30) return 'text-error'
    return 'text-warning'
  })

  const chipColor = computed(() => {
    if (!props.dataHealthReport) return 'grey'
    const score = props.dataHealthReport.score
    if (score >= 70) return 'success'
    if (score <= 30) return 'error'
    return 'warning'
  })

  const gaugeColor = computed(() => {
    if (!props.dataHealthReport) return '#9E9E9E'
    const score = props.dataHealthReport.score
    if (score >= 70) return '#4CAF50' // Success green
    if (score <= 30) return '#F44336' // Error red
    return '#FF9800' // Warning orange
  })

  // SVG Circle calculations
  const circumference = 2 * Math.PI * 32 // radius = 32

  const progressOffset = computed(() => {
    if (!props.dataHealthReport) return circumference
    const score = props.dataHealthReport.score
    const progress = score / 100
    return circumference * (1 - progress)
  })
</script>

<style scoped>
  .gauge-container {
    flex-shrink: 0;
  }

  .gauge-text {
    font-size: 18px;
    font-weight: bold;
    font-family: 'Roboto', sans-serif;
  }

  .gap-3 {
    gap: 12px;
  }

  .flex-1 {
    flex: 1;
  }

  .border-s-4 {
    border-left-width: 4px !important;
    border-left-style: solid !important;
  }

  .border-success {
    border-left-color: rgb(var(--v-theme-success)) !important;
  }

  .border-error {
    border-left-color: rgb(var(--v-theme-error)) !important;
  }

  .border-warning {
    border-left-color: rgb(var(--v-theme-warning)) !important;
  }
</style>
