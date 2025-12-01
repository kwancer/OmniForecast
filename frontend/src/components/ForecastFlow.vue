<template>
  <v-container class="fill-height pa-0" fluid>
    <v-row justify="center" align="center" class="fill-height ma-0">
      <v-col cols="12" md="10" lg="8" class="fill-height d-flex flex-column">
        
        <!-- Header -->
        <div class="d-flex align-center py-6">
          <v-icon icon="mdi-compass-outline" color="primary" size="32" class="mr-3"></v-icon>
          <div>
            <h1 class="text-h5 font-weight-bold font-header text-white">OmniForecast</h1>
            <div class="text-caption text-medium-emphasis font-header">INDUSTRIAL INTELLIGENCE</div>
          </div>
        </div>

        <!-- Main Content Area -->
        <v-card class="flex-grow-1 d-flex flex-column mb-6" color="surface" border>
          <v-carousel
            v-model="step"
            :show-arrows="false"
            hide-delimiters
            class="fill-height"
            height="100%"
          >
            
            <!-- STEP 1: UPLOAD & INTENT -->
            <v-carousel-item value="upload">
              <v-container class="fill-height d-flex flex-column justify-center align-center" style="max-width: 600px;">
                <div class="text-center mb-8">
                  <h2 class="text-h4 font-header mb-2">Initialize Operation</h2>
                  <p class="text-body-1 text-medium-emphasis">Upload historical data and define your forecasting objective.</p>
                </div>

                <v-file-input
                  v-model="file"
                  label="Historical Data (CSV)"
                  prepend-icon="mdi-database"
                  accept=".csv"
                  class="w-100 mb-4"
                  color="primary"
                ></v-file-input>

                <v-textarea
                  v-model="intent"
                  label="Operational Intent"
                  placeholder="e.g., Forecast sales for the next 12 months focusing on seasonality..."
                  prepend-icon="mdi-text-box-search-outline"
                  rows="4"
                  class="w-100 mb-6"
                  color="primary"
                ></v-textarea>

                <v-btn
                  color="primary"
                  size="large"
                  block
                  @click="analyzeIntent"
                  :loading="loading"
                  :disabled="!file || !intent"
                >
                  <v-icon start>mdi-radar</v-icon>
                  Analyze Signal
                </v-btn>
              </v-container>
            </v-carousel-item>

            <!-- STEP 2: PLAN REVIEW -->
            <v-carousel-item value="plan">
              <v-container class="fill-height d-flex flex-column">
                <div class="d-flex align-center mb-6">
                  <v-btn icon="mdi-arrow-left" variant="text" @click="step = 'upload'"></v-btn>
                  <h2 class="text-h5 font-header ml-2">Mission Plan</h2>
                </div>

                <v-row class="fill-height overflow-y-auto">
                  <v-col cols="12" md="6">
                    <v-card variant="outlined" class="h-100 pa-4">
                      <div class="text-overline text-secondary mb-2">DETECTED ONTOLOGY</div>
                      <pre class="font-mono text-body-2" style="white-space: pre-wrap;">{{ JSON.stringify(ontology, null, 2) }}</pre>
                    </v-card>
                  </v-col>
                  <v-col cols="12" md="6" class="d-flex flex-column justify-center">
                    <v-alert
                      color="secondary"
                      variant="tonal"
                      icon="mdi-robot"
                      title="System Analysis"
                      class="mb-6"
                    >
                      The Intent Layer has mapped your request. The system is ready to execute the forecasting engine using an Additive Regression Model.
                    </v-alert>

                    <v-btn
                      color="primary"
                      size="x-large"
                      block
                      @click="executeForecast"
                      :loading="loading"
                    >
                      <v-icon start>mdi-rocket-launch</v-icon>
                      Execute Forecast
                    </v-btn>
                  </v-col>
                </v-row>
              </v-container>
            </v-carousel-item>

            <!-- STEP 3: RESULTS -->
            <v-carousel-item value="results">
              <v-container class="fill-height d-flex flex-column">
                <div class="d-flex align-center mb-4">
                  <v-btn icon="mdi-refresh" variant="text" @click="step = 'upload'"></v-btn>
                  <h2 class="text-h5 font-header ml-2">Forecast Output</h2>
                </div>

                <v-row class="flex-grow-1">
                  <v-col cols="12" md="8">
                    <v-card variant="outlined" class="h-100 pa-4 d-flex flex-column">
                      <div class="d-flex justify-space-between align-center mb-4">
                        <div class="text-overline text-primary">TRAJECTORY</div>
                        <v-chip color="primary" size="small" variant="outlined">CONFIDENCE: HIGH</v-chip>
                      </div>
                      
                      <!-- Simple Visualization Placeholder using v-sparkline if available or just bars -->
                      <v-sheet color="transparent" class="flex-grow-1 d-flex align-center justify-center border-thin rounded">
                         <!-- Using a simple table for now as chart.js needs setup -->
                         <v-table density="compact" class="w-100 h-100 bg-transparent">
                           <thead>
                             <tr>
                               <th class="text-left font-mono">Time</th>
                               <th class="text-right font-mono text-primary">Forecast</th>
                             </tr>
                           </thead>
                           <tbody>
                             <tr v-for="(item, i) in forecastResults" :key="i">
                               <td class="font-mono">{{ formatDate(item[timeCol]) }}</td>
                               <td class="font-mono text-right text-primary font-weight-bold">{{ formatValue(item[targetCol]) }}</td>
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
                      <p class="text-body-2">{{ explanation }}</p>
                    </v-card>

                    <v-btn variant="outlined" block class="mb-2" prepend-icon="mdi-download">Export JSON</v-btn>
                    <v-btn variant="outlined" block prepend-icon="mdi-file-chart">Export Report</v-btn>
                  </v-col>
                </v-row>
              </v-container>
            </v-carousel-item>

          </v-carousel>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'

const step = ref('upload')
const loading = ref(false)
const file = ref(null)
const intent = ref('')
const ontology = ref(null)
const forecastResults = ref([])
const explanation = ref('')

// Helper to find cols from ontology
const timeCol = computed(() => {
  if (!ontology.value) return 'Date'
  const col = ontology.value.columns.find(c => c.role === 'time_index')
  return col ? col.column_name : 'Date'
})

const targetCol = computed(() => {
  if (!ontology.value) return 'Value'
  const col = ontology.value.columns.find(c => c.role === 'target')
  return col ? col.column_name : 'Value'
})

const formatDate = (val) => {
  if (!val) return ''
  return new Date(val).toLocaleDateString()
}

const formatValue = (val) => {
  if (typeof val !== 'number') return val
  return val.toFixed(2)
}

const analyzeIntent = async () => {
  if (!file.value || !intent.value) return
  
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('prompt', intent.value)

    const response = await fetch('http://localhost:8002/plan', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Plan failed')
    
    ontology.value = await response.json()
    step.value = 'plan'
  } catch (e) {
    console.error(e)
    alert('Analysis failed: ' + e.message)
  } finally {
    loading.value = false
  }
}

const executeForecast = async () => {
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('ontology_json', JSON.stringify(ontology.value))

    const response = await fetch('http://localhost:8002/forecast', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) throw new Error('Forecast failed')
    
    const data = await response.json()
    forecastResults.value = data.forecast
    explanation.value = data.explanation
    step.value = 'results'
  } catch (e) {
    console.error(e)
    alert('Forecast failed: ' + e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Minimal overrides if needed, mostly relying on Vuetify classes */
.font-header {
  font-family: 'Space Grotesk', sans-serif !important;
}
.font-mono {
  font-family: 'JetBrains Mono', monospace !important;
}
</style>
