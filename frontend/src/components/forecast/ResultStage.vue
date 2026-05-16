<template>
  <v-container class="fill-height d-flex flex-column pa-0" fluid>
    <!-- Header bar -->
    <div class="d-flex align-center px-4 py-4 w-100 bg-surface border-b">
      <v-btn
        class="hover-lift"
        icon="mdi-arrow-left"
        size="small"
        variant="tonal"
        @click="store.setStep('plan')"
      />
      <div class="ml-4">
        <h2 class="text-h6 font-weight-bold font-header mb-0">Step 3: Forecast</h2>
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

    <!-- Main scrollable content -->
    <v-row class="flex-grow-1 ma-0 w-100 bg-background overflow-hidden">
      <v-col class="h-100 overflow-y-auto pa-6" cols="12">

        <!-- ═══ HERO SCORE ═══ -->
        <DataHealthCard :data-health-report="store.dataHealthReport" mode="hero" />

        <!-- ═══ MAIN CONTENT SPLIT ═══ -->
        <v-row class="mt-6 content-split" style="min-height: 0; flex-wrap: nowrap;">

          <!-- LEFT: Chart + Quick Actions -->
          <v-col class="d-flex flex-column" cols="12" md="8" style="gap: 16px;">
            <div class="chart-container" style="height: 620px; width: 100%;">
              <ForecastChart />
            </div>

            <!-- Quick Actions Bar -->
            <v-card class="quick-actions-bar pa-3 d-flex align-center flex-wrap" rounded="lg" variant="outlined">
              <span class="text-caption text-medium-emphasis mr-3 hidden-xs">Your forecast data</span>
              <v-btn
                color="primary"
                prepend-icon="mdi-table-eye"
                size="small"
                variant="tonal"
                @click="showForecastValuesDialog = true"
              >
                View values
              </v-btn>
              <v-btn
                class="ml-2"
                color="primary"
                prepend-icon="mdi-content-copy"
                size="small"
                variant="text"
                @click="copyForecastTable"
              >
                Copy
              </v-btn>
              <v-btn
                class="ml-2"
                color="primary"
                prepend-icon="mdi-download"
                size="small"
                variant="text"
                @click="downloadForecastCSV"
              >
                Download CSV
              </v-btn>
              <v-divider class="mx-3 hidden-xs" vertical />
              <v-btn
                class="ml-auto"
                color="secondary"
                prepend-icon="mdi-lightbulb-outline"
                size="small"
                variant="text"
                @click="showTechnicalSheet = true"
              >
                Show reasoning
              </v-btn>
            </v-card>
          </v-col>

          <!-- RIGHT: AI Assistant -->
          <v-col class="d-flex flex-column ai-column" cols="12" md="4" style="gap: 16px; overflow: hidden;">
            <div class="insight-card insight-card--secondary flex-grow-1 d-flex flex-column ai-card">
              <div class="insight-card__header mb-2">
                <div class="panel-icon panel-icon--secondary mr-3">
                  <v-icon color="white" size="16">mdi-robot-excited-outline</v-icon>
                </div>
                <span class="font-weight-bold">AI Assistant</span>
              </div>

              <div ref="chatThreadRef" class="chat-thread flex-grow-1">
                <!-- Loading state -->
                <div v-if="store.explainabilityMessages.length === 0" class="chat-msg chat-msg--assistant">
                  <div class="typing-indicator">
                    <span /><span /><span />
                  </div>
                  <div class="text-caption text-medium-emphasis mt-1">Analysing your forecast…</div>
                </div>

                <div
                  v-for="(msg, i) in store.explainabilityMessages"
                  :key="i"
                  :class="['chat-msg', msg.role === 'assistant' ? 'chat-msg--assistant' : 'chat-msg--user']"
                >
                  <div class="text-caption font-weight-bold mb-1">
                    {{ msg.role === 'assistant' ? 'AI Assistant' : 'You' }}
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
                  <div v-if="msg.evidence && msg.evidence.length > 0" class="mt-2">
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

              <div v-if="topSuggestions.length > 0" class="mt-3">
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
                  color="secondary"
                  :disabled="!question.trim() || store.askingExplainability"
                  icon
                  :loading="store.askingExplainability"
                  variant="flat"
                  @click="submitQuestion()"
                >
                  <v-icon>mdi-send</v-icon>
                </v-btn>
              </div>
            </div>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>

  <!-- Technical Details Bottom Sheet -->
  <TechnicalDetailsSheet v-model="showTechnicalSheet" />

  <!-- Forecast Values Dialog -->
  <v-dialog v-model="showForecastValuesDialog" max-width="800" scrollable>
    <v-card rounded="lg">
      <v-card-title class="d-flex align-center pa-4">
        <span class="text-h6 font-weight-bold">Forecast Values</span>
        <v-spacer />
        <v-btn icon="mdi-close" size="small" variant="text" @click="showForecastValuesDialog = false" />
      </v-card-title>
      <v-divider />
      <v-card-text class="pa-0">
        <v-table density="compact" fixed-header height="500px">
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
      </v-card-text>
      <v-divider />
      <v-card-actions class="pa-4">
        <v-btn color="primary" prepend-icon="mdi-content-copy" variant="tonal" @click="copyForecastTable">
          Copy to clipboard
        </v-btn>
        <v-btn color="primary" prepend-icon="mdi-download" variant="text" @click="downloadForecastCSV">
          Download CSV
        </v-btn>
        <v-spacer />
        <v-btn variant="text" @click="showForecastValuesDialog = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
  import { marked } from 'marked'
  import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
  import { useAppStore } from '@/stores/app'
  import { useForecastStore } from '@/stores/forecast'
  import { formatNumber } from '@/utils/formatters'
  import DataHealthCard from './DataHealthCard.vue'
  import ForecastChart from './ForecastChart.vue'
  import TechnicalDetailsSheet from './TechnicalDetailsSheet.vue'

  // Configure marked for safe, minimal output
  marked.setOptions({ breaks: true, gfm: true })

  const store = useForecastStore()

  const question = ref('')
  const chatThreadRef = ref<HTMLElement | null>(null)
  const expandedEvidence = reactive(new Set<number>())
  const topSuggestions = computed(() => store.suggestedQuestions.slice(0, 3))

  // New layout state
  const showForecastValuesDialog = ref(false)
  const showTechnicalSheet = ref(false)

  // (Technical details logic moved to TechnicalDetailsSheet.vue)

  const askedQuestions = computed(() => {
    const asked = new Set<string>()
    for (const msg of store.explainabilityMessages) {
      if (msg.role === 'user') {
        asked.add(msg.content.trim().toLowerCase())
      }
    }
    return asked
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
  })

  watch(
    () => store.explainabilityMessages.map(m => m.content.length).join(','),
    async () => {
      await scrollChatToBottom()
    },
  )

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

  const appStore = useAppStore()

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

/* ─── Chart Container ─── */
.chart-container {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-theme-primary), 0.08);
  background: rgb(var(--v-theme-surface));
}

/* ─── Quick Actions Bar ─── */
.quick-actions-bar {
  background: rgb(var(--v-theme-surface)) !important;
  border: 1px solid rgba(var(--v-theme-primary), 0.08) !important;
  gap: 8px;
}

/* ─── Content Split Row ─── */
.content-split {
  /* Height = chart (620px) + quick-actions (~56px) + gap (16px) */
  height: 692px;
  max-height: 692px;
  align-items: stretch !important;
  overflow: hidden;
}

.content-split > .v-col {
  min-height: 0;
  max-height: 100%;
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

/* ─── Chat Thread ─── */
.chat-thread {
  min-height: 200px;
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

/* ─── AI Column height matches left side ─── */
.ai-column {
  align-self: stretch;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
}

.ai-card {
  overflow: hidden;
  min-height: 0;
  max-height: 100%;
}

/* Ensure chat thread can shrink and scrolls internally */
.chat-thread {
  min-height: 0 !important;
}
</style>
