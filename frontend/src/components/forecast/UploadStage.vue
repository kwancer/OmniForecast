<template>
  <IntentProgressView v-if="store.loading" />
  <v-container v-else class="fill-height d-flex flex-column pa-0" fluid>
    <div class="d-flex align-center px-4 py-4 w-100 bg-surface border-b">
      <div class="ml-2">
        <h2 class="text-h6 font-weight-bold font-header mb-0">Start Prediction</h2>
      </div>
      <v-spacer />

      <div class="text-caption text-medium-emphasis mr-4 text-right hidden-sm-and-down">
        Upload data to begin
      </div>

      <!-- Sample data shortcut in the header when no file is loaded -->
      <v-btn
        v-if="!file"
        class="mr-3 hover-lift"
        color="secondary"
        prepend-icon="mdi-auto-fix"
        size="small"
        variant="tonal"
        @click="store.loadSampleData"
      >
        Try Sample Data
      </v-btn>

      <v-btn
        class="ml-2 hover-lift font-weight-bold"
        color="primary"
        :disabled="!file || !intent"
        elevation="0"
        :loading="store.loading"
        variant="flat"
        @click="store.analyzeIntent"
      >
        Continue
        <v-icon end>mdi-chevron-right</v-icon>
      </v-btn>
    </div>

    <v-row class="flex-grow-1 ma-0 w-100 bg-background overflow-hidden">
      <v-col class="h-100 overflow-y-auto pa-6 d-flex justify-center" cols="12">
        <div style="max-width: 1000px; width: 100%;">

          <div class="text-center mb-8 mt-2">
            <h1 class="text-h3 font-weight-bold font-header">What would you like to forecast?</h1>
            <p class="text-body-1 text-medium-emphasis mt-2">Just upload your CSV data and explain below.</p>
          </div>

          <div class="platform-briefing mb-8">
            <div class="d-flex align-center justify-space-between px-4 py-2">
              <div class="d-flex align-center">
                <v-icon class="mr-3" color="primary" icon="mdi-information-outline" size="18" />
                <span class="text-caption font-weight-medium text-medium-emphasis">
                  We use AI to interpret your goals and statistical models to execute them.
                </span>
              </div>
              <v-btn
                class="text-decoration-underline font-weight-bold"
                color="primary"
                size="x-small"
                variant="text"
                @click="showIntegrityDetail = !showIntegrityDetail"
              >
                {{ showIntegrityDetail ? 'Show less' : 'Learn more' }}
              </v-btn>
            </div>
            <v-expand-transition>
              <div v-if="showIntegrityDetail" class="px-4 pb-4">
                <div class="text-caption pt-2 border-t opacity-80" style="line-height: 1.5; color: rgba(var(--v-theme-on-surface), 1);">
                  Unlike chat-based LLMs that generate code on-the-fly, OmniForecast uses proven deterministic algorithms for modeling. This ensures your forecasts are statistically sound, reproducible, and grounded in your historical data.
                </div>
              </div>
            </v-expand-transition>
          </div>

          <!-- FILE + INTENT INPUTS -->
          <v-card class="pa-5 pa-md-6 mb-6 upload-card" variant="outlined">
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

            <!-- File stats strip (appears after file is selected) -->
            <v-expand-transition>
              <div v-if="fileStats" class="d-flex align-center flex-wrap mt-3 gap-3">
                <v-chip color="primary" prepend-icon="mdi-file-delimited" size="small" variant="tonal">
                  {{ fileStats.name }}
                </v-chip>
                <v-chip prepend-icon="mdi-weight" size="small" variant="outlined">
                  {{ fileStats.sizeLabel }}
                </v-chip>
                <v-chip v-if="fileStats.rowCount" prepend-icon="mdi-table-row" size="small" variant="outlined">
                  ~{{ fileStats.rowCount.toLocaleString() }} rows
                </v-chip>
                <v-chip v-if="fileStats.colCount" prepend-icon="mdi-table-column" size="small" variant="outlined">
                  {{ fileStats.colCount }} columns
                </v-chip>
              </div>
            </v-expand-transition>

            <div class="d-flex justify-end mt-3 mb-4">
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
              class="w-100"
              color="primary"
              hint="Describe what you want to predict in plain English."
              persistent-hint
              placeholder="e.g. Forecast sales for the next 12 months, focusing on seasonal trends..."
              prepend-icon="mdi-text-box-search-outline"
              rows="4"
            />
          </v-card>

          <!-- DATA PREVIEW -->
          <v-expand-transition>
            <div v-if="previewData" class="mt-2">
              <div class="d-flex align-center mb-4">
                <h3 class="text-subtitle-1 font-weight-bold">Data Preview</h3>
                <v-chip class="ml-3" size="x-small" variant="outlined">First {{ previewData.rows.length }} Rows</v-chip>
              </div>

              <v-card class="preview-card overflow-hidden" variant="outlined">
                <v-table density="compact" hover>
                  <thead class="bg-surface-light">
                    <tr>
                      <th
                        v-for="h in previewData.headers"
                        :key="h"
                        class="font-weight-bold font-mono text-no-wrap text-medium-emphasis"
                        style="background: var(--v-theme-surface-light) !important;"
                      >
                        {{ h }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in previewData.rows" :key="i">
                      <td
                        v-for="(val, j) in row"
                        :key="j"
                        class="text-caption text-no-wrap font-mono text-medium-emphasis"
                      >
                        {{ val }}
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card>
            </div>
          </v-expand-transition>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import IntentProgressView from './IntentProgressView.vue'

  const store = useForecastStore()

  const file = computed({
    get: () => store.file,
    set: val => store.setFile(val),
  })

  const intent = computed({
    get: () => store.intent,
    set: val => store.setIntent(val),
  })

  // State for the "Learn more" alert toggle
  const showIntegrityDetail = ref(false)

  // ─── File Stats ───
  interface FileStats {
    name: string
    sizeLabel: string
    rowCount: number | null
    colCount: number | null
  }

  const fileStats = ref<FileStats | null>(null)

  function formatFileSize (bytes: number): string {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  // ─── Preview Data ───
  interface PreviewData {
    headers: string[]
    rows: string[][]
  }

  const previewData = ref<PreviewData | null>(null)

  // Simple CSV parser
  function parseCSVLine (line: string): string[] {
    const result: string[] = []
    let current = ''
    let inQuotes = false

    for (const char of line) {
      if (char === '"') {
        inQuotes = !inQuotes
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim())
        current = ''
      } else {
        current += char
      }
    }
    result.push(current.trim())
    return result
  }

  watch(file, async newFile => {
    if (!newFile) {
      previewData.value = null
      fileStats.value = null
      return
    }

    const maxFileSize = 10 * 1024 * 1024
    if (newFile.size > maxFileSize) {
      console.warn('File too large for preview')
      fileStats.value = { name: newFile.name, sizeLabel: formatFileSize(newFile.size), rowCount: null, colCount: null }
      previewData.value = null
      return
    }

    const text = await newFile.text()
    if (!text) return

    const lines = text.split('\n').filter(l => l.trim().length > 0)
    if (lines.length === 0) return

    const firstLine = lines[0]
    if (!firstLine) return

    const headers = parseCSVLine(firstLine)
    const rows = lines.slice(1, 6).map(l => parseCSVLine(l))

    fileStats.value = {
      name: newFile.name,
      sizeLabel: formatFileSize(newFile.size),
      rowCount: lines.length - 1,
      colCount: headers.length,
    }

    previewData.value = { headers, rows }
  }, { immediate: true })
</script>

<style scoped>
.font-mono {
  font-family: 'Roboto Mono', monospace;
}

.platform-briefing {
  background: rgba(var(--v-theme-primary), 0.04);
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.upload-card {
  border-color: rgba(var(--v-theme-primary), 0.12) !important;
  transition: border-color 0.3s ease;
}

.upload-card:hover,
.upload-card:focus-within {
  border-color: rgba(var(--v-theme-primary), 0.3) !important;
}

.preview-card {
  border-color: rgba(var(--v-theme-secondary), 0.2) !important;
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02) !important;
}

:deep(thead tr th) {
  border-bottom: 2px solid var(--v-border-color) !important;
}

.gap-3 {
  gap: 8px;
}
</style>
