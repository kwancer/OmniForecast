<template>
  <v-container class="fill-height d-flex flex-column">
    <div class="d-flex align-center mb-4">
      <v-btn icon="mdi-refresh" variant="text" @click="store.reset()"></v-btn>
      <h2 class="text-h5 font-header ml-2">Forecast Output</h2>
    </div>

    <v-row class="flex-grow-1 overflow-y-auto">
      <v-col cols="12" md="8">
        <v-card variant="outlined" class="h-100 pa-4 d-flex flex-column">
          <div class="d-flex justify-space-between align-center mb-4">
            <div class="text-overline text-primary">TRAJECTORY</div>
            <v-chip color="primary" size="small" variant="outlined">CONFIDENCE: HIGH</v-chip>
          </div>
          
          <v-sheet color="transparent" class="flex-grow-1 d-flex align-center justify-center border-thin rounded overflow-y-auto">
             <v-table density="compact" class="w-100 bg-transparent">
               <thead>
                 <tr>
                   <th class="text-left font-mono">Time</th>
                   <th class="text-right font-mono text-primary">Forecast</th>
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
        <v-card color="secondary" variant="tonal" class="pa-4 mb-4">
          <div class="d-flex align-center mb-2">
            <v-icon icon="mdi-brain" class="mr-2"></v-icon>
            <span class="font-weight-bold">Neural Insight</span>
          </div>
          <p class="text-body-2">{{ store.explanation }}</p>
        </v-card>

        <v-btn variant="outlined" block class="mb-2" prepend-icon="mdi-download">Export JSON</v-btn>
        <v-btn variant="outlined" block prepend-icon="mdi-file-chart">Export Report</v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useForecastStore } from '@/stores/forecast'

const store = useForecastStore()

const formatDate = (val: string | number | undefined) => {
  if (!val) return ''
  return new Date(val).toLocaleDateString()
}

const formatValue = (val: string | number | undefined) => {
  if (val === undefined) return ''
  if (typeof val !== 'number') return val
  return val.toFixed(2)
}
</script>
