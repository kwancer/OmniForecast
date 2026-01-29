<template>
  <v-container class="fill-height d-flex flex-column">
    <div class="d-flex align-center mb-4">
      <h2 class="text-h5 font-header ml-2">Forecast Output</h2>
    </div>

    <v-row class="flex-grow-1 overflow-y-auto">
      <v-col cols="12" md="8">
        <v-card class="h-100 pa-4 d-flex flex-column" variant="outlined">
          <div class="d-flex justify-space-between align-center mb-4">
            <div class="text-overline text-primary">PROJECTED TRAJECTORY</div>
            <v-chip color="primary" size="small" variant="outlined">CONFIDENCE: HIGH</v-chip>
          </div>

          <v-sheet class="flex-grow-1 d-flex align-center justify-center border-thin rounded overflow-y-auto" color="transparent">
            <v-table class="w-100 bg-transparent" density="compact">
              <thead>
                <tr>
                  <th class="text-left font-mono">Time</th>
                  <th class="text-right font-mono text-primary">Forecasted Value</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, i) in store.forecastResults" :key="i">
                  <td class="font-mono">{{ formatDate(item[store.timeCol]) }}</td>
                  <td class="font-mono text-right text-primary font-weight-bold">{{ formatValue(item[store.targetCol]) }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-sheet>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card class="pa-4 mb-4 bg-surface" variant="outlined">
          <div class="d-flex align-center mb-2">
            <div class="text-overline">Reliability Metrics</div>
            <v-tooltip location="top">
              <template #activator="{ props }">
                <v-icon v-bind="props" class="ml-2" color="medium-emphasis" size="small">mdi-information-outline</v-icon>
              </template>
              <span>Validation testing ensures the model is accurate by testing against known historical data.</span>
            </v-tooltip>
          </div>
          <v-row dense>
            <v-col v-for="metric in store.metrics" :key="metric.name" cols="4">
              <div class="text-caption text-medium-emphasis text-truncate">{{ getMetricLabel(metric.name) }}</div>
              <div class="text-subtitle-2 font-weight-bold font-mono">{{ metric.value.toFixed(2) }}{{ metric.name === 'MAPE' ? '%' : '' }}</div>
            </v-col>
          </v-row>
        </v-card>

        <v-card class="pa-4 mb-4" color="secondary" variant="tonal">
          <div class="d-flex align-center mb-2">
            <v-icon class="mr-2" icon="mdi-shield-check-outline" />
            <span class="font-weight-bold">Executive Summary</span>
          </div>
          <p class="text-body-2">{{ store.explanation }}</p>
        </v-card>

        <v-btn block class="mb-2" prepend-icon="mdi-download" variant="outlined">Export JSON</v-btn>
        <v-btn block class="mb-4" prepend-icon="mdi-file-chart" variant="outlined">Export Formal Report</v-btn>

        <v-divider class="mb-4" />

        <v-btn
          block
          color="primary"
          elevation="2"
          size="x-large"
          @click="store.reset()"
        >
          New Forecast Journey
          <v-icon end>mdi-refresh</v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { useForecastStore } from '@/stores/forecast'

  const store = useForecastStore()

  function formatDate (val: string | number | undefined) {
    if (!val) return ''
    return new Date(val).toLocaleDateString()
  }

  function formatValue (val: string | number | undefined) {
    if (val === undefined) return ''
    if (typeof val !== 'number') return val
    return val.toFixed(2)
  }

  function getMetricLabel (name: string) {
    switch (name) {
      case 'MAE': { return 'Average Error'
      }
      case 'RMSE': { return 'Precision'
      }
      case 'MAPE': { return 'Variation'
      }
      default: { return name
      }
    }
  }
</script>
