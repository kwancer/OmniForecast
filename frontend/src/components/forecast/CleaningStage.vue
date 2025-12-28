<template>
  <v-container class="fill-height d-flex flex-column">
    <div class="d-flex align-center mb-6">
      <v-btn icon="mdi-arrow-left" variant="text" @click="store.setStep('plan')"></v-btn>
      <h2 class="text-h5 font-header ml-2">Data Preparation</h2>
      <v-chip color="success" class="ml-auto" size="small" prepend-icon="mdi-check-circle">READY FOR ANALYSIS</v-chip>
    </div>

    <v-row class="flex-grow-1 overflow-hidden">
      <!-- Left Column: Report and Data Preview -->
      <v-col cols="12" md="8" class="h-100 overflow-y-auto">
        <v-card variant="outlined" class="mb-4 bg-surface">
          <v-tabs v-model="tab" color="primary">
            <v-tab value="report">Corrections Report</v-tab>
            <v-tab value="data">Cleaned Data Preview</v-tab>
          </v-tabs>
          <v-divider></v-divider>
          
          <v-window v-model="tab">
            <!-- Report Tab -->
            <v-window-item value="report">
              <v-list lines="two" v-if="store.cleaningReport?.actions.length">
                <template v-for="(action, index) in store.cleaningReport?.actions" :key="index">
                  <v-list-item>
                    <template v-slot:prepend>
                      <v-avatar :color="getActionColor(action.action)" size="40" variant="tonal">
                        <v-icon :icon="getActionIcon(action.action)"></v-icon>
                      </v-avatar>
                    </template>

                    <v-list-item-title class="font-weight-bold">
                      {{ action.column }}: {{ formatActionName(action.action) }}
                    </v-list-item-title>
                    <v-list-item-subtitle class="text-wrap">
                      {{ action.description }}
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-divider v-if="index < (store.cleaningReport?.actions.length ?? 0) - 1" inset></v-divider>
                </template>
              </v-list>
              <v-card-text v-else class="text-center py-8 text-medium-emphasis">
                No specific transformations were required. The dataset was already in a model-ready state.
              </v-card-text>
            </v-window-item>

            <!-- Data Tab -->
            <v-window-item value="data">
               <v-card-text v-if="store.cleanedData.length > 0">
                 <div class="d-flex justify-end mb-2">
                   <v-btn
                    variant="text"
                    color="primary"
                    prepend-icon="mdi-download"
                    size="small"
                    @click="downloadCsv"
                   >
                    Download CSV
                   </v-btn>
                 </div>
                 <v-table density="compact" fixed-header height="400px">
                   <thead>
                     <tr>
                       <th v-for="key in dataHeaders" :key="key" class="text-left">
                         {{ key }}
                       </th>
                     </tr>
                   </thead>
                   <tbody>
                     <tr v-for="(row, i) in displayedData" :key="i">
                       <td v-for="key in Object.keys(row || {})" :key="key">
                         {{ formatCell(row[key]) }}
                       </td>
                     </tr>
                   </tbody>
                 </v-table>
                 <div class="text-caption text-center mt-2 text-medium-emphasis">
                   Showing {{ displayedData.length }} of {{ store.cleanedData.length }} rows
                 </div>
               </v-card-text>
               <v-card-text v-else class="text-center py-8 text-medium-emphasis">
                 No data available to display.
               </v-card-text>
            </v-window-item>
          </v-window>
        </v-card>
      </v-col>

      <!-- Right Column: Summary -->
      <v-col cols="12" md="4" class="d-flex flex-column">
        <v-card color="primary" variant="tonal" class="pa-4 mb-4">
          <div class="text-overline mb-2">Preparation Summary</div>
          <div class="d-flex justify-space-between mb-1">
            <span class="text-caption">Original Shape:</span>
            <span class="text-caption font-weight-bold">{{ store.cleaningReport?.initial_shape.join(' x ') }}</span>
          </div>
          <div class="d-flex justify-space-between mb-3">
            <span class="text-caption">Final Shape:</span>
            <span class="text-caption font-weight-bold">{{ store.cleaningReport?.final_shape.join(' x ') }}</span>
          </div>
          <p class="text-body-2 mb-0">
            {{ store.cleaningReport?.summary }}
          </p>
        </v-card>

        <v-spacer></v-spacer>

        <v-card variant="flat" border class="pa-4 bg-surface">
          <p class="text-caption text-medium-emphasis mb-4">
            The system has prepared your data for modelling. Proceed to view the forecast results.
          </p>
          <v-btn
            color="primary"
            block
            size="large"
            @click="store.setStep('results')"
            elevation="2"
          >
            Finalise & Continue
            <v-icon end>mdi-chevron-right</v-icon>
          </v-btn>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useForecastStore } from '@/stores/forecast'

const store = useForecastStore()
const tab = ref('report')

const displayedData = computed(() => {
  // Show only first 500 rows to avoid lag if large
  return store.cleanedData.slice(0, 500)
})

const dataHeaders = computed(() => {
  if (store.cleanedData && store.cleanedData.length > 0) {
    return Object.keys(store.cleanedData[0] || {})
  }
  return []
})

const getActionIcon = (action: string) => {
  switch (action) {
    case 'normalization': return 'mdi-format-letter-case'
    case 'type_conversion': return 'mdi-variable'
    case 'aggregation': return 'mdi-layers-triple'
    case 'resampling': return 'mdi-calendar-clock'
    case 'gap_filling': return 'mdi-plus-box'
    case 'imputation': return 'mdi-eyedropper'
    default: return 'mdi-wrench'
  }
}

const getActionColor = (action: string) => {
  switch (action) {
    case 'imputation': return 'orange'
    case 'resampling': return 'blue'
    case 'gap_filling': return 'purple'
    default: return 'primary'
  }
}

const formatActionName = (name: string) => {
  return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

const formatCell = (val: any) => {
  if (typeof val === 'number') {
    return val.toLocaleString(undefined, { maximumFractionDigits: 4 })
  }
  return val
}

const downloadCsv = () => {
  if (!store.cleanedData.length) return

  const headers = dataHeaders.value
  const headerRow = headers.join(',')

  const bodyRows = store.cleanedData.map(row => {
    return headers.map(header => {
      const val = row[header]
      const escaped = ('' + val).replace(/"/g, '\\"')
      return `"${escaped}"`
    }).join(',')
  })

  const csvContent = [headerRow, ...bodyRows].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.setAttribute('hidden', '')
  a.setAttribute('href', url)
  a.setAttribute('download', 'cleaned_data.csv')
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
</script>
