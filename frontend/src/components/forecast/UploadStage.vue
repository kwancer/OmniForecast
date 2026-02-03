<template>
  <v-container class="bg-background fill-height d-flex flex-column justify-center" fluid>
    <v-row class="flex-grow-0 w-100" justify="center">
      <v-col cols="12" md="8" sm="10">
        <div class="text-center mb-6">
          <h2 class="text-h4 font-header mb-2">Start Prediction</h2>
          <p class="text-body-1 text-medium-emphasis">Upload historical data and define your prediction objective. </p>
        </div>

        <v-alert
          border="start"
          class="mb-6"
          density="compact"
          type="info"
          variant="outlined"
        >
          <div class="text-body-2">
            AI assists in understanding your intent and converting it into a computer-usable format, but all forecasting logic and code execution are deterministic. No code is generated on-the-fly.
          </div>
        </v-alert>

        <div class="d-flex align-center mb-1">
          <v-file-input
            v-model="file"
            accept=".csv"
            class="w-100"
            color="primary"
            hide-details
            label="Historical Data (CSV)"
            prepend-icon="mdi-database"
          />
          <v-tooltip location="top">
            <template #activator="{ props }">
              <v-icon v-bind="props" class="ml-2" color="medium-emphasis">mdi-help-circle-outline</v-icon>
            </template>
            <span>Upload a CSV file containing at least one date column and one numeric value column.</span>
          </v-tooltip>
        </div>

        <div class="d-flex justify-end mb-4">
          <v-btn
            class="text-none"
            color="secondary"
            prepend-icon="mdi-auto-fix"
            size="small"
            variant="text"
            @click="store.loadSampleData"
          >
            Try with Sample Sales Data
          </v-btn>
        </div>

        <v-textarea
          v-model="intent"
          class="w-100 mb-6"
          color="primary"
          hint="Describe what you want to predict in plain English."
          persistent-hint
          placeholder="e.g. Forecast sales for the next 12 months, focusing on seasonal trends..."
          prepend-icon="mdi-text-box-search-outline"
          rows="4"
        />

        <v-btn
          block
          color="primary"
          :disabled="!file || !intent"
          elevation="2"
          :loading="store.loading"
          size="x-large"
          @click="store.analyzeIntent"
        >
          Continue
          <v-icon end>mdi-chevron-right</v-icon>
        </v-btn>

        <!-- DATA X-RAY PREVIEW -->
        <v-expand-transition>
          <div v-if="previewData" class="mt-8">
            <div class="d-flex align-center mb-4">
              <v-icon class="mr-2" color="primary">mdi-magnify-scan</v-icon>
              <h3 class="text-h6 font-weight-bold">Data X-Ray Preview</h3>
              <v-chip class="ml-3" size="x-small" variant="outlined">First 5 Rows</v-chip>
            </div>

            <v-row>
              <v-col cols="12" md="8">
                <v-card class="border-secondary-light overflow-hidden" variant="outlined">
                  <v-table density="compact">
                    <thead>
                      <tr>
                        <th v-for="h in previewData.headers" :key="h" class="text-caption font-weight-bold text-no-wrap">
                          {{ h }}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, i) in previewData.rows" :key="i">
                        <td v-for="(val, j) in row" :key="j" class="text-caption text-no-wrap font-mono">
                          {{ val }}
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card class="pa-4 border-primary h-100" variant="outlined">
                  <div class="text-overline mb-2">Signal Overview</div>
                  <div v-if="previewData.sparklineData.length > 0" class="sparkline-container">
                    <svg height="80" preserveAspectRatio="none" viewBox="0 0 100 100" width="100%">
                      <path
                        :d="sparklinePath"
                        fill="none"
                        stroke="rgb(var(--v-theme-primary))"
                        stroke-width="2"
                      />
                    </svg>
                    <div class="d-flex justify-space-between mt-2">
                      <span class="text-caption text-medium-emphasis">Start</span>
                      <span class="text-caption text-medium-emphasis">End</span>
                    </div>
                  </div>
                  <div v-else class="text-caption text-medium-emphasis d-flex flex-column align-center justify-center h-100">
                    <v-icon class="mb-2">mdi-chart-bell-curve-cumulative</v-icon>
                    No numeric trend detected
                  </div>
                </v-card>
              </v-col>
            </v-row>
          </div>
        </v-expand-transition>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'

  const store = useForecastStore()

  const file = computed({
    get: () => store.file,
    set: val => store.setFile(val),
  })

  const intent = computed({
    get: () => store.intent,
    set: val => store.setIntent(val),
  })

  interface PreviewData {
    headers: string[]
    rows: string[][]
    sparklineData: number[]
  }

  const previewData = ref<PreviewData | null>(null)

  watch(file, async (newFile) => {
    if (!newFile) {
      previewData.value = null
      return
    }

    const text = await newFile.text()
    if (!text) return

    const lines = text.split('\n').filter(l => l.trim().length > 0)
    if (lines.length === 0) return

    const headers = lines[0].split(',').map(h => h.trim())
    const rows = lines.slice(1, 6).map(l => l.split(',').map(v => v.trim()))

    // Heuristic for sparkline: find first numeric column that isn't the first one (often ID/Date)
    let targetIdx = -1
    const firstRow = rows[0]
    if (firstRow) {
      for (let i = 1; i < headers.length; i++) {
        const valStr = firstRow[i]
        if (valStr) {
          const val = parseFloat(valStr)
          if (!Number.isNaN(val)) {
            targetIdx = i
            break
          }
        }
      }
    }
    // Fallback to first column if no others found
    if (targetIdx === -1) targetIdx = 0

    const sparklineData: number[] = []
    // Sample up to 50 points for sparkline
    const sampleStep = Math.max(1, Math.floor(lines.length / 50))
    for (let i = 1; i < lines.length; i += sampleStep) {
      const line = lines[i]
      if (line) {
        const parts = line.split(',')
        const valStr = parts[targetIdx]
        if (valStr) {
          const val = parseFloat(valStr)
          if (!Number.isNaN(val)) {
            sparklineData.push(val)
          }
        }
      }
    }

    previewData.value = { headers, rows, sparklineData }
  }, { immediate: true })

  const sparklinePath = computed(() => {
    if (!previewData.value || previewData.value.sparklineData.length < 2) return ''
    const data = previewData.value.sparklineData
    const min = Math.min(...data)
    const max = Math.max(...data)
    const range = max - min || 1

    const width = 100
    const height = 100
    const stepX = width / (data.length - 1)

    return data.map((val, i) => {
      const x = i * stepX
      const y = height - ((val - min) / range) * height
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`
    }).join(' ')
  })
</script>

<style scoped>
.font-mono {
  font-family: 'Roboto Mono', monospace;
}
.sparkline-container {
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 4px;
  padding: 8px;
}
.border-secondary-light {
  border-color: rgba(var(--v-theme-secondary), 0.2) !important;
}
.border-primary {
  border-color: rgb(var(--v-theme-primary)) !important;
}
</style>
