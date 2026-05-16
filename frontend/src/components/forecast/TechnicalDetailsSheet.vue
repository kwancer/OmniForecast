<template>
  <v-bottom-sheet v-model="isOpen" inset max-width="1200">
    <v-card class="technical-sheet-card" rounded="lg">
      <v-card-title class="d-flex align-center pa-4">
        <v-icon class="mr-2" color="primary">mdi-lightbulb-outline</v-icon>
        <span class="text-h6 font-weight-bold">Reasoning & Technical Details</span>
        <v-spacer />
        <v-btn icon="mdi-close" size="small" variant="text" @click="isOpen = false" />
      </v-card-title>
      <v-divider />
      <v-card-text class="pa-4 overflow-y-auto" style="max-height: 85vh;">

        <!-- Selected Method Summary -->
        <v-card v-if="store.modelMetadata" class="mb-4 pa-4" rounded="lg" variant="outlined">
          <div class="d-flex align-center flex-wrap" style="gap: 12px;">
            <div class="d-flex align-center">
              <div class="panel-icon panel-icon--primary mr-3">
                <v-icon color="white" size="16">mdi-brain</v-icon>
              </div>
              <span class="font-weight-bold text-body-1">Selected Method</span>
            </div>
            <v-chip color="primary" size="small" variant="flat">{{ store.modelMetadata.name }}</v-chip>
            <v-chip
              :color="store.modelMetadata.supports_covariates ? 'success' : 'grey'"
              size="small"
              variant="tonal"
            >
              <v-icon size="12" start>{{ store.modelMetadata.supports_covariates ? 'mdi-check' : 'mdi-close' }}</v-icon>
              {{ store.modelMetadata.supports_covariates ? 'Uses your factors' : 'Ignores extra factors' }}
            </v-chip>
            <span class="text-body-2 text-medium-emphasis ml-auto hidden-sm-and-down">{{ store.modelMetadata?.description }}</span>
          </div>
        </v-card>

        <!-- Nested Technical Panels -->
        <v-expansion-panels class="styled-panels" multiple variant="accordion">
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
                <!-- Reliability Metrics -->
                <div v-if="displayMetrics.length > 0" class="metric-strip">
                  <div class="text-caption text-medium-emphasis mb-2">Reliability Metrics</div>
                  <v-row dense>
                    <v-col v-for="metric in displayMetrics" :key="metric.name" cols="6" md="3">
                      <div class="metric-tile">
                        <div class="metric-tile__value">{{ formatMetricValue(metric) }}</div>
                        <div class="metric-tile__label">{{ getMetricLabel(metric.name) }}</div>
                      </div>
                    </v-col>
                  </v-row>
                </div>
                <BacktestChart v-if="store.backtestData.length > 0" :data="store.backtestData" />
                <ModelTournament :results="store.tournamentResults" />
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- Covariate Values -->
          <v-expansion-panel v-if="covariateDisplayData.length > 0" rounded="lg">
            <v-expansion-panel-title class="font-weight-bold">
              <div class="d-flex align-center">
                <div class="panel-icon panel-icon--info mr-3">
                  <v-icon color="white" size="16">mdi-chart-timeline-variant</v-icon>
                </div>
                Covariate History & Model Inputs
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <div class="d-flex flex-column pa-2" style="gap: 16px;">
                <v-alert
                  v-if="hasActiveCovariates && !selectedModelSupportsCovariates"
                  class="text-body-2"
                  color="warning"
                  icon="mdi-alert"
                  variant="tonal"
                >
                  The selected model <strong>{{ store.modelMetadata?.name }}</strong> does not support covariates.
                  Any planned drivers or external factors below were <strong>ignored</strong> during forecasting.
                </v-alert>
                <v-alert
                  v-else-if="hasActiveCovariates && selectedModelSupportsCovariates"
                  class="text-body-2"
                  color="success"
                  icon="mdi-check-circle"
                  variant="tonal"
                >
                  The selected model <strong>{{ store.modelMetadata?.name }}</strong> supports covariates and used the <strong>active</strong> factors shown below.
                </v-alert>
                <v-alert
                  v-else
                  class="text-body-2"
                  color="primary"
                  icon="mdi-information-outline"
                  variant="tonal"
                >
                  No active covariates. All columns below are ignored and were not used by the model.
                </v-alert>

                <div class="covariate-grid">
                  <v-card
                    v-for="item in covariateDisplayData"
                    :key="item.column_name"
                    class="covariate-card"
                    :class="{ 'covariate-card--ignored': item.isIgnored }"
                    variant="outlined"
                  >
                    <v-card-item>
                      <template #prepend>
                        <v-icon
                          :color="item.isIgnored ? 'grey' : (item.covariate_type === 'known_future' ? 'success' : 'warning')"
                          size="20"
                        >
                          {{ item.isIgnored ? 'mdi-eye-off' : (item.covariate_type === 'known_future' ? 'mdi-pencil-circle' : 'mdi-lock') }}
                        </v-icon>
                      </template>
                      <v-card-title
                        class="text-subtitle-2 font-weight-bold"
                        :class="{ 'text-disabled text-decoration-line-through': item.isIgnored }"
                      >
                        {{ item.display_name }}
                      </v-card-title>
                      <template #append>
                        <v-chip
                          :color="item.isIgnored ? 'grey' : (item.covariate_type === 'known_future' ? 'success' : 'warning')"
                          size="x-small"
                          variant="tonal"
                        >
                          {{ item.isIgnored ? 'Ignored' : (item.covariate_type === 'known_future' ? 'Planned Driver' : 'External Factor') }}
                        </v-chip>
                      </template>
                    </v-card-item>
                    <v-card-text class="pt-0">
                      <div class="d-flex align-center mb-2">
                        <v-chip
                          class="mr-2"
                          :color="item.isIgnored ? 'grey' : 'info'"
                          size="x-small"
                          variant="outlined"
                        >
                          {{ item.strategyLabel }}
                        </v-chip>
                      </div>

                    </v-card-text>
                  </v-card>
                </div>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- Data Cleaning Report -->
          <v-expansion-panel v-if="store.cleaningReport" rounded="lg">
            <v-expansion-panel-title class="font-weight-bold">
              <div class="d-flex align-center">
                <div class="panel-icon panel-icon--secondary mr-3">
                  <v-icon color="white" size="16">mdi-auto-fix</v-icon>
                </div>
                Data Preparation Report
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row>
                <!-- Applied Transformations -->
                <v-col cols="12" md="5">
                  <div class="section-header mb-4">
                    <div class="section-header__icon section-header__icon--secondary">
                      <v-icon color="white" size="18">mdi-auto-fix</v-icon>
                    </div>
                    <h3 class="text-subtitle-1 font-weight-bold mb-0">Applied Transformations</h3>
                  </div>

                  <v-alert
                    v-if="store.cleaningReport?.summary"
                    class="mb-4 text-body-2 summary-alert"
                    color="primary"
                    icon="mdi-information-outline"
                    variant="tonal"
                  >
                    {{ store.cleaningReport.summary }}
                  </v-alert>

                  <div v-if="store.cleaningReport?.actions.length" class="transform-timeline">
                    <div
                      v-for="(action, index) in store.cleaningReport?.actions"
                      :key="index"
                      class="transform-item"
                    >
                      <div class="transform-item__dot">
                        <v-avatar :color="getActionColor(action.action)" size="32" variant="tonal">
                          <v-icon :icon="getActionIcon(action.action)" size="16" />
                        </v-avatar>
                      </div>
                      <div class="transform-item__content">
                        <div class="d-flex align-center mb-1">
                          <span class="font-weight-bold text-subtitle-2">{{ action.column }}</span>
                          <v-chip class="ml-2 text-uppercase" :color="getActionColor(action.action)" size="x-small" variant="flat">
                            {{ formatActionName(action.action) }}
                          </v-chip>
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          {{ action.description }}
                        </div>
                      </div>
                    </div>
                  </div>
                </v-col>

                <!-- Dataset Snapshot -->
                <v-col cols="12" md="7">
                  <div class="d-flex align-center mb-4">
                    <div class="section-header">
                      <div class="section-header__icon section-header__icon--primary">
                        <v-icon color="white" size="18">mdi-table-large</v-icon>
                      </div>
                      <h3 class="text-subtitle-1 font-weight-bold ma-0">Dataset Snapshot</h3>
                    </div>
                    <v-spacer />
                    <v-btn-toggle
                      v-model="viewMode"
                      color="primary"
                      density="compact"
                      mandatory
                      rounded="lg"
                      variant="outlined"
                    >
                      <v-btn class="text-caption font-weight-bold" size="small" value="raw">Raw</v-btn>
                      <v-btn class="text-caption font-weight-bold" :disabled="!store.cleaningReport?.cleaned_sample" size="small" value="cleaned">Cleaned</v-btn>
                    </v-btn-toggle>
                  </div>

                  <v-card class="border layout-card bg-surface" style="border-radius: 12px; overflow-x: auto;" variant="flat">
                    <v-table
                      v-if="currentData.headers.length > 0"
                      density="compact"
                      fixed-header
                      hover
                      style="background: transparent;"
                    >
                      <thead class="bg-surface-light">
                        <tr>
                          <th
                            v-for="h in currentData.headers"
                            :key="h"
                            class="font-weight-bold font-mono text-caption"
                            :class="[
                              affectedColumns.has(h) ? 'text-secondary' : 'text-medium-emphasis',
                              ignoredColumns.has(h.trim()) && viewMode === 'raw' ? 'opacity-40 text-decoration-line-through' : ''
                            ]"
                            style="white-space: nowrap; background: var(--v-theme-surface-light) !important;"
                          >
                            <v-icon v-if="affectedColumns.has(h)" class="mr-1" size="small">mdi-auto-fix</v-icon>
                            {{ h }}
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(row, idx) in currentData.rows" :key="idx">
                          <td
                            v-for="(col, i) in row"
                            :key="i"
                            class="text-caption"
                            :class="[
                              currentData.headers[i] && affectedColumns.has(currentData.headers[i]) ? 'text-secondary font-weight-medium bg-secondary-lighten-5' : 'text-medium-emphasis',
                              currentData.headers[i] && ignoredColumns.has(currentData.headers[i].trim()) && viewMode === 'raw' ? 'opacity-40 bg-surface text-decoration-line-through text-disabled' : ''
                            ]"
                            style="white-space: nowrap;"
                          >
                            {{ col }}
                          </td>
                        </tr>
                      </tbody>
                    </v-table>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Feature Engineering Details -->
              <v-row
                v-if="store.modelMetadata?.feature_engineering_steps?.length"
                class="mt-4"
              >
                <v-col cols="12">
                  <div class="section-header mb-4">
                    <div class="section-header__icon section-header__icon--warning">
                      <v-icon color="white" size="18">mdi-hammer-wrench</v-icon>
                    </div>
                    <h3 class="text-subtitle-1 font-weight-bold mb-0">Feature Engineering</h3>
                  </div>
                  <v-alert
                    class="text-body-2 mb-4"
                    color="warning"
                    icon="mdi-information-outline"
                    variant="tonal"
                  >
                    The selected model automatically generated these additional features to improve forecast accuracy.
                  </v-alert>
                  <div class="d-flex flex-wrap ga-2">
                    <v-chip
                      v-for="(step, index) in store.modelMetadata.feature_engineering_steps"
                      :key="index"
                      color="warning"
                      label
                      size="small"
                      variant="tonal"
                    >
                      {{ step }}
                    </v-chip>
                  </div>
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>

        </v-expansion-panels>

      </v-card-text>
    </v-card>
  </v-bottom-sheet>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import { useAppStore } from '@/stores/app'
  import { useForecastStore } from '@/stores/forecast'
  import { formatMetric, formatNumber } from '@/utils/formatters'
  import BacktestChart from './BacktestChart.vue'
  import ModelTournament from './ModelTournament.vue'

  const props = defineProps<{
    modelValue: boolean
  }>()

  const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
  }>()

  const isOpen = computed({
    get: () => props.modelValue,
    set: val => emit('update:modelValue', val),
  })

  const store = useForecastStore()
  const appStore = useAppStore()
  const isAlternativeUi = import.meta.env.VITE_ALTERNATIVE_UI === 'true'

  // Data Cleaning Logic
  const viewMode = ref<'raw' | 'cleaned'>('raw')
  const parsedData = ref<{ headers: string[], rows: string[][] }>({ headers: [], rows: [] })

  const cleanedParsedData = computed(() => {
    if (!store.cleaningReport?.cleaned_sample || store.cleaningReport.cleaned_sample.length === 0) {
      return { headers: [], rows: [] }
    }
    const sample = store.cleaningReport.cleaned_sample
    const firstRow = sample[0]
    if (!firstRow) return { headers: [], rows: [] }
    const headers = Object.keys(firstRow)
    const rows = sample.map(row => headers.map(h => {
      const val = row[h]
      if (typeof val === 'number') {
        return formatNumber(val, { decimals: 4 })
      }
      return String(val ?? '')
    }))
    return { headers, rows }
  })

  const currentData = computed(() => {
    return viewMode.value === 'raw' ? parsedData.value : cleanedParsedData.value
  })

  const affectedColumns = computed(() => {
    if (!store.cleaningReport?.actions) return new Set<string>()
    return new Set(store.cleaningReport.actions.map(a => a.column))
  })

  const ignoredColumns = computed(() => {
    const ignored = new Set<string>()
    if (store.ontology?.ignored_columns) {
      for (const c of store.ontology.ignored_columns) ignored.add(c.trim())
    }
    if (store.ontology?.columns) {
      for (const c of store.ontology.columns) {
        if (c.role === 'ignore') ignored.add(c.column_name.trim())
      }
    }
    return ignored
  })

  // Covariate display data
  const selectedModelSupportsCovariates = computed(() =>
    store.modelMetadata?.supports_covariates === true,
  )

  const covariateDisplayData = computed(() => {
    if (!store.ontology?.columns) return []

    const ignoredSet = new Set<string>(store.ontology.ignored_columns || [])
    for (const c of store.ontology.columns) {
      if (c.role === 'ignore') ignoredSet.add(c.column_name)
    }

    const allCovariates = store.ontology.columns.filter(c =>
      (c.covariate_type != null || c.role === 'covariate' || ignoredSet.has(c.column_name))
      && c.role !== 'target'
      && c.role !== 'time_index'
      && c.role !== 'group_id',
    )

    if (allCovariates.length === 0) return []

    const overridesArr = store.ontology.scenario_overrides || []
    const overrides: Record<string, number | number[] | 'seasonal'> = {}
    for (const o of overridesArr) {
      overrides[o.column_name] = o.values
    }
    return allCovariates.map(col => {
      const colName = col.column_name
      const isIgnored = ignoredSet.has(colName)
      const override = overrides[colName]

      let strategyLabel = 'Hold Steady'
      if (isIgnored) {
        strategyLabel = 'Ignored'
      } else if (override === 'seasonal') {
        strategyLabel = 'Use Seasonal Pattern'
      } else if (Array.isArray(override)) {
        strategyLabel = 'Custom Series'
      } else if (typeof override === 'number') {
        strategyLabel = 'Set Fixed'
      }

      return {
        column_name: colName,
        display_name: col.display_name || colName,
        covariate_type: col.covariate_type || 'unknown_past',
        isIgnored,
        strategyLabel,
      }
    })
  })

  const hasActiveCovariates = computed(() =>
    covariateDisplayData.value.some(c => !c.isIgnored),
  )

  function getActionIcon (action: string) {
    switch (action) {
      case 'normalization': { return 'mdi-format-letter-case'
      }
      case 'type_conversion': { return 'mdi-variable'
      }
      case 'aggregation': { return 'mdi-layers-triple'
      }
      case 'resampling': { return 'mdi-calendar-clock'
      }
      case 'gap_filling': { return 'mdi-plus-box'
      }
      case 'imputation': { return 'mdi-eyedropper'
      }
      case 'column_dropping': { return 'mdi-table-column-remove'
      }
      default: { return 'mdi-wrench'
      }
    }
  }

  function getActionColor (action: string) {
    switch (action) {
      case 'imputation': { return 'warning'
      }
      case 'resampling': { return 'info'
      }
      case 'gap_filling': { return 'secondary'
      }
      case 'type_conversion': { return 'primary'
      }
      case 'column_dropping': { return 'grey-darken-1'
      }
      default: { return 'primary'
      }
    }
  }

  function formatActionName (name: string) {
    return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }

  // Metrics
  const displayMetrics = computed(() => {
    if (isAlternativeUi) {
      return store.metrics.filter(m => m.name === 'RMSE' || m.name === 'MAE' || m.name === 'MAPE')
    }
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
    return formatMetric(metric.value, metric.name)
  }

  function formatDate (val: any) {
    if (val === undefined || val === null) return 'N/A'
    if (typeof val === 'number' && val > 1700 && val < 2500) {
      return val.toString()
    }
    const date = new Date(val)
    if (Number.isNaN(date.getTime())) return 'Invalid Date'

    if (store.ontology?.problem.granularity.unit === 'year') {
      return date.getFullYear().toString()
    }

    return date.toLocaleDateString()
  }

  function formatValue (val: any) {
    return formatNumber(val)
  }

  async function copyForecastTable () {
    const timeCol = store.timeCol
    const headers = ['Date', 'Lower (80%)', 'Median', 'Upper (80%)']
    const rows = store.forecastResults.map((row: any) => [
      row.date || row.year || row[timeCol],
      row.conf_80_lower ?? row.lower ?? '',
      row.median_forecast ?? row.mean ?? row[store.targetCol] ?? '',
      row.conf_80_upper ?? row.upper ?? '',
    ])
    const csv = [headers.join('\t'), ...rows.map(r => r.join('\t'))].join('\n')
    try {
      await navigator.clipboard.writeText(csv)
      appStore.notify('Forecast data copied to clipboard', 'success')
    } catch {
      appStore.notify('Failed to copy data', 'error')
    }
  }

  onMounted(async () => {
    if (store.file && (store.file.type.includes('csv') || store.file.name.endsWith('.csv'))) {
      try {
        const text = await store.file.slice(0, 10_000).text()
        const lines = text.split(/\r?\n/).filter(l => l.trim().length > 0)
        if (lines.length > 0) {
          const parseLine = (line: string) => {
            const row: string[] = []
            let inQuotes = false
            let val = ''
            for (const char of line) {
              if (char === '"') inQuotes = !inQuotes
              else if (char === ',' && !inQuotes) {
                row.push(val.trim())
                val = ''
              } else {
                val += char
              }
            }
            row.push(val.trim())
            return row
          }
          const firstLine = lines[0]
          if (firstLine) {
            const headers = parseLine(firstLine)
            const rows = lines.slice(1, 11).map(l => parseLine(l))
            parsedData.value = { headers, rows }
          }
        }
      } catch (error) {
        console.warn('Failed to parse dataset preview', error)
      }
    }
  })

  function downloadForecastCSV () {
    const timeCol = store.timeCol
    const headers = ['Date', 'Lower (80%)', 'Median', 'Upper (80%)']
    const rows = store.forecastResults.map((row: any) => [
      row.date || row.year || row[timeCol],
      row.conf_80_lower ?? row.lower ?? '',
      row.median_forecast ?? row.mean ?? row[store.targetCol] ?? '',
      row.conf_80_upper ?? row.upper ?? '',
    ])
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `forecast_data_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }
</script>

<style scoped>
.font-mono {
  font-family: 'JetBrains Mono', 'Roboto Mono', monospace;
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

.panel-icon--info {
  background: linear-gradient(135deg, rgb(var(--v-theme-info)), rgba(var(--v-theme-info), 0.7));
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

.metric-strip {
  background: rgba(var(--v-theme-surface), 0.6);
  border: 1px solid rgba(var(--v-theme-primary), 0.06);
  border-radius: 12px;
  padding: 16px;
}

/* ─── Cleaning Report Styles ─── */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
}

.section-header__icon--primary {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)), rgba(var(--v-theme-primary), 0.7));
}

.section-header__icon--secondary {
  background: linear-gradient(135deg, rgb(var(--v-theme-secondary)), rgba(var(--v-theme-secondary), 0.7));
}

.section-header__icon--warning {
  background: linear-gradient(135deg, #fb8c00, #ffb74d);
}

.summary-alert {
  border-radius: 12px !important;
}

.transform-timeline {
  position: relative;
}

.transform-timeline::before {
  content: '';
  position: absolute;
  left: 27px;
  top: 24px;
  bottom: 24px;
  width: 2px;
  background: linear-gradient(
    to bottom,
    rgba(var(--v-theme-primary), 0.3),
    rgba(var(--v-theme-secondary), 0.15)
  );
  border-radius: 2px;
}

.transform-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 8px;
  margin-bottom: 4px;
  border-radius: 10px;
  transition: all 0.2s ease;
  position: relative;
}

.transform-item:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}

.transform-item__dot {
  flex-shrink: 0;
  z-index: 1;
}

.transform-item__content {
  flex-grow: 1;
  min-width: 0;
}

.layout-card {
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02) !important;
}

/* ─── Covariate Grid ─── */
.covariate-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.covariate-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.08);
  border-radius: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.covariate-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.covariate-card--ignored {
  opacity: 0.5;
  background: rgba(var(--v-theme-surface), 0.6);
  filter: grayscale(0.5);
}

.value-row {
  display: flex;
  align-items: baseline;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
