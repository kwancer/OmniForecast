<template>
  <IntentProgressView v-if="store.loading" />
  <v-container v-else class="fill-height d-flex flex-column pa-0" fluid>
    <div class="d-flex align-center px-4 py-4 w-100 bg-surface border-b">
      <div class="ml-2">
        <h2 class="text-h6 font-weight-bold font-header mb-0">Step 1: Upload</h2>
      </div>
      <v-spacer />

      <div class="text-caption text-medium-emphasis mr-4 text-right hidden-sm-and-down">
        Upload data to begin
      </div>

      <!-- Sample data shortcut in the header when no file is loaded -->
      <v-menu v-if="!file" open-on-hover>
        <template #activator="{ props }">
          <v-btn
            v-bind="props"
            class="mr-3 hover-lift"
            color="secondary"
            prepend-icon="mdi-auto-fix"
            size="small"
            variant="tonal"
          >
            Try with sample data
            <v-icon end>mdi-chevron-down</v-icon>
          </v-btn>
        </template>
        <v-list class="elevation-3 rounded-lg" max-width="400" min-width="320">
          <v-list-subheader class="text-uppercase font-weight-bold text-caption">Available Datasets</v-list-subheader>
          <v-list-item
            v-for="ds in sampleDatasets"
            :key="ds.filename"
            class="mb-1"
            link
            @click="store.loadSampleData(ds.filename, ds.goal)"
          >
            <v-list-item-title class="font-weight-bold text-body-2">{{ ds.title }}</v-list-item-title>
            <div class="text-caption mt-1" style="line-height: 1.3; opacity: 0.8;">
              {{ ds.description }}
            </div>
          </v-list-item>
        </v-list>
      </v-menu>

      <v-btn
        class="ml-2 hover-lift font-weight-bold"
        color="primary"
        :disabled="!file || !intent"
        elevation="0"
        :loading="store.loading"
        variant="flat"
        @click="store.analyzeIntent()"
      >
        Continue
        <v-icon end>mdi-chevron-right</v-icon>
      </v-btn>
    </div>

    <v-row class="flex-grow-1 ma-0 w-100 bg-background overflow-hidden">
      <v-col class="h-100 overflow-y-auto pa-6 d-flex justify-center" cols="12">
        <div style="max-width: 860px; width: 100%;">

          <!-- Hero Heading -->
          <div class="text-center mb-8 mt-4">
            <h1 class="text-h3 font-weight-bold font-header hero-heading">What would you like to forecast?</h1>
            <p class="text-body-1 text-medium-emphasis mt-3" style="max-width: 520px; margin: 0 auto;">
              Upload your time-series data and describe your goal — we handle the rest.
            </p>
          </div>

          <!-- Platform Briefing -->
          <div class="platform-briefing mb-8">
            <div class="d-flex align-center justify-space-between px-4 py-2">
              <div class="d-flex align-center">
                <v-icon class="mr-3" color="primary" icon="mdi-shield-check-outline" size="18" />
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
                  Unlike chat-based LLMs that generate code on-the-fly, AskForecast uses proven deterministic algorithms for modeling. This ensures your forecasts are statistically sound, reproducible, and grounded in your historical data.
                </div>
              </div>
            </v-expand-transition>
          </div>

          <div class="input-area">

            <div class="d-flex flex-wrap upload-paste-row">
              <!-- CSV Upload -->
              <div v-if="!pasteActive" class="upload-col">
                <div
                  class="dropzone"
                  :class="{
                    'dropzone--active': isDragOver,
                    'dropzone--has-file': !!file,
                  }"
                  @click="triggerFileInput"
                  @dragenter.prevent="onDragEnter"
                  @dragleave.prevent="onDragLeave"
                  @dragover.prevent
                  @drop.prevent="onDrop"
                >
                  <!-- Hidden native file input -->
                  <input
                    ref="fileInputRef"
                    accept=".csv"
                    style="display: none"
                    type="file"
                    @change="onFileInputChange"
                  >

                  <!-- Empty state -->
                  <div v-if="!file" class="dropzone__empty">
                    <div class="dropzone__icon-wrap">
                      <v-icon
                        class="dropzone__icon"
                        :class="{ 'dropzone__icon--pulse': isDragOver }"
                        :color="isDragOver ? 'primary' : 'medium-emphasis'"
                        size="48"
                      >
                        mdi-cloud-upload-outline
                      </v-icon>
                    </div>
                    <div class="mt-4 d-flex align-center justify-center">
                      <span class="text-body-1 font-weight-bold" :class="isDragOver ? 'text-primary' : ''">
                        {{ isDragOver ? 'Drop your file here' : 'Drag & drop your CSV file' }}
                      </span>
                      <v-tooltip location="top" max-width="300" open-delay="200">
                        <template #activator="{ props }">
                          <v-icon
                            v-bind="props"
                            class="ml-2 mb-1 opacity-80"
                            color="medium-emphasis"
                            size="18"
                            @click.stop
                          >
                            mdi-information-outline
                          </v-icon>
                        </template>
                        <div class="text-caption" style="line-height: 1.5;">
                          <div class="font-weight-bold mb-1 text-white">CSV Requirements:</div>
                          <ul class="pl-4 mb-0">
                            <li>Standard comma-separated values</li>
                            <li>Vertical layout (rows = time steps, columns = variables)</li>
                            <li>Requires a date/time column (any date format works)</li>
                          </ul>
                        </div>
                      </v-tooltip>
                    </div>
                    <div class="mt-1 text-caption text-medium-emphasis">
                      or <span class="text-primary font-weight-bold cursor-pointer">browse files</span> — CSV up to 10 MB
                    </div>
                  </div>

                  <!-- File loaded state -->
                  <div v-else class="dropzone__loaded">
                    <div class="d-flex align-center">
                      <div class="file-icon-wrap mr-4">
                        <v-icon color="primary" size="28">mdi-file-delimited-outline</v-icon>
                      </div>
                      <div class="flex-grow-1">
                        <div class="d-flex align-center mb-1">
                          <span class="text-body-2 font-weight-bold text-truncate" style="max-width: 300px;">{{ fileStats?.name }}</span>
                          <v-chip
                            class="ml-2"
                            color="success"
                            prepend-icon="mdi-check-circle"
                            size="x-small"
                            variant="tonal"
                          >Loaded</v-chip>
                        </div>
                        <div class="d-flex align-center flex-wrap file-meta-row">
                          <span v-if="fileStats?.sizeLabel" class="file-meta-item">
                            <v-icon size="12">mdi-weight</v-icon> {{ fileStats.sizeLabel }}
                          </span>
                          <span v-if="fileStats?.rowCount" class="file-meta-item">
                            <v-icon size="12">mdi-table-row</v-icon> {{ formatNumber(fileStats.rowCount) }} rows
                          </span>
                          <span v-if="fileStats?.colCount" class="file-meta-item">
                            <v-icon size="12">mdi-table-column</v-icon> {{ fileStats.colCount }} cols
                          </span>
                        </div>
                      </div>
                      <v-btn
                        color="error"
                        icon="mdi-close"
                        size="small"
                        variant="text"
                        @click.stop="clearFile"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Excel Paste -->
              <div v-if="!file || pasteActive" class="paste-col">
                <div
                  class="paste-zone"
                  :class="{ 'paste-zone--active': pasteActive }"
                >
                  <div v-if="!pasteActive" class="paste-zone__empty">
                    <div class="paste-zone__icon-wrap">
                      <v-icon color="medium-emphasis" size="36">mdi-table-arrow-right</v-icon>
                    </div>
                    <div class="mt-3 text-body-1 font-weight-bold text-medium-emphasis">
                      Or paste straight from Excel
                    </div>
                    <div class="mt-1 text-caption text-medium-emphasis">
                      Copy cells in Excel and paste here
                    </div>
                    <textarea
                      ref="pasteTextareaRef"
                      v-model="pasteText"
                      class="paste-textarea mt-3"
                      placeholder="Paste your copied Excel cells here..."
                      rows="4"
                      @paste="onExcelPaste"
                    />
                  </div>
                  <div v-else class="paste-zone__loaded">
                    <div class="d-flex align-center">
                      <div class="file-icon-wrap mr-4">
                        <v-icon color="success" size="28">mdi-table-check</v-icon>
                      </div>
                      <div class="flex-grow-1">
                        <div class="d-flex align-center mb-1">
                          <span class="text-body-2 font-weight-bold">Pasted from Excel</span>
                          <v-chip
                            class="ml-2"
                            color="success"
                            prepend-icon="mdi-check-circle"
                            size="x-small"
                            variant="tonal"
                          >Loaded</v-chip>
                        </div>
                        <div class="d-flex align-center flex-wrap file-meta-row">
                          <span v-if="fileStats?.rowCount" class="file-meta-item">
                            <v-icon size="12">mdi-table-row</v-icon> {{ formatNumber(fileStats.rowCount) }} rows
                          </span>
                          <span v-if="fileStats?.colCount" class="file-meta-item">
                            <v-icon size="12">mdi-table-column</v-icon> {{ fileStats.colCount }} cols
                          </span>
                        </div>
                      </div>
                      <v-btn
                        color="error"
                        icon="mdi-close"
                        size="small"
                        variant="text"
                        @click.stop="clearPaste"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Sample Data Link (contextual, only when no file) -->
            <transition name="fade-up">
              <div v-if="!file" class="text-center mt-3 mb-2">
                <v-menu open-on-hover>
                  <template #activator="{ props }">
                    <v-btn
                      v-bind="props"
                      class="text-none"
                      color="secondary"
                      prepend-icon="mdi-auto-fix"
                      size="small"
                      variant="text"
                    >
                      Or try with sample data
                      <v-icon end>mdi-chevron-down</v-icon>
                    </v-btn>
                  </template>
                  <v-list class="elevation-3 rounded-lg" max-width="400" min-width="320">
                    <v-list-subheader class="text-uppercase font-weight-bold text-caption">Available Datasets</v-list-subheader>
                    <v-list-item
                      v-for="ds in sampleDatasets"
                      :key="ds.filename"
                      class="mb-1"
                      link
                      @click="store.loadSampleData(ds.filename, ds.goal)"
                    >
                      <v-list-item-title class="font-weight-bold text-body-2">{{ ds.title }}</v-list-item-title>
                      <div class="text-caption mt-1" style="line-height: 1.3; opacity: 0.8;">
                        {{ ds.description }}
                      </div>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </div>
            </transition>

            <!-- DATA PREVIEW -->
            <v-expand-transition>
              <div v-if="previewData" class="mt-6">
                <div class="d-flex align-center mb-2">
                  <v-icon class="mr-2" color="secondary" size="18">mdi-table-eye</v-icon>
                  <span class="text-caption font-weight-bold text-uppercase" style="letter-spacing: 1px;">Data Preview</span>
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

            <div class="intent-input-wrap mt-6">
              <div class="intent-input-label d-flex align-center mb-2">
                <v-icon class="mr-2" color="primary" size="18">mdi-message-text-outline</v-icon>
                <span class="text-caption font-weight-bold text-uppercase" style="letter-spacing: 1px;">Your Forecast Goal</span>
              </div>
              <div class="intent-box" :class="{ 'intent-box--focused': isIntentFocused }">
                <textarea
                  ref="intentTextareaRef"
                  v-model="intentValue"
                  class="intent-textarea"
                  placeholder="e.g. Forecast monthly revenue for the next 12 months, focusing on seasonal trends and growth..."
                  rows="4"
                  @blur="isIntentFocused = false"
                  @focus="isIntentFocused = true"
                />
                <div class="intent-box__footer">
                  <span class="text-caption text-medium-emphasis">
                    <v-icon size="12">mdi-lightbulb-outline</v-icon>
                    Be specific about what to predict, how far ahead, and any patterns to focus on.
                  </span>
                  <span class="text-caption" :class="intentValue.length > 0 ? 'text-primary' : 'text-disabled'">
                    {{ intentValue.length }} chars
                  </span>
                </div>
              </div>
            </div>

            <!-- Second Continue Button -->
            <div class="mt-6 d-flex justify-end">
              <v-btn
                class="hover-lift font-weight-bold"
                color="primary"
                :disabled="!file || !intent"
                elevation="0"
                :loading="store.loading"
                variant="flat"
                @click="store.analyzeIntent()"
              >
                Continue
                <v-icon end>mdi-chevron-right</v-icon>
              </v-btn>
            </div>
          </div>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import { formatFileSize, formatNumber } from '@/utils/formatters'
  import IntentProgressView from './IntentProgressView.vue'

  const store = useForecastStore()

  interface SampleDataset {
    filename: string
    title: string
    goal: string
    description: string
  }

  const sampleDatasets = ref<SampleDataset[]>([])

  onMounted(async () => {
    try {
      const response = await fetch('/datasets/samples.json')
      if (response.ok) {
        sampleDatasets.value = await response.json()
      }
    } catch (error) {
      console.error('Failed to load sample datasets', error)
    }
  })

  const file = computed({
    get: () => store.file,
    set: val => store.setFile(val),
  })

  const intent = computed({
    get: () => store.intent,
    set: val => store.setIntent(val),
  })

  // Local intent value for textarea (syncs with store)
  const intentValue = ref(intent.value || '')
  watch(intentValue, val => {
    intent.value = val
  })
  watch(intent, val => {
    if (val !== intentValue.value) intentValue.value = val || ''
  })

  // State for the "Learn more" alert toggle
  const showIntegrityDetail = ref(false)

  const isDragOver = ref(false)
  const fileInputRef = ref<HTMLInputElement | null>(null)
  const isIntentFocused = ref(false)
  let dragCounter = 0

  function triggerFileInput () {
    fileInputRef.value?.click()
  }

  function onFileInputChange (e: Event) {
    const target = e.target as HTMLInputElement
    if (target.files && target.files[0]) {
      pasteActive.value = false
      pasteText.value = ''
      file.value = target.files[0]
    }
  }

  function onDragEnter () {
    dragCounter++
    isDragOver.value = true
  }

  function onDragLeave () {
    dragCounter--
    if (dragCounter <= 0) {
      isDragOver.value = false
      dragCounter = 0
    }
  }

  function onDrop (e: DragEvent) {
    isDragOver.value = false
    dragCounter = 0
    const droppedFile = e.dataTransfer?.files?.[0]
    if (droppedFile && droppedFile.name.endsWith('.csv')) {
      pasteActive.value = false
      pasteText.value = ''
      file.value = droppedFile
    }
  }

  function clearFile () {
    file.value = null
    pasteActive.value = false
    pasteText.value = ''
    if (fileInputRef.value) fileInputRef.value.value = ''
  }

  const pasteText = ref('')
  const pasteActive = ref(false)

  function onExcelPaste (_e: ClipboardEvent) {
    // Let the paste complete, then process
    setTimeout(() => {
      processPastedText(pasteText.value)
    }, 0)
  }

  function processPastedText (text: string) {
    const trimmed = text.trim()
    if (!trimmed) {
      pasteActive.value = false
      return
    }
    const parsed = parsePastedData(trimmed)
    if (!parsed || parsed.rows.length === 0) {
      pasteActive.value = false
      return
    }
    const csvText = convertToCsv(parsed.headers, parsed.rows)
    const blob = new Blob([csvText], { type: 'text/csv' })
    const newFile = new File([blob], 'pasted_data.csv', { type: 'text/csv' })
    pasteActive.value = true
    file.value = newFile
  }

  function clearPaste () {
    pasteActive.value = false
    pasteText.value = ''
    file.value = null
    previewData.value = null
    fileStats.value = null
  }

  function parsePastedData (text: string): { headers: string[], rows: string[][] } | null {
    const lines = text.split(/\r?\n/).filter(l => l.trim().length > 0)
    if (lines.length === 0) return null

    // Detect delimiter: tab is most common for Excel, but fallback to comma
    const hasTab = lines.some(l => l.includes('\t'))
    const delimiter = hasTab ? '\t' : ','

    const firstLine = lines[0]!
    const headers = firstLine.split(delimiter).map(h => h.trim())
    const rows = lines.slice(1).map(line => {
      const cells = line.split(delimiter).map(c => c.trim())
      return cells
    })

    return { headers, rows }
  }

  function convertToCsv (headers: string[], rows: string[][]): string {
    const escape = (val: string) => {
      if (val.includes(',') || val.includes('"') || val.includes('\n')) {
        return `"${val.replace(/"/g, '""')}"`
      }
      return val
    }
    const csvLines = [
      headers.map(element => escape(element)).join(','),
      ...rows.map(row => row.map(element => escape(element)).join(',')),
    ]
    return csvLines.join('\n')
  }

  interface FileStats {
    name: string
    sizeLabel: string
    rowCount: number | null
    colCount: number | null
  }

  const fileStats = ref<FileStats | null>(null)

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
  font-family: 'JetBrains Mono', 'Roboto Mono', monospace;
}

.hero-heading {
  background: linear-gradient(135deg,
    rgb(var(--v-theme-primary)) 0%,
    rgb(var(--v-theme-secondary)) 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.platform-briefing {
  background: rgba(var(--v-theme-primary), 0.04);
  border: 1px solid rgba(var(--v-theme-primary), 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.input-area {
  background: rgba(var(--v-theme-primary), 0.02);
  border: 1px solid rgba(var(--v-theme-primary), 0.06);
  border-radius: 20px;
  padding: 28px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.input-area:hover {
  border-color: rgba(var(--v-theme-primary), 0.12);
}

.dropzone {
  position: relative;
  border: 2px dashed rgba(var(--v-theme-primary), 0.2);
  border-radius: 16px;
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  background: rgba(var(--v-theme-primary), 0.02);
}

.dropzone:hover {
  border-color: rgba(var(--v-theme-primary), 0.4);
  background: rgba(var(--v-theme-primary), 0.04);
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(var(--v-theme-primary), 0.08);
}

.dropzone--active {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-primary), 0.08) !important;
  transform: translateY(-2px) scale(1.005);
  box-shadow: 0 8px 32px rgba(var(--v-theme-primary), 0.15) !important;
}

.dropzone--has-file {
  border-style: solid;
  border-color: rgba(var(--v-theme-primary), 0.15);
  padding: 20px 24px;
  cursor: default;
  background: rgba(var(--v-theme-primary), 0.03);
}

.dropzone--has-file:hover {
  transform: none;
  box-shadow: none;
}

.dropzone__icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: rgba(var(--v-theme-primary), 0.08);
  transition: all 0.3s ease;
}

.dropzone:hover .dropzone__icon-wrap {
  background: rgba(var(--v-theme-primary), 0.12);
  transform: scale(1.05);
}

.dropzone--active .dropzone__icon-wrap {
  background: rgba(var(--v-theme-primary), 0.18);
  transform: scale(1.1);
}

.dropzone__icon {
  transition: transform 0.3s ease;
}

.dropzone__icon--pulse {
  animation: icon-pulse 1s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.upload-paste-row {
  gap: 16px;
  align-items: stretch;
}

.upload-col,
.paste-col {
  flex: 1 1 0;
  min-width: 280px;
  display: flex;
}

.upload-col .dropzone,
.paste-col .paste-zone {
  width: 100%;
  height: 100%;
}

.paste-zone {
  position: relative;
  border: 2px dashed rgba(var(--v-theme-secondary), 0.2);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  background: rgba(var(--v-theme-secondary), 0.02);
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.paste-zone:hover {
  border-color: rgba(var(--v-theme-secondary), 0.4);
  background: rgba(var(--v-theme-secondary), 0.04);
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(var(--v-theme-secondary), 0.08);
}

.paste-zone--active {
  border-style: solid;
  border-color: rgba(var(--v-theme-success), 0.3);
  background: rgba(var(--v-theme-success), 0.03);
}

.paste-zone__icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(var(--v-theme-secondary), 0.08);
}

.paste-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid rgba(var(--v-theme-secondary), 0.2);
  border-radius: 10px;
  outline: none;
  resize: none;
  font-family: 'JetBrains Mono', 'Roboto Mono', monospace;
  font-size: 0.8rem;
  line-height: 1.4;
  color: rgb(var(--v-theme-on-surface));
  background: rgba(var(--v-theme-surface), 0.8);
}

.paste-textarea:focus {
  border-color: rgb(var(--v-theme-secondary));
  box-shadow: 0 0 0 2px rgba(var(--v-theme-secondary), 0.1);
}

.paste-textarea::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.35);
  font-style: italic;
}

.file-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(var(--v-theme-primary), 0.08);
  flex-shrink: 0;
}

.file-meta-row {
  gap: 12px;
}

.file-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.intent-input-wrap {
  position: relative;
}

.intent-box {
  position: relative;
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  border-radius: 14px;
  overflow: hidden;
  transition: all 0.3s ease;
  background: rgba(var(--v-theme-surface), 1);
}

.intent-box:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.intent-box--focused {
  border-color: rgb(var(--v-theme-primary)) !important;
  box-shadow: 0 0 0 3px rgba(var(--v-theme-primary), 0.1),
              0 4px 16px rgba(var(--v-theme-primary), 0.06);
}

.intent-textarea {
  width: 100%;
  padding: 16px 20px;
  border: none;
  outline: none;
  resize: none;
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  line-height: 1.6;
  color: rgb(var(--v-theme-on-surface));
  background: transparent;
}

.intent-textarea::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.35);
  font-style: italic;
}

.intent-box__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-top: 1px solid rgba(var(--v-theme-primary), 0.06);
  background: rgba(var(--v-theme-primary), 0.02);
}

.preview-card {
  border-color: rgba(var(--v-theme-secondary), 0.2) !important;
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02) !important;
}

:deep(thead tr th) {
  border-bottom: 2px solid var(--v-border-color) !important;
}

.fade-up-enter-active,
.fade-up-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-up-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-up-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
