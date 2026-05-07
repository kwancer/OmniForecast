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
          Forecast Skill Score
        </div>
        <div class="d-flex align-center">
          <span class="text-h3 font-weight-bold" :class="textColorClass">
            {{ dataHealthReport?.score ?? 'N/A' }}
          </span>
          <span class="text-h6 text-medium-emphasis ml-1">/100</span>
          <v-chip
            class="ml-3"
            :color="chipColor"
            size="small"
            variant="flat"
          >
            {{ dataHealthReport.rating }}
          </v-chip>
        </div>
      </div>

      <!-- Circular Gauge & Toggle -->
      <div class="d-flex flex-column align-center">
        <svg height="80" viewBox="0 0 80 80" width="80">
          <!-- Background Circle -->
          <circle
            cx="40"
            cy="40"
            fill="none"
            r="32"
            stroke="#e0e0e0"
            stroke-width="8"
          />
          <!-- Progress Circle -->
          <circle
            cx="40"
            cy="40"
            fill="none"
            r="32"
            :stroke="gaugeColor"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="progressOffset"
            stroke-linecap="round"
            stroke-width="8"
            transform="rotate(-90 40 40)"
          />
          <!-- Center Text -->
          <text
            class="gauge-text"
            :fill="gaugeColor"
            text-anchor="middle"
            x="40"
            y="45"
          >
            {{ dataHealthReport.score }}
          </text>
        </svg>

        <!-- Expand/Collapse Button -->
        <v-btn
          size="x-small"
          variant="text"
          @click="showDetails = !showDetails"
        >
          {{ showDetails ? 'Hide' : 'Details' }}
          <v-icon
            end
            :icon="showDetails ? 'mdi-chevron-up' : 'mdi-chevron-down'"
            size="small"
          />
        </v-btn>
      </div>
    </div>

    <!-- Collapsible Details Section -->
    <v-expand-transition>
      <div v-show="showDetails">
        <v-divider class="mb-3" />

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
            This score measures how much predictable structure exists in your data compared to a baseline. A score of 0 indicates the data is functionally random or highly chaotic to standard models, resulting in a baseline forecast.
          </div>
        </v-alert>

        <!-- Dual Metrics Display -->
        <div class="mt-3">
          <!-- MSE Comparison: Naive Baseline vs. Winner -->
          <!-- MSE is used (not RMSE) because FSS = 1 - MSE_winner/MSE_naive -->
          <!-- which is algebraically identical to out-of-sample R². -->
          <div
            v-if="dataHealthReport.mse_naive !== undefined && dataHealthReport.mse_winner !== undefined"
            class="mt-3"
          >
            <div class="d-flex align-center gap-1 mb-2">
              <span class="text-caption text-medium-emphasis">Out-of-Sample MSE Comparison</span>
              <v-tooltip location="top" max-width="320">
                <template #activator="{ props: tip }">
                  <v-icon v-bind="tip" class="text-medium-emphasis" size="14">mdi-information-outline</v-icon>
                </template>
                <span>
                  MSE (Mean Squared Error) is used here — not RMSE — because the FSS formula
                  <strong>FSS = 1 - MSE_winner / MSE_naive</strong> is algebraically identical
                  to the out-of-sample R² statistic. Squaring errors before dividing ensures
                  the ratio is scale-invariant and mathematically consistent with R².
                </span>
              </v-tooltip>
            </div>
            <div class="d-flex gap-3">
              <v-card class="flex-1 pa-3" color="surface" variant="outlined">
                <div class="text-caption text-medium-emphasis">Naive Baseline MSE</div>
                <div class="text-h6 font-weight-bold font-mono text-error">
                  {{ formatMse(dataHealthReport.mse_naive) }}
                </div>
                <div class="text-caption text-medium-emphasis mt-1">Flat-line forecast</div>
              </v-card>
              <v-card class="flex-1 pa-3" color="surface" variant="outlined">
                <div class="text-caption text-medium-emphasis">Winner MSE</div>
                <div class="text-h6 font-weight-bold font-mono text-success">
                  {{ formatMse(dataHealthReport.mse_winner) }}
                </div>
                <div class="text-caption text-medium-emphasis mt-1">{{ dataHealthReport.winner_name }}</div>
              </v-card>
            </div>
            <v-progress-linear
              class="mt-3"
              color="primary"
              height="6"
              :model-value="dataHealthReport.score"
              rounded
            />
            <div class="text-caption text-medium-emphasis mt-1">
              FSS: {{ dataHealthReport.score }}/100 — equivalent to R² = {{ formatNumber(dataHealthReport.score / 100, { decimals: 2 }) }}
              (MSE reduced from {{ formatNumber(dataHealthReport.mse_naive) }} → {{ formatNumber(dataHealthReport.mse_winner) }})
            </div>
          </div>
        </div>
      </div>
    </v-expand-transition>
  </v-card>
</template>

<script setup lang="ts">
  import type { DataHealthReport } from '@/types'
  import { computed, ref } from 'vue'
  import { formatNumber } from '@/utils/formatters'

  const props = defineProps<{
    dataHealthReport: DataHealthReport | null
  }>()

  const showDetails = ref(false)

  function formatMse (val: number | undefined | null) {
    return formatNumber(val)
  }

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
