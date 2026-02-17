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
              <v-table density="compact" fixed-header height="350px">
                <thead>
                  <tr>
                    <th class="text-left">Date</th>
                    <th class="text-right">Lower (80%)</th>
                    <th class="text-right">Median</th>
                    <th class="text-right">Upper (80%)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in store.forecastResults" :key="i">
                    <td class="font-mono">{{ formatDate(row.date || row.year || row[store.timeCol]) }}</td>
                    <td class="font-mono text-right text-medium-emphasis">
                      {{ formatValue(row.conf_80_lower ?? row.lower) }}
                    </td>
                    <td class="font-mono text-right font-weight-bold text-primary">
                      {{ formatValue(row.median_forecast ?? row.mean ?? row[store.targetCol]) }}
                    </td>
                    <td class="font-mono text-right text-medium-emphasis">
                      {{ formatValue(row.conf_80_upper ?? row.upper) }}
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
            <v-col v-for="metric in displayMetrics" :key="metric.name" cols="6">
              <div class="text-caption text-medium-emphasis text-truncate">{{ getMetricLabel(metric.name) }}</div>
              <div class="text-subtitle-2 font-weight-bold font-mono">{{ formatMetricValue(metric) }}</div>
            </v-col>
          </v-row>
        </v-card>

        <v-card class="pa-4 mb-4" color="secondary" variant="tonal">
          <div class="d-flex align-center mb-2">
            <v-icon class="mr-2" icon="mdi-shield-check-outline" />
            <span class="font-weight-bold">Executive Summary</span>
          </div>
          <p class="text-body-2" style="white-space: pre-line;">{{ formattedExplanation }}</p>
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
  import { computed } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import DataHealthCard from './DataHealthCard.vue'
  import ForecastChart from './ForecastChart.vue' // <--- IMPORT THE CHART HERE

  const store = useForecastStore()

  // Format numbers in the explanation string
  const formattedExplanation = computed(() => {
    if (!store.explanation) return ''
    // Regex to find floats or integers (including those with decimals)
    // Avoid small indices like "10 periods" by checking length or context if needed,
    // but typically toLocaleString is fine for all numbers > 999.
    return store.explanation.replace(/\b\d+(\.\d+)?\b/g, match => {
      const num = Number.parseFloat(match)
      // Only format large numbers or those with many digits to avoid mangling small integers like "10"
      if (!Number.isNaN(num) && (num >= 1000 || match.includes('.'))) {
        return num.toLocaleString(undefined, {
          minimumFractionDigits: match.includes('.') ? 2 : 0,
          maximumFractionDigits: 2,
        })
      }
      return match
    })
  })

  function formatDate (val: any) {
    if (val === undefined || val === null) return 'N/A'
    // Handle numeric years (e.g., 1990)
    if (typeof val === 'number' && val > 1700 && val < 2500) {
      return val.toString()
    }
    const date = new Date(val)
    if (Number.isNaN(date.getTime())) return 'Invalid Date'

    // If granularity is year, just show the year
    if (store.ontology?.problem.granularity.unit === 'year') {
      return date.getFullYear().toString()
    }

    return date.toLocaleDateString()
  }

  function formatValue (val: any) {
    if (typeof val === 'number') {
      return val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
    return val
  }

  // Filter out RMSE and R² from display
  const displayMetrics = computed(() => {
    return store.metrics.filter(m => m.name !== 'RMSE' && m.name !== 'R²')
  })

  function getMetricLabel (name: string) {
    switch (name) {
      case 'MAE': { return 'Typical Error'
      }
      case 'MAPE': { return 'Error %'
      }
      case 'R²': { return 'Accuracy Score'
      }
      default: { return name
      }
    }
  }

  function formatMetricValue (metric: any) {
    const val = typeof metric.value === 'number' ? metric.value : 0
    if (metric.name === 'MAE') {
      return `±${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
    if (metric.name === 'MAPE') {
      return `${val.toFixed(1)}%`
    }
    if (metric.name === 'R²') {
      return `${(val * 100).toFixed(0)}%`
    }
    return val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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
