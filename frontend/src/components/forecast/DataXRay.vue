<template>
  <v-expansion-panels class="mb-6" outlined>
    <v-expansion-panel>
      <v-expansion-panel-title>
        <div class="d-flex align-center">
          <v-icon class="mr-3" color="primary">mdi-chart-box-outline</v-icon>
          <span class="text-subtitle-1 font-weight-bold">Advanced Data Inspection</span>
          <v-chip class="ml-3" color="primary" size="x-small" variant="tonal">
            {{ ontology.meta.domain_inference }}
          </v-chip>
        </div>
      </v-expansion-panel-title>

      <v-expansion-panel-text>
        <v-row class="mb-6 mt-2">
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis mb-1">Data Completeness</div>
            <div class="d-flex align-center">
              <v-icon class="mr-1" :color="ontology.meta.completeness_check === 'complete' ? 'success' : 'warning'" icon="mdi-circle-medium" />
              <span class="font-weight-bold text-capitalize">{{ ontology.meta.completeness_check }}</span>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis mb-1">Time Regularity</div>
            <div class="d-flex align-center">
              <v-icon class="mr-1" :color="ontology.problem.granularity.is_regular ? 'success' : 'error'" icon="mdi-circle-medium" />
              <span class="font-weight-bold">{{ ontology.problem.granularity.is_regular ? 'Regular Intervals' : 'Irregular/Gaps' }}</span>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis mb-1">Target Sparsity</div>
            <div class="d-flex align-center">
              <v-progress-linear
                class="mr-3"
                color="primary"
                height="8"
                :model-value="sparsityPercent"
                rounded
                style="width: 80px"
              />
              <span class="font-weight-bold">{{ sparsityPercent.toFixed(1) }}% Zeros</span>
            </div>
          </v-col>
        </v-row>

        <v-divider class="mb-6" />

        <div class="text-overline mb-4">Structure Analysis (First 5 Rows)</div>

        <v-row class="align-stretch" dense>

          <v-col cols="12" md="3">
            <v-card class="h-100 d-flex flex-column border-secondary-light" variant="outlined">
              <div class="pa-3 bg-grey-lighten-4 border-b">
                <div class="text-subtitle-2 font-weight-bold text-medium-emphasis d-flex align-center">
                  <v-icon size="small" start>mdi-clock-outline</v-icon>
                  TIMELINE
                </div>
              </div>
              <v-table class="bg-transparent flex-grow-1" density="compact">
                <thead>
                  <th class="text-left pt-2">
                    {{ timeCol?.display_name || timeCol?.column_name || 'Index' }}
                  </th>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in sampleRows" :key="i">
                    <td class="font-mono text-caption">{{ formatVal(row[timeCol?.column_name || '']) }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card>
          </v-col>

          <v-col cols="12" :md="featureCols.length > 0 ? 6 : 1">
            <v-card v-if="featureCols.length > 0" class="h-100 d-flex flex-column border-info-light" variant="outlined">
              <div class="pa-3 bg-blue-grey-lighten-5 border-b">
                <div class="text-subtitle-2 font-weight-bold text-info-darken-2 d-flex align-center">
                  <v-icon size="small" start>mdi-table-column-plus-after</v-icon>
                  PREDICTORS (COVARIATES)
                </div>
              </div>
              <div class="overflow-x-auto">
                <v-table class="bg-transparent" density="compact">
                  <thead>
                    <tr>
                      <th v-for="col in featureCols" :key="col.column_name" class="text-left pt-2 text-no-wrap">
                        {{ col.display_name || col.column_name }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in sampleRows" :key="i">
                      <td v-for="col in featureCols" :key="col.column_name" class="font-mono text-caption text-no-wrap">
                        {{ formatVal(row[col.column_name]) }}
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </div>
            </v-card>

            <div v-else class="h-100 d-flex align-center justify-center border rounded border-dashed text-medium-emphasis text-caption pa-4 text-center">
              No additional predictors found.<br>Forecasting using history only.
            </div>
          </v-col>

          <v-col class="d-flex align-center justify-center" cols="12" md="1">
            <v-icon color="medium-emphasis" size="large">mdi-arrow-right-thick</v-icon>
          </v-col>

          <v-col cols="12" md="2">
            <v-card class="h-100 d-flex flex-column border-primary" style="border-width: 2px !important;" variant="outlined">
              <div class="pa-3 bg-blue-lighten-5 border-b">
                <div class="text-subtitle-2 font-weight-bold text-primary d-flex align-center">
                  <v-icon size="small" start>mdi-target</v-icon>
                  TARGET
                </div>
              </div>
              <v-table class="bg-transparent flex-grow-1" density="compact">
                <thead>
                  <th class="text-left pt-2 font-weight-bold">
                    {{ targetCol?.display_name || targetCol?.column_name }}
                  </th>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in sampleRows" :key="i">
                    <td class="font-mono text-caption font-weight-bold text-primary">{{ formatVal(row[targetCol?.column_name || '']) }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card>
          </v-col>

        </v-row>

      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup lang="ts">
  import type { ForecastOntology } from '@/types'
  import { computed } from 'vue'

  const props = defineProps<{
    ontology: ForecastOntology
  }>()

  // --- HELPERS FOR THE VIEW ---

  const timeCol = computed(() => props.ontology.columns.find(c => c.role === 'time_index'))
  const targetCol = computed(() => props.ontology.columns.find(c => c.role === 'target'))

  // Get all columns that are NOT time, target, or ignored
  const featureCols = computed(() =>
    props.ontology.columns.filter(c =>
      !['time_index', 'target', 'ignore'].includes(c.role),
    ),
  )

  const sampleRows = computed(() => {
    // If backend provides data, use it. Otherwise, return empty array (or mock data if strictly needed)
    return props.ontology.sample_data || []
  })

  const sparsityPercent = computed(() => {
    const target = props.ontology.columns.find(c => c.role === 'target')
    const ratio = target?.constraints?.sparsity_ratio ?? 0
    return ratio * 100
  })

  function formatVal (val: any) {
    if (val === null || val === undefined) return '-'
    if (typeof val === 'number') return Number.isInteger(val) ? val : val.toFixed(2)
    if (typeof val === 'string' && val.length > 15) return val.slice(0, 12) + '...'
    return val
  }
</script>

<style scoped>
.font-mono {
  font-family: 'Roboto Mono', monospace;
}
.border-dashed {
  border-style: dashed !important;
}
.border-primary {
  border-color: rgb(var(--v-theme-primary)) !important;
}
</style>
