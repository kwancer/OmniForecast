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
        <h2 class="text-h6 font-weight-bold font-header mb-0">Data Preparation</h2>
      </div>
      <v-spacer />

      <div class="hidden-sm-and-down d-flex align-center bg-surface-light px-4 py-2 rounded-lg border">
        <div class="text-center mx-2">
          <div class="text-caption text-medium-emphasis text-uppercase" style="font-size: 10px;">Original Shape</div>
          <div class="font-weight-bold font-mono">{{ store.cleaningReport?.initial_shape.join(' x ') || '?' }}</div>
        </div>
        <v-icon class="mx-2 text-medium-emphasis" size="small">mdi-arrow-right</v-icon>
        <div class="text-center mx-2">
          <div class="text-caption text-medium-emphasis text-uppercase" style="font-size: 10px;">Final Shape</div>
          <div class="font-weight-bold font-mono text-primary">{{ store.cleaningReport?.final_shape.join(' x ') || '?' }}</div>
        </div>
      </div>

      <v-btn
        class="ml-6 hover-lift"
        color="primary"
        elevation="0"
        variant="flat"
        @click="store.setStep('results')"
      >
        View Analytics
        <v-icon end>mdi-chart-line</v-icon>
      </v-btn>
    </div>

    <v-row class="flex-grow-1 ma-0 w-100 bg-background overflow-hidden">
      <!-- Left Panel: Corrections Timeline -->
      <v-col class="h-100 overflow-y-auto border-r bg-surface" cols="12" md="4" style="border-right-width: 1px !important;">
        <div class="pa-4">
          <h3 class="text-subtitle-1 font-weight-bold mb-4 d-flex align-center">
            <v-icon color="secondary" start>mdi-auto-fix</v-icon>
            Applied Transformations
          </h3>

          <v-alert
            v-if="store.cleaningReport?.summary"
            class="mb-6 text-body-2"
            color="primary"
            icon="mdi-information-outline"
            variant="tonal"
          >
            {{ store.cleaningReport.summary }}
          </v-alert>

          <div v-if="store.cleaningReport?.actions.length" class="ml-6 border-s-sm pl-8 relative">
            <div
              v-for="(action, index) in store.cleaningReport?.actions"
              :key="index"
              class="mb-6 position-relative group hover-lift rounded-lg px-2 py-1 mx-n2"
            >
              <div class="position-absolute bg-background rounded-circle border d-flex align-center justify-center" style="left: -49px; top: 0px; width: 34px; height: 34px;">
                <v-avatar :color="getActionColor(action.action)" size="30" variant="tonal">
                  <v-icon :icon="getActionIcon(action.action)" size="16" />
                </v-avatar>
              </div>

              <div class="font-weight-bold text-subtitle-2 d-flex align-center">
                {{ action.column }}
                <v-chip class="ml-2 text-uppercase" :color="getActionColor(action.action)" size="x-small" variant="flat">
                  {{ formatActionName(action.action) }}
                </v-chip>
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                {{ action.description }}
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-medium-emphasis">
            <v-icon class="mb-4" color="success" size="48">mdi-check-circle-outline</v-icon>
            <p>Dataset arrived in optimal condition.</p>
            <p class="text-caption">No transformations required.</p>
          </div>
        </div>
      </v-col>

      <!-- Right Panel: Data Preview -->
      <v-col class="h-100 overflow-y-auto d-flex flex-column" cols="12" md="8">
        <div class="pa-4 h-100 d-flex flex-column">
          <div class="d-flex align-center mb-4">
            <div>
              <h3 class="text-subtitle-1 font-weight-bold d-flex align-center ma-0">
                <v-icon color="primary" start>mdi-table-large</v-icon>
                Dataset Snapshot
              </h3>
              <div class="text-caption text-medium-emphasis mt-1">This is the first 10 items</div>
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

          <v-card class="d-flex flex-column text-body-2 border layout-card bg-surface" style="border-radius: 8px; overflow-x: auto;" variant="flat">
            <v-table v-if="currentData.headers.length > 0" density="comfortable" hover style="background: transparent;">
              <thead class="bg-surface-light">
                <tr>
                  <th
                    v-for="h in currentData.headers"
                    :key="h"
                    class="font-weight-bold font-mono"
                    :class="[
                      affectedColumns.has(h) ? 'text-secondary' : 'text-medium-emphasis',
                      ignoredColumns.has(h.trim()) && viewMode === 'raw' ? 'opacity-40 text-decoration-line-through' : ''
                    ]"
                    style="white-space: nowrap; background: var(--v-theme-surface-light) !important;"
                  >
                    <v-icon v-if="affectedColumns.has(h)" class="mr-1" size="small">mdi-auto-fix</v-icon>
                    <v-icon v-if="ignoredColumns.has(h.trim()) && viewMode === 'raw'" class="mr-1" size="small">mdi-eye-off</v-icon>
                    {{ h }}
                    <v-chip v-if="targetColumn === h.trim()" class="ml-2 font-weight-bold" color="primary" size="x-small">TARGET</v-chip>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in currentData.rows" :key="idx">
                  <td
                    v-for="(col, i) in row"
                    :key="i"
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
            <div v-else class="ma-auto text-center text-medium-emphasis pa-8">
              <v-icon class="mb-4" size="32">mdi-file-delimited-outline</v-icon>
              <div>Connecting to data buffer...</div>
              <div class="text-caption mt-2">Only available for CSV uploads.</div>
            </div>
          </v-card>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref } from 'vue'
  import { useForecastStore } from '@/stores/forecast'

  const store = useForecastStore()

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
      // Try to round excessively long floats for neatness, but handle strings nicely.
      if (typeof val === 'number') {
        return Number.isInteger(val) ? String(val) : val.toFixed(4)
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

  const targetColumn = computed(() => {
    if (store.ontology?.columns) {
      const target = store.ontology.columns.find(c => c.role === 'target')
      if (target) return target.column_name.trim()
    }
    return null
  })

  onMounted(async () => {
    if (store.file && (store.file.type.includes('csv') || store.file.name.endsWith('.csv'))) {
      try {
        // Read a small chunk to prevent memory issues
        const text = await store.file.slice(0, 10_000).text()
        const lines = text.split(/\r?\n/).filter(l => l.trim().length > 0)

        if (lines.length > 0) {
          // Simplistic CSV parsing (ignores quoted commas for a quick snapshot)
          // For real robustness, a library is better, but this handles basic datasets smoothly
          const parseLine = (line: string) => {
            const row = []
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
          if (!firstLine) return
          const headers = parseLine(firstLine)
          const rows = lines.slice(1, 11).map(l => parseLine(l)) // Preview top 10 rows

          parsedData.value = { headers, rows }
        }
      } catch (error) {
        console.warn('Failed to parse dataset preview', error)
      }
    }
  })

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
</script>

<style scoped>
.layout-card {
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02) !important;
}

:deep(thead tr th) {
  border-bottom: 2px solid var(--v-border-color) !important;
}
</style>
