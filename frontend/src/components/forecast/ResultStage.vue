<template>
  <v-container class="fill-height d-flex flex-column pa-2 pa-md-4">
    <div class="d-flex align-center mb-4">
      <v-btn icon="mdi-arrow-left" variant="text" @click="store.setStep('plan')" />
      <h2 class="text-h5 font-header ml-2">Analytic Output</h2>
    </div>

    <v-row class="flex-grow-1 overflow-y-auto">

      <v-col class="d-flex flex-column gap-4" cols="12" md="8">

        <!-- Data Health Card -->
        <DataHealthCard :data-health-report="store.dataHealthReport" />

        <div style="height: 450px; width: 100%;">
          <ForecastChart />
        </div>

        <v-expansion-panels class="mt-4">
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon color="primary" size="small" start>mdi-table</v-icon>
              View Raw Forecast Data
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-table density="compact" fixed-header height="300px">
                <thead>
                  <tr>
                    <th class="text-left">Date</th>
                    <th class="text-right">Predicted Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in store.forecastResults" :key="i">
                    <td class="font-mono">{{ formatDate(row[store.timeCol]!) }}</td>
                    <td class="font-mono text-right font-weight-bold text-primary">
                      {{ formatValue(row[store.targetCol]) }}
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

      </v-col>

      <v-col cols="12" md="4">

        <v-card class="pa-4 mb-4 bg-surface" variant="outlined">
          <div class="d-flex align-center mb-2">
            <div class="text-overline">Reliability Metrics</div>
          </div>
          <v-row dense>
            <v-col v-for="metric in store.metrics" :key="metric.name" cols="4">
              <div class="text-caption text-medium-emphasis text-truncate">{{ getMetricLabel(metric.name) }}</div>
              <div class="text-subtitle-2 font-weight-bold font-mono">{{ metric.value.toFixed(2) }}</div>
            </v-col>
          </v-row>
        </v-card>

        <v-card class="pa-4 mb-4" color="secondary" variant="tonal">
          <div class="d-flex align-center mb-2">
            <v-icon class="mr-2" icon="mdi-shield-check-outline" />
            <span class="font-weight-bold">Executive Summary</span>
          </div>
          <p class="text-body-2" style="white-space: pre-line;">{{ store.explanation }}</p>
        </v-card>

        <v-card v-if="store.modelMetadata" class="pa-4 mb-4" color="accent" variant="tonal">
          <div class="d-flex align-center mb-2">
            <v-icon class="mr-2" icon="mdi-brain" />
            <span class="font-weight-bold">Selected Model: {{ store.modelMetadata.name }}</span>
          </div>
          <p class="text-body-2 mb-2">{{ store.modelMetadata.description }}</p>
          <p class="text-body-2 text-medium-emphasis font-italic mb-2">Why? {{ store.modelMetadata.rationale }}</p>
          <v-btn
            v-if="store.modelMetadata.educational_video_url"
            color="primary"
            :href="store.modelMetadata.educational_video_url"
            prepend-icon="mdi-youtube"
            size="small"
            target="_blank"
            variant="outlined"
          >
            Learn More
          </v-btn>
        </v-card>

        <v-btn block class="mb-4" prepend-icon="mdi-download" variant="outlined">Export JSON</v-btn>

        <v-divider class="mb-4" />

        <v-btn
          block
          color="primary"
          elevation="2"
          size="x-large"
          @click="store.reset()"
        >
          New Forecast
          <v-icon end>mdi-refresh</v-icon>
        </v-btn>
      </v-col>

    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { useForecastStore } from '@/stores/forecast'
  import DataHealthCard from './DataHealthCard.vue'
  import ForecastChart from './ForecastChart.vue' // <--- IMPORT THE CHART HERE

  const store = useForecastStore()

  const formatDate = (val: string | number) => new Date(val).toLocaleDateString()

  function formatValue (val: any) {
    if (typeof val === 'number') return val.toFixed(2)
    return val
  }

  function getMetricLabel (name: string) {
    switch (name) {
      case 'MAE': { return 'Avg Error'
      }
      case 'RMSE': { return 'Precision'
      }
      case 'MAPE': { return 'Error %'
      }
      default: { return name
      }
    }
  }
</script>

<style scoped>
.gap-4 {
  gap: 16px;
}
.font-mono {
  font-family: 'Roboto Mono', monospace;
}
</style>
