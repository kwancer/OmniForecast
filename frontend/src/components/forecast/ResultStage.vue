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
              <DataHealthCard v-if="!isAlternativeUi" :data-health-report="store.dataHealthReport" />

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
                          <v-table v-if="currentData.headers.length > 0" density="compact" fixed-header hover style="background: transparent;">
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
              
              <!-- Scenario Builder -->
              <div class="insight-card insight-card--secondary mb-5">
                <div class="insight-card__header mb-4">
                  <div class="panel-icon panel-icon--success mr-3">
                    <v-icon color="white" size="16">mdi-tune-variant</v-icon>
                  </div>
                  <span class="font-weight-bold">Scenario Builder</span>
                </div>
                <ScenarioBuilder @recalculate="store.executeForecast()" />
              </div>

              <!-- AI Explainability Layer -->
              <div class="insight-card insight-card--secondary mb-5">
                <div class="insight-card__header">
                  <div class="panel-icon panel-icon--secondary mr-3">
                    <v-icon color="white" size="16">mdi-robot-excited-outline</v-icon>
                  </div>
                  <span class="font-weight-bold">AI Explainability Layer</span>
                </div>

                <div ref="chatThreadRef" class="chat-thread mt-3">
                  <!-- Loading state -->
                  <div v-if="store.explainabilityMessages.length === 0" class="chat-msg chat-msg--assistant">
                    <div class="typing-indicator">
                      <span /><span /><span />
                    </div>
                    <div class="text-caption text-medium-emphasis mt-1">Analyzing your forecast…</div>
                  </div>

                  <div
                    v-for="(msg, i) in store.explainabilityMessages"
                    :key="i"
                    :class="['chat-msg', msg.role === 'assistant' ? 'chat-msg--assistant' : 'chat-msg--user']"
                  >
                    <div class="text-caption font-weight-bold mb-1">
                      {{ msg.role === 'assistant' ? 'AI Analyst' : 'You' }}
                    </div>

                    <!-- Typing indicator when assistant message is still empty -->
                    <div v-if="msg.role === 'assistant' && !msg.content && store.askingExplainability" class="typing-indicator">
                      <span /><span /><span />
                    </div>
                    <div
                      v-else-if="msg.role === 'assistant'"
                      class="chat-md-body text-body-2"
                      v-html="renderMarkdown(msg.content)"
                    />
                    <div v-else class="text-body-2" style="white-space: pre-line; line-height: 1.5;">{{ msg.content }}</div>

                    <!-- Evidence disclosure -->
                    <div v-if="msg.evidence && msg.evidence.length" class="mt-2">
                      <v-btn
                        class="text-caption"
                        density="compact"
                        prepend-icon="mdi-link-variant"
                        size="small"
                        variant="text"
                        @click="toggleEvidence(i)"
                      >
                        {{ expandedEvidence.has(i) ? 'Hide' : 'View' }} sources ({{ msg.evidence.length }})
                      </v-btn>
                      <div v-if="expandedEvidence.has(i)" class="evidence-list mt-1">
                        <div v-for="(ev, j) in msg.evidence" :key="`ev-${j}`" class="evidence-chip">
                          <div class="evidence-chip__source">{{ ev.source }}</div>
                          <div class="evidence-chip__detail">{{ ev.detail }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-if="topSuggestions.length" class="mt-3">
                  <v-chip
                    v-for="(suggestion, i) in topSuggestions"
                    :key="`s-${i}`"
                    :class="['mr-1', 'mb-1', { 'suggestion-asked': askedQuestions.has(suggestion.toLowerCase()) }]"
                    :disabled="askedQuestions.has(suggestion.toLowerCase())"
                    size="small"
                    variant="outlined"
                    @click="submitQuestion(suggestion)"
                  >
                    {{ suggestion }}
                  </v-chip>
                </div>

                <div class="chat-input-row mt-3">
                  <v-text-field
                    v-model="question"
                    class="chat-input"
                    density="compact"
                    hide-details
                    placeholder="Ask about reliability, risk, model choice, assumptions…"
                    variant="outlined"
                    @keydown.enter.prevent="submitQuestion()"
                  />
                  <v-btn
                    class="chat-send-btn"
                    :disabled="!question.trim() || store.askingExplainability"
                    :loading="store.askingExplainability"
                    color="secondary"
                    icon
                    variant="flat"
                    @click="submitQuestion()"
                  >
                    <v-icon>mdi-send</v-icon>
                  </v-btn>
                </div>
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
  import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
  import { marked } from 'marked'
  import { useForecastStore } from '@/stores/forecast'
  import BacktestChart from './BacktestChart.vue'
  import DataHealthCard from './DataHealthCard.vue'
  import ForecastChart from './ForecastChart.vue'
  import ModelTournament from './ModelTournament.vue'
  import ScenarioBuilder from './ScenarioBuilder.vue'

  // Configure marked for safe, minimal output
  marked.setOptions({ breaks: true, gfm: true })

  const store = useForecastStore()
  const isAlternativeUi = import.meta.env.VITE_ALTERNATIVE_UI === 'true'

  const question = ref('')
  const chatThreadRef = ref<HTMLElement | null>(null)
  const expandedEvidence = reactive(new Set<number>())
  const topSuggestions = computed(() => store.suggestedQuestions.slice(0, 3))

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

  function getActionIcon (action: string) {
    switch (action) {
      case 'normalization': return 'mdi-format-letter-case'
      case 'type_conversion': return 'mdi-variable'
      case 'aggregation': return 'mdi-layers-triple'
      case 'resampling': return 'mdi-calendar-clock'
      case 'gap_filling': return 'mdi-plus-box'
      case 'imputation': return 'mdi-eyedropper'
      case 'column_dropping': return 'mdi-table-column-remove'
      default: return 'mdi-wrench'
    }
  }

  function getActionColor (action: string) {
    switch (action) {
      case 'imputation': return 'warning'
      case 'resampling': return 'info'
      case 'gap_filling': return 'secondary'
      case 'type_conversion': return 'primary'
      case 'column_dropping': return 'grey-darken-1'
      default: return 'primary'
    }
  }

  function formatActionName (name: string) {
    return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
  }

  const askedQuestions = computed(() => {
    const asked = new Set<string>()
    for (const msg of store.explainabilityMessages) {
      if (msg.role === 'user') {
        asked.add(msg.content.trim().toLowerCase())
      }
    }
    return asked
  })

  const lastMsgEmpty = computed(() => {
    const msgs = store.explainabilityMessages
    if (msgs.length === 0) return true
    const last = msgs[msgs.length - 1]
    if (!last) return true
    return last.role === 'assistant' && !last.content
  })

  function renderMarkdown (text: string): string {
    if (!text) return ''
    return marked.parse(text, { async: false }) as string
  }

  function toggleEvidence (index: number) {
    if (expandedEvidence.has(index)) {
      expandedEvidence.delete(index)
    } else {
      expandedEvidence.add(index)
    }
  }

  async function scrollChatToBottom () {
    await nextTick()
    if (!chatThreadRef.value) return
    chatThreadRef.value.scrollTop = chatThreadRef.value.scrollHeight
  }

  async function submitQuestion (prefilled?: string) {
    const q = (prefilled ?? question.value).trim()
    if (!q) return
    question.value = ''
    await store.askExplainability(q, true)
    await scrollChatToBottom()
  }

  onMounted(async () => {
    if (store.forecastResults.length > 0 && store.explainabilityMessages.length === 0) {
      await store.initializeExplainability()
    }
    await scrollChatToBottom()

    // CSV Parsing for Cleaning Report
    if (store.file && (store.file.type.includes('csv') || store.file.name.endsWith('.csv'))) {
      try {
        const text = await store.file.slice(0, 10_000).text()
        const lines = text.split(/\r?\n/).filter(l => l.trim().length > 0)
        if (lines.length > 0) {
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

  watch(
    () => store.explainabilityMessages.map(m => m.content.length).join(','),
    async () => {
      await scrollChatToBottom()
    },
  )

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

  // Determine metrics to display based on UI mode
  const displayMetrics = computed(() => {
    if (isAlternativeUi) {
      // Alternative UI: Show traditional metrics (RMSE, MAE, MAPE)
      return store.metrics.filter(m => m.name === 'RMSE' || m.name === 'MAE' || m.name === 'MAPE')
    }
    // Default UI: Filter out RMSE and R² (not used anyway as card is hidden)
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

.chat-thread {
  min-height: 320px;
  max-height: 460px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 6px 8px 2px;
  border-radius: 14px;
  background:
    radial-gradient(circle at 0% 0%, rgba(var(--v-theme-secondary), 0.08), transparent 45%),
    radial-gradient(circle at 100% 100%, rgba(var(--v-theme-primary), 0.08), transparent 45%),
    rgba(var(--v-theme-surface), 0.65);
  border: 1px solid rgba(var(--v-theme-secondary), 0.1);
}

.chat-msg {
  border-radius: 14px;
  padding: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.09);
  box-shadow: 0 8px 24px rgba(16, 24, 40, 0.04);
}

.chat-msg--assistant {
  background: linear-gradient(145deg, rgba(var(--v-theme-secondary), 0.12), rgba(var(--v-theme-secondary), 0.04));
}

.chat-msg--user {
  background: linear-gradient(145deg, rgba(var(--v-theme-primary), 0.12), rgba(var(--v-theme-primary), 0.05));
}

.chat-thread::-webkit-scrollbar {
  width: 8px;
}

.chat-thread::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-primary), 0.25);
  border-radius: 999px;
}

.chat-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-input {
  flex: 1;
}

.chat-send-btn {
  width: 42px;
  height: 42px;
  min-width: 42px;
}

/* ─── Typing Indicator ─── */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(var(--v-theme-secondary), 0.5);
  animation: typingBounce 1.2s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* ─── Evidence Disclosure ─── */
.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.evidence-chip {
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  font-size: 0.75rem;
}

.evidence-chip__source {
  font-weight: 600;
  color: rgba(var(--v-theme-secondary), 1);
  margin-bottom: 2px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-size: 0.65rem;
}

.evidence-chip__detail {
  color: rgba(var(--v-theme-on-surface), 0.65);
  line-height: 1.35;
  word-break: break-word;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
}

/* ─── Markdown Body ─── */
.chat-md-body {
  line-height: 1.55;
}

.chat-md-body :deep(p) {
  margin-bottom: 8px;
}

.chat-md-body :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-md-body :deep(ul),
.chat-md-body :deep(ol) {
  padding-left: 18px;
  margin-bottom: 8px;
}

.chat-md-body :deep(li) {
  margin-bottom: 2px;
}

.chat-md-body :deep(strong) {
  color: rgb(var(--v-theme-secondary));
  font-weight: 700;
}

.chat-md-body :deep(code) {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85em;
  background: rgba(var(--v-theme-on-surface), 0.06);
  padding: 1px 4px;
  border-radius: 4px;
}

/* ─── Suggestion Chips ─── */
.suggestion-asked {
  opacity: 0.35;
  text-decoration: line-through;
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
</style>
