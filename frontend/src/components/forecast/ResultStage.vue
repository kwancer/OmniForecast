<template>
  <v-container class="fill-height d-flex flex-column pa-0" fluid>
    <div class="d-flex align-center px-4 py-4 w-100 bg-surface border-b">
      <v-btn
        class="hover-lift"
        icon="mdi-arrow-left"
        size="small"
        variant="tonal"
        @click="store.setStep('plan')"
      />
      <div class="ml-4">
        <h2 class="text-h6 font-weight-bold font-header mb-0">Analytic Output</h2>
      </div>
      <v-spacer />

      <div class="text-caption text-medium-emphasis mr-4 text-right hidden-sm-and-down">
        Review final model results
      </div>

      <v-btn
        class="ml-2 hover-lift font-weight-bold"
        color="primary"
        elevation="0"
        variant="flat"
        @click="store.reset()"
      >
        New Forecast
        <v-icon end>mdi-refresh</v-icon>
      </v-btn>
    </div>

    <v-row class="flex-grow-1 ma-0 w-100 bg-background overflow-hidden">
      <v-col class="h-100 overflow-y-auto pa-6 d-flex justify-center" cols="12">
        <div style="max-width: 1200px; width: 100%;">
          <v-row>

            <!-- ═══ LEFT: Charts & Data ═══ -->
            <v-col class="d-flex flex-column" cols="12" md="8" style="gap: 20px;">

              <!-- Data Health Card -->
              <DataHealthCard :data-health-report="store.dataHealthReport" />

              <!-- Forecast Chart -->
              <div class="chart-container" style="height: 450px; width: 100%;">
                <ForecastChart />
              </div>

              <!-- Expandable Panels -->
              <v-expansion-panels class="styled-panels" variant="accordion">
                <!-- Tournament Analysis -->
                <v-expansion-panel v-if="store.tournamentResults.length > 0" rounded="lg">
                  <v-expansion-panel-title class="font-weight-bold">
                    <div class="d-flex align-center">
                      <div class="panel-icon panel-icon--success mr-3">
                        <v-icon color="white" size="16">mdi-comment-text-outline</v-icon>
                      </div>
                      Reasoning & Model Tournament
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <div class="d-flex flex-column pa-2" style="gap: 24px;">
                      <BacktestChart v-if="store.backtestData.length > 0" :data="store.backtestData" />
                      <ModelTournament :results="store.tournamentResults" />
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Raw Data -->
                <v-expansion-panel rounded="lg">
                  <v-expansion-panel-title class="font-weight-bold">
                    <div class="d-flex align-center">
                      <div class="panel-icon panel-icon--primary mr-3">
                        <v-icon color="white" size="16">mdi-table</v-icon>
                      </div>
                      View Raw Forecast Data
                    </div>
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

            <!-- ═══ RIGHT: Sidebar Insights ═══ -->
            <v-col cols="12" md="4">

              <!-- Reliability Metrics -->
              <div class="insight-card mb-5">
                <div class="insight-card__header">
                  <div class="panel-icon panel-icon--primary mr-3">
                    <v-icon color="white" size="16">mdi-chart-bar</v-icon>
                  </div>
                  <span class="text-overline font-weight-bold">Reliability Metrics</span>
                </div>
                <v-row class="mt-3" dense>
                  <v-col v-for="metric in displayMetrics" :key="metric.name" cols="6">
                    <div class="metric-tile">
                      <div class="metric-tile__value">{{ formatMetricValue(metric) }}</div>
                      <div class="metric-tile__label">{{ getMetricLabel(metric.name) }}</div>
                    </div>
                  </v-col>
                </v-row>
              </div>

              <!-- Executive Summary -->
              <div class="insight-card insight-card--secondary mb-5">
                <div class="insight-card__header">
                  <div class="panel-icon panel-icon--secondary mr-3">
                    <v-icon color="white" size="16">mdi-shield-check-outline</v-icon>
                  </div>
                  <span class="font-weight-bold">Executive Summary</span>
                </div>
                <p class="text-body-2 mt-3 mb-0" style="white-space: pre-line; line-height: 1.6;">{{ formattedExplanation }}</p>
              </div>

              <!-- Selected Model -->
              <div v-if="store.modelMetadata" class="insight-card insight-card--violet mb-5">
                <div class="insight-card__header">
                  <div class="panel-icon panel-icon--primary mr-3">
                    <v-icon color="white" size="16">mdi-brain</v-icon>
                  </div>
                  <span class="font-weight-bold">Selected Model</span>
                  <v-chip class="ml-2" color="primary" size="x-small" variant="flat">{{ store.modelMetadata.name }}</v-chip>
                </div>
                <p class="text-body-2 mt-3 mb-2">{{ store.modelMetadata.description }}</p>
                <p class="text-body-2 text-medium-emphasis font-italic mb-3">Why? {{ store.modelMetadata.rationale }}</p>
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
              </div>

            </v-col></v-row>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import BacktestChart from './BacktestChart.vue'
  import DataHealthCard from './DataHealthCard.vue'
  import ForecastChart from './ForecastChart.vue'
  import ModelTournament from './ModelTournament.vue'

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
.font-mono {
  font-family: 'JetBrains Mono', 'Roboto Mono', monospace;
}

/* ─── Chart Container ─── */
.chart-container {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-theme-primary), 0.08);
  background: rgb(var(--v-theme-surface));
}

/* ─── Panel Icon Badges ─── */
.panel-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  flex-shrink: 0;
}

.panel-icon--primary {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)), rgba(var(--v-theme-primary), 0.7));
}

.panel-icon--secondary {
  background: linear-gradient(135deg, rgb(var(--v-theme-secondary)), rgba(var(--v-theme-secondary), 0.7));
}

.panel-icon--success {
  background: linear-gradient(135deg, rgb(var(--v-theme-success)), rgba(var(--v-theme-success), 0.7));
}

/* ─── Expansion Panels ─── */
.styled-panels {
  gap: 8px;
}

.styled-panels :deep(.v-expansion-panel) {
  border: 1px solid rgba(var(--v-theme-primary), 0.08) !important;
  border-radius: 12px !important;
  margin-bottom: 8px;
}

.styled-panels :deep(.v-expansion-panel::before) {
  box-shadow: none !important;
}

.styled-panels :deep(.v-expansion-panel-title) {
  font-size: 0.9rem;
}

/* ─── Insight Cards (sidebar) ─── */
.insight-card {
  background: rgba(var(--v-theme-primary), 0.03);
  border: 1px solid rgba(var(--v-theme-primary), 0.08);
  border-radius: 16px;
  padding: 20px;
  transition: border-color 0.3s ease;
}

.insight-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.15);
}

.insight-card--secondary {
  background: rgba(var(--v-theme-secondary), 0.04);
  border-color: rgba(var(--v-theme-secondary), 0.1);
}

.insight-card--secondary:hover {
  border-color: rgba(var(--v-theme-secondary), 0.2);
}

.insight-card--violet {
  background: rgba(var(--v-theme-primary), 0.04);
  border-color: rgba(var(--v-theme-primary), 0.1);
}

.insight-card__header {
  display: flex;
  align-items: center;
}

/* ─── Metric Tiles ─── */
.metric-tile {
  padding: 12px;
  border-radius: 10px;
  background: rgba(var(--v-theme-primary), 0.04);
  border: 1px solid rgba(var(--v-theme-primary), 0.06);
  text-align: center;
  transition: all 0.25s ease;
}

.metric-tile:hover {
  border-color: rgba(var(--v-theme-primary), 0.15);
  transform: translateY(-1px);
}

.metric-tile__value {
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.15rem;
  color: rgb(var(--v-theme-primary));
}

.metric-tile__label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 4px;
  font-weight: 500;
}
</style>
