<template>
  <div class="future-data-grid">
    <!-- Toolbar -->
    <div class="d-flex align-center pa-2 bg-surface-light border-b">
      <v-icon class="mr-2" color="primary" size="16">mdi-table-edit</v-icon>
      <span class="text-caption font-weight-medium">Future values</span>
      <v-spacer />
      <v-chip size="x-small" variant="tonal">{{ horizon }} steps</v-chip>
      <v-tooltip location="top" text="Upload CSV with future values">
        <template #activator="{ props: tProps }">
          <v-btn
            v-bind="tProps"
            class="ml-2"
            density="compact"
            icon="mdi-file-upload-outline"
            size="x-small"
            variant="text"
            @click="triggerFileUpload"
          />
        </template>
      </v-tooltip>
      <input
        ref="fileInput"
        accept=".csv"
        class="d-none"
        type="file"
        @change="handleFileUpload"
      >
    </div>

    <div class="spreadsheet-container">
      <v-table class="compact-table" density="compact" fixed-header hover>
        <thead>
          <tr>
            <th class="time-col font-weight-bold">Future Date</th>
            <th
              v-for="col in columns"
              :key="col.column_name"
              class="covariate-col font-weight-bold text-center"
              :class="{ 'external-header': col.covariate_type === 'unknown_past' }"
            >
              <div class="d-flex flex-column align-center">
                <div class="d-flex align-center justify-center gap-1">
                  <v-icon
                    :color="col.covariate_type === 'known_future' ? 'success' : 'info'"
                    size="14"
                  >
                    {{ col.covariate_type === 'known_future' ? 'mdi-account-cog-outline' : 'mdi-weather-partly-cloudy' }}
                  </v-icon>
                  <span class="text-caption">{{ col.display_name || col.column_name }}</span>
                </div>

                <!-- Strategy selector -->
                <v-menu offset-y>
                  <template #activator="{ props: menuProps }">
                    <v-chip
                      v-bind="menuProps"
                      class="mt-1"
                      :color="strategyColor(strategyFor(col.column_name))"
                      density="compact"
                      size="x-small"
                      variant="tonal"
                    >
                      {{ strategyLabel(strategyFor(col.column_name)) }}
                      <v-icon end size="12">mdi-chevron-down</v-icon>
                    </v-chip>
                  </template>
                  <v-list density="compact" min-width="180">
                    <v-list-item
                      v-for="s in (col.covariate_type === 'known_future' ? plannedStrategies : externalStrategies)"
                      :key="s.value"
                      :subtitle="s.subtitle"
                      :title="s.title"
                      @click="setStrategy(col.column_name, s.value)"
                    />
                  </v-list>
                </v-menu>

                <!-- Constant input inline in header -->
                <div
                  v-if="strategyFor(col.column_name) === 'constant'"
                  class="mt-1"
                  style="width: 70px;"
                >
                  <input
                    v-model.number="constantInputs[col.column_name]"
                    class="header-input"
                    placeholder="value"
                    type="number"
                    @change="applyConstant(col.column_name)"
                    @keyup.enter="applyConstant(col.column_name)"
                  >
                </div>
              </div>
            </th>
          </tr>
        </thead>
        <tbody v-if="futureTimestamps.length > 0">
          <tr v-for="(timestamp, rowIdx) in futureTimestamps" :key="rowIdx">
            <td class="time-col text-caption font-mono">{{ formatDate(timestamp) }}</td>
            <td
              v-for="col in columns"
              :key="col.column_name"
              class="pa-0"
              :class="{ 'readonly-cell': col.covariate_type === 'unknown_past' || isSeasonalInsufficient(col.column_name) }"
            >
              <input
                v-if="!isSeasonalInsufficient(col.column_name)"
                v-model.number="gridData[col.column_name]![rowIdx]"
                class="spreadsheet-input"
                placeholder="0"
                type="number"
                @input="onCellInput(col.column_name)"
              >
              <div
                v-else
                class="spreadsheet-input insufficient-cell"
                title="Not enough history to detect a repeating pattern — values will be estimated from available data"
              >
                —
              </div>
            </td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr>
            <td class="text-center pa-4 text-caption text-medium-emphasis" :colspan="columns.length + 1">
              <v-icon class="mb-1" size="18">mdi-calendar-remove</v-icon>
              <div>No date data available to generate forecast steps.</div>
            </td>
          </tr>
        </tbody>
      </v-table>
    </div>
  </div>
</template>

<script setup lang="ts">
  import type { ColumnOntology } from '@/types'
  import { addDays, addHours, addMinutes, addMonths, addWeeks, addYears, format, parseISO } from 'date-fns'
  import { computed, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'

  const store = useForecastStore()
  const props = defineProps<{
    columns: ColumnOntology[]
    horizon: number
    frequency: string
  }>()

  const emit = defineEmits(['update:overrides'])

  const gridData = ref<Record<string, number[]>>({})
  const constantInputs = ref<Record<string, number>>({})
  const fileInput = ref<HTMLInputElement | null>(null)

  const plannedStrategies = [
    { value: 'default' as const, title: 'Hold Steady', subtitle: 'Repeat last known value' },
    { value: 'seasonal' as const, title: 'Same as Last Period', subtitle: 'Repeat the value from the matching time last year' },
    { value: 'constant' as const, title: 'Set Fixed', subtitle: 'One value for all steps' },
    { value: 'custom' as const, title: 'Custom Series', subtitle: 'Edit each step' },
  ]

  const externalStrategies = [
    { value: 'default' as const, title: 'Hold Steady', subtitle: 'Freeze last known value' },
    { value: 'seasonal' as const, title: 'Same as Last Period', subtitle: 'Repeat the value from the matching time last year' },
    { value: 'constant' as const, title: 'Set Fixed', subtitle: 'One assumed value for all steps' },
    { value: 'custom' as const, title: 'Custom Series', subtitle: 'Edit each assumed step' },
  ]

  // ─── Date helpers ───

  function getLastHistoricalDate (): Date | null {
    const timeCol = store.timeCol
    if (store.historyResults.length > 0) {
      const lastRow = store.historyResults.at(-1)
      if (lastRow) {
        const raw = lastRow[timeCol]
        if (raw) {
          const d = new Date(raw)
          if (!Number.isNaN(d.getTime())) return d
          const p = parseISO(String(raw))
          if (!Number.isNaN(p.getTime())) return p
        }
      }
    }
    const tail = store.ontology?.historical_tail || store.ontology?.sample_data
    if (tail && tail.length > 0) {
      const lastRow = tail.at(-1)
      if (lastRow) {
        const raw = lastRow[timeCol]
        if (raw) {
          const d = new Date(raw)
          if (!Number.isNaN(d.getTime())) return d
          const p = parseISO(String(raw))
          if (!Number.isNaN(p.getTime())) return p
        }
      }
    }
    return null
  }

  const futureTimestamps = computed(() => {
    const start = getLastHistoricalDate()
    if (!start) return []
    let current = new Date(start)
    const dates: Date[] = []
    for (let i = 1; i <= props.horizon; i++) {
      switch (props.frequency.toLowerCase()) {
        case 'minute': {
          current = addMinutes(current, 1)
          break
        }
        case 'hour': {
          current = addHours(current, 1)
          break
        }
        case 'day': {
          current = addDays(current, 1)
          break
        }
        case 'week': {
          current = addWeeks(current, 1)
          break
        }
        case 'month': {
          current = addMonths(current, 1)
          break
        }
        case 'quarter': {
          current = addMonths(current, 3)
          break
        }
        case 'year': {
          current = addYears(current, 1)
          break
        }
        default: {
          current = addDays(current, 1)
        }
      }
      dates.push(new Date(current))
    }
    return dates
  })

  function formatDate (date: Date) {
    try {
      if (['month', 'quarter', 'year'].includes(props.frequency)) {
        return format(date, 'MMM yyyy')
      }
      return format(date, 'MMM d, yyyy')
    } catch {
      return date.toLocaleDateString()
    }
  }

  // ─── Value helpers ───

  function getLastKnownValue (colName: string): number {
    if (store.historyResults.length > 0) {
      const lastRow = store.historyResults.at(-1)
      if (lastRow) {
        const v = lastRow[colName]
        if (v !== undefined) return Number(v) || 0
      }
    }
    const tail = store.ontology?.historical_tail || store.ontology?.sample_data
    if (tail && tail.length > 0) {
      const lastRow = tail.at(-1)
      if (lastRow) {
        const v = lastRow[colName]
        if (v !== undefined) return Number(v) || 0
      }
    }
    return 0
  }

  function getPeriod (): number | null {
    switch (props.frequency.toLowerCase()) {
      case 'day': { return 7
      }
      case 'week': { return 52
      }
      case 'month': { return 12
      }
      case 'quarter': { return 4
      }
      case 'year': { return 1
      }
      default: { return null
      }
    }
  }

  function getHistorySeries (colName: string): number[] {
    const series: number[] = []
    if (store.historyResults.length > 0) {
      for (const row of store.historyResults) {
        series.push(Number(row[colName]) || 0)
      }
      return series
    }
    const tail = store.ontology?.historical_tail || store.ontology?.sample_data
    if (tail) {
      for (const row of tail) {
        series.push(Number(row[colName]) || 0)
      }
    }
    return series
  }

  function isSeasonalInsufficient (colName: string): boolean {
    const s = strategyFor(colName)
    if (s !== 'seasonal') return false
    const period = getPeriod()
    if (!period) return true
    const history = getHistorySeries(colName)
    return history.length < period
  }

  function getSeasonalValues (colName: string): number[] {
    const history = getHistorySeries(colName)
    const period = getPeriod()
    if (!period || history.length < period) {
      return Array.from({ length: props.horizon }, () => getLastKnownValue(colName))
    }
    const values: number[] = []
    for (let i = 0; i < props.horizon; i++) {
      let idx = history.length + i - period
      while (idx >= history.length) {
        idx -= period
      }
      if (idx >= 0) {
        values.push(history[idx]!)
      } else {
        values.push(history.at(-1)!)
      }
    }
    return values
  }

  // ─── Strategy detection ───

  function strategyFor (colName: string): 'default' | 'constant' | 'custom' | 'seasonal' {
    const item = store.ontology?.scenario_overrides?.find(o => o.column_name === colName)
    const override = item?.values
    if (override === 'seasonal') return 'seasonal'
    if (Array.isArray(override)) return 'custom'
    if (typeof override === 'number') return 'constant'
    return 'default'
  }

  function strategyLabel (s: 'default' | 'constant' | 'custom' | 'seasonal'): string {
    switch (s) {
      case 'default': { return 'Hold Steady'
      }
      case 'constant': { return 'Set Fixed'
      }
      case 'custom': { return 'Custom Series'
      }
      case 'seasonal': { return 'Last Period'
      }
    }
  }

  function strategyColor (s: 'default' | 'constant' | 'custom' | 'seasonal'): string {
    switch (s) {
      case 'default': { return 'grey'
      }
      case 'constant': { return 'secondary'
      }
      case 'custom': { return 'primary'
      }
      case 'seasonal': { return 'info'
      }
    }
  }

  // ─── Grid init & sync ───

  function buildColumnData (colName: string): number[] {
    const item = store.ontology?.scenario_overrides?.find(o => o.column_name === colName)
    const override = item?.values
    if (override === 'seasonal') {
      return getSeasonalValues(colName)
    }
    if (Array.isArray(override)) {
      const arr = [...override]
      while (arr.length < props.horizon) arr.push(arr.at(-1) || 0)
      return arr.slice(0, props.horizon)
    }
    if (typeof override === 'number') {
      return Array.from({ length: props.horizon }, () => override)
    }
    const lastVal = getLastKnownValue(colName)
    return Array.from({ length: props.horizon }, () => lastVal)
  }

  function initGrid () {
    const newGrid: Record<string, number[]> = {}
    for (const col of props.columns) {
      newGrid[col.column_name] = buildColumnData(col.column_name)
      // Init constant input if applicable
      const item = store.ontology?.scenario_overrides?.find(o => o.column_name === col.column_name)
      const override = item?.values
      if (typeof override === 'number') {
        constantInputs.value[col.column_name] = override
      }
    }
    gridData.value = newGrid
  }

  watch(() => props.columns, initGrid, { deep: true, immediate: true })
  watch(() => props.horizon, initGrid, { immediate: true })

  // Watch external changes to scenario_overrides (e.g. from left panel)
  watch(() => store.ontology?.scenario_overrides, () => {
    if (!store.ontology) return
    for (const col of props.columns) {
      const newData = buildColumnData(col.column_name)
      const oldData = gridData.value[col.column_name]
      if (!oldData || JSON.stringify(oldData) !== JSON.stringify(newData)) {
        gridData.value[col.column_name] = newData
      }
      const item = store.ontology.scenario_overrides?.find(o => o.column_name === col.column_name)
      const override = item?.values
      if (typeof override === 'number') {
        constantInputs.value[col.column_name] = override
      }
    }
  }, { deep: true })

  function emitOverrides () {
    if (!store.ontology) return
    const newOverrides: any[] = []
    for (const col of props.columns) {
      const s = strategyFor(col.column_name)
      if (s === 'default') continue

      if (s === 'seasonal') {
        newOverrides.push({ column_name: col.column_name, values: 'seasonal' })
      } else {
        const data = gridData.value[col.column_name]
        if (!data) continue

        if (s === 'constant') {
          newOverrides.push({ column_name: col.column_name, values: data[0] })
        } else {
          newOverrides.push({ column_name: col.column_name, values: [...data] })
        }
      }
    }
    store.ontology.scenario_overrides = newOverrides
    emit('update:overrides', [...newOverrides])
  }

  // ─── User actions ───

  function setStrategy (colName: string, strategy: 'default' | 'constant' | 'custom' | 'seasonal') {
    if (!store.ontology) return
    if (!store.ontology.scenario_overrides) store.ontology.scenario_overrides = []

    // Filter out existing override for this column
    store.ontology.scenario_overrides = store.ontology.scenario_overrides.filter(o => o.column_name !== colName)

    switch (strategy) {
      case 'constant': {
        const lastVal = getLastKnownValue(colName)
        store.ontology.scenario_overrides.push({ column_name: colName, values: lastVal })
        constantInputs.value[colName] = lastVal

        break
      }
      case 'seasonal': {
        store.ontology.scenario_overrides.push({ column_name: colName, values: 'seasonal' as any })

        break
      }
      case 'custom': {
        const lastVal = getLastKnownValue(colName)
        store.ontology.scenario_overrides.push({ column_name: colName, values: Array.from({ length: props.horizon }, () => lastVal) })

        break
      }
    // No default
    }

    // Rebuild this column's grid data
    gridData.value[colName] = buildColumnData(colName)
    emitOverrides()
  }

  function applyConstant (colName: string) {
    const val = constantInputs.value[colName] ?? 0
    if (!store.ontology) return
    if (!store.ontology.scenario_overrides) store.ontology.scenario_overrides = []

    const existing = store.ontology.scenario_overrides.find(o => o.column_name === colName)
    if (existing) {
      existing.values = val
    } else {
      store.ontology.scenario_overrides.push({ column_name: colName, values: val })
    }

    gridData.value[colName] = Array.from({ length: props.horizon }, () => val)
    emitOverrides()
  }

  function onCellInput (colName: string) {
    if (!store.ontology) return
    if (!store.ontology.scenario_overrides) store.ontology.scenario_overrides = []

    const existing = store.ontology.scenario_overrides.find(o => o.column_name === colName)
    if (existing) {
      existing.values = [...gridData.value[colName]!]
    } else {
      store.ontology.scenario_overrides.push({ column_name: colName, values: [...gridData.value[colName]!] })
    }
    emitOverrides()
  }

  function triggerFileUpload () {
    fileInput.value?.click()
  }

  function handleFileUpload (event: Event) {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file) return

    file.text().then(text => {
      if (!text) return
      parseCsvUpload(text)
    })
    target.value = ''
  }

  function parseCsvUpload (text: string) {
    if (!store.ontology) return
    const lines = text.split('\n').filter(l => l.trim())
    if (lines.length < 2) return

    const firstLine = lines[0]!
    const headers = firstLine.split(',').map(h => h.trim())

    for (let rowIdx = 1; rowIdx < lines.length && rowIdx - 1 < props.horizon; rowIdx++) {
      const line = lines[rowIdx]
      if (!line) continue
      const cells = line.split(',').map(c => c.trim())
      for (const [colIdx, colName] of headers.entries()) {
        if (!colName) continue
        const col = props.columns.find(c => c.column_name === colName)
        if (!col) continue

        const rawVal = cells[colIdx]
        if (!rawVal) continue
        const val = Number(rawVal)
        if (Number.isNaN(val)) continue

        if (!gridData.value[colName]) continue
        const gridRow = rowIdx - 1
        if (gridRow < props.horizon) {
          gridData.value[colName]![gridRow] = val
        }
      }
    }

    // Sync to store
    for (const col of props.columns) {
      const data = gridData.value[col.column_name]
      if (!data) continue

      if (store.ontology.scenario_overrides) {
        store.ontology.scenario_overrides = store.ontology.scenario_overrides.filter(o => o.column_name !== col.column_name)
        store.ontology.scenario_overrides.push({ column_name: col.column_name, values: [...data] })
      }
    }
    emitOverrides()
  }
</script>

<style scoped>
.future-data-grid {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  overflow: hidden;
}

.spreadsheet-container {
  max-height: 420px;
  overflow: auto;
}

.compact-table :deep(th) {
  height: auto !important;
  padding: 6px 4px !important;
  font-size: 0.75rem !important;
  background-color: var(--v-theme-surface-light) !important;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.compact-table :deep(td) {
  height: 32px !important;
  padding: 0 !important;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
}

.time-col {
  width: 110px;
  background-color: var(--v-theme-surface-light);
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.compact-table :deep(td.time-col),
.compact-table :deep(th.time-col) {
  padding: 0 10px !important;
}

.covariate-col {
  min-width: 120px;
}

.external-header {
  background-color: rgba(var(--v-theme-info), 0.03) !important;
}

.spreadsheet-input {
  width: 100%;
  height: 32px;
  border: none;
  background: transparent;
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  outline: none;
  transition: background 0.15s;
}

.spreadsheet-input:focus {
  background-color: rgba(var(--v-theme-primary), 0.06);
  box-shadow: inset 0 0 0 1px rgb(var(--v-theme-primary));
}

.readonly-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

.readonly-input {
  color: rgba(var(--v-theme-on-surface), 0.45);
  cursor: not-allowed;
}

.header-input {
  width: 100%;
  height: 22px;
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  border-radius: 4px;
  background: rgba(var(--v-theme-primary), 0.04);
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  outline: none;
}

.header-input:focus {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.08);
}

.spreadsheet-input::-webkit-inner-spin-button,
.spreadsheet-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.insufficient-cell {
  color: rgba(var(--v-theme-on-surface), 0.35);
  cursor: help;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
