<template>
  <v-card class="unified-table-card border" variant="flat">
    <v-table class="unified-table" density="comfortable" fixed-header hover>
      <thead>
        <tr>
          <th
            v-for="col in orderedColumns"
            :key="col.column_name"
            class="unified-th"
            :class="{ 'ignored-col': isIgnored(col.column_name), 'sticky-col': col.column_name === timeColName }"
          >
            <div class="th-content pt-4">
              <div class="th-name">
                <v-icon
                  v-if="getColumnRole(col.column_name) === 'target'"
                  class="mr-1"
                  color="primary"
                  size="small"
                >mdi-target</v-icon>
                <v-icon
                  v-else-if="getColumnRole(col.column_name) === 'time_index'"
                  class="mr-1"
                  color="secondary"
                  size="small"
                >mdi-clock-outline</v-icon>
                <v-icon
                  v-else-if="isIgnored(col.column_name)"
                  class="mr-1"
                  size="small"
                >mdi-eye-off</v-icon>
                <span :class="{ 'text-decoration-line-through': isIgnored(col.column_name)}">
                  {{ col.display_name || col.column_name }}
                </span>
              </div>

              <!-- Ignore / Re-include toggle in header -->
              <template v-if="getColumnRole(col.column_name) !== 'target' && getColumnRole(col.column_name) !== 'time_index' && getColumnRole(col.column_name) !== 'group_id'">
                <v-btn
                  v-if="isIgnored(col.column_name)"
                  class="th-btn"
                  color="primary"
                  density="compact"
                  size="x-small"
                  variant="outlined"
                  @click="$emit('toggle-ignore', col.column_name, false)"
                >
                  <v-icon size="12" start>mdi-eye</v-icon>
                  Re-include
                </v-btn>
                <v-btn
                  v-else
                  class="th-btn"
                  color="grey"
                  density="compact"
                  size="x-small"
                  variant="text"
                  @click="$emit('toggle-ignore', col.column_name, true)"
                >
                  <v-icon size="12" start>mdi-eye-off</v-icon>
                  Ignore
                </v-btn>
              </template>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <!-- Historical: First 2 rows -->
        <tr
          v-for="(row, idx) in headRows"
          :key="`head-${idx}`"
        >
          <td
            v-for="col in orderedColumns"
            :key="col.column_name"
            class="unified-td"
            :class="{
              'ignored-col': isIgnored(col.column_name),
              'target-cell': getColumnRole(col.column_name) === 'target',
              'sticky-col': col.column_name === timeColName,
            }"
          >
            {{ formatVal(row[col.column_name]) }}
          </td>
        </tr>

        <!-- Ellipsis row -->
        <tr class="ellipsis-row">
          <td
            v-for="col in orderedColumns"
            :key="col.column_name"
            class="unified-td ellipsis-cell"
            :class="{ 'sticky-col': col.column_name === timeColName }"
          >
            ⋯
          </td>
        </tr>

        <!-- Historical: Last 3 rows -->
        <tr
          v-for="(row, idx) in tailRows"
          :key="`tail-${idx}`"
        >
          <td
            v-for="col in orderedColumns"
            :key="col.column_name"
            class="unified-td"
            :class="{
              'ignored-col': isIgnored(col.column_name),
              'target-cell': getColumnRole(col.column_name) === 'target',
              'sticky-col': col.column_name === timeColName,
            }"
          >
            {{ formatVal(row[col.column_name]) }}
          </td>
        </tr>

        <template v-if="hasCovariates">
          <!-- Divider with label -->
          <tr class="divider-row">
            <td class="divider-cell" :colspan="orderedColumns.length">
              <span class="divider-label">Future Assumptions</span>
            </td>
          </tr>

          <!-- Behaviour Row -->
          <tr class="behaviour-row">
            <td
              v-for="col in orderedColumns"
              :key="col.column_name"
              class="unified-td behaviour-cell"
              :class="{ 'ignored-col': isIgnored(col.column_name), 'sticky-col': col.column_name === timeColName }"
            >
              <!-- Time column -->
              <div v-if="getColumnRole(col.column_name) === 'time_index'" class="behaviour-content">
                <v-chip color="secondary" density="comfortable" size="small" variant="flat">
                  <v-icon size="14" start>mdi-clock</v-icon>
                  Timeline
                </v-chip>
                <div class="behaviour-meta">
                  {{ col.data_type }}
                </div>
              </div>

              <!-- Target column -->
              <div v-else-if="getColumnRole(col.column_name) === 'target'" class="behaviour-content">
                <v-chip color="primary" density="comfortable" size="small" variant="flat">
                  <v-icon size="14" start>mdi-target</v-icon>
                  Target
                </v-chip>
                <div class="behaviour-meta">
                  {{ col.constraints?.min_value !== null && col.constraints?.min_value !== undefined ? 'Positive only' : 'Any value' }}
                </div>
              </div>

              <!-- Group column -->
              <div v-else-if="getColumnRole(col.column_name) === 'group_id'" class="behaviour-content">
                <v-chip color="warning" density="comfortable" size="small" variant="flat">
                  <v-icon size="14" start>mdi-group</v-icon>
                  Group
                </v-chip>
                <div class="behaviour-meta">
                  Series identifier
                </div>
              </div>

              <!-- Ignored column -->
              <div v-else-if="isIgnored(col.column_name)" class="behaviour-content">
                <v-chip color="grey" density="comfortable" size="small" variant="outlined">
                  <v-icon size="14" start>mdi-eye-off</v-icon>
                  Not Used
                </v-chip>
              </div>

              <!-- Covariate column -->
              <div v-else class="behaviour-content">
                <!-- Planned / External toggle -->
                <div class="d-flex align-center justify-center mb-3">
                  <v-btn-toggle
                    color="primary"
                    density="comfortable"
                    mandatory
                    :model-value="col.covariate_type === 'known_future' ? 'planned' : 'external'"
                    rounded
                    variant="tonal"
                    @update:model-value="v => $emit('change-type', col.column_name, v === 'planned' ? 'known_future' : 'unknown_past')"
                  >
                    <v-btn size="small" value="planned">
                      <v-icon size="14" start>mdi-cog</v-icon>
                      Planned
                    </v-btn>
                    <v-btn size="small" value="external">
                      <v-icon size="14" start>mdi-cloud</v-icon>
                      External
                    </v-btn>
                  </v-btn-toggle>
                  <v-tooltip location="top" max-width="320">
                    <template #activator="{ props: tipProps }">
                      <v-icon v-bind="tipProps" class="ml-2" color="medium-emphasis" size="14">mdi-information-outline</v-icon>
                    </template>
                    <div class="text-caption">
                      <strong>Planned drivers</strong> (like price or promotions) are values you control — the model uses your exact numbers directly.<br><br>
                      <strong>External factors</strong> (like weather or competitor prices) are assumptions you make — the model looks at the pattern before your assumption, so the impact builds gradually.
                    </div>
                  </v-tooltip>
                </div>

                <!-- Strategy dropdown -->
                <v-menu offset-y>
                  <template #activator="{ props: menuProps }">
                    <v-chip
                      v-bind="menuProps"
                      :color="strategyColor(strategyFor(col.column_name))"
                      density="comfortable"
                      size="small"
                      variant="tonal"
                    >
                      {{ strategyLabel(strategyFor(col.column_name)) }}
                      <v-icon end size="14">mdi-chevron-down</v-icon>
                    </v-chip>
                  </template>
                  <v-list density="compact" min-width="200">
                    <v-list-item
                      v-for="s in availableStrategies(col.covariate_type)"
                      :key="s.value"
                      :subtitle="s.subtitle"
                      :title="s.title"
                      @click="setStrategy(col.column_name, s.value)"
                    />
                  </v-list>
                </v-menu>

                <!-- Constant input -->
                <div
                  v-if="strategyFor(col.column_name) === 'constant'"
                  class="mt-3"
                  style="width: 90px;"
                >
                  <v-text-field
                    v-model.number="constantInputs[col.column_name]"
                    class="constant-input"
                    density="compact"
                    hide-details
                    placeholder="Value"
                    type="number"
                    variant="outlined"
                    @blur="applyConstant(col.column_name)"
                    @keyup.enter="applyConstant(col.column_name)"
                  />
                </div>
              </div>
            </td>
          </tr>
          <!-- Future value rows -->
          <tr
            v-for="(date, idx) in futureTimestamps"
            :key="`future-${idx}`"
          >
            <td
              v-for="col in orderedColumns"
              :key="col.column_name"
              class="unified-td future-cell"
              :class="{
                'ignored-col': isIgnored(col.column_name),
                'target-cell': getColumnRole(col.column_name) === 'target',
                'sticky-col': col.column_name === timeColName,
              }"
            >
              <!-- Time column: future date -->
              <template v-if="getColumnRole(col.column_name) === 'time_index'">
                <span class="text-secondary font-weight-medium">{{ formatDate(date) }}</span>
              </template>

              <!-- Target column: subtle forecast indicator -->
              <template v-else-if="getColumnRole(col.column_name) === 'target'">
                <v-tooltip location="top" text="This value will be predicted by the model">
                  <template #activator="{ props: tipProps }">
                    <div v-bind="tipProps" class="forecasted-indicator">
                      <v-icon color="primary" size="18">mdi-crystal-ball</v-icon>
                    </div>
                  </template>
                </v-tooltip>
              </template>

              <!-- Group column -->
              <template v-else-if="getColumnRole(col.column_name) === 'group_id'">
                <span class="text-disabled">—</span>
              </template>

              <!-- Ignored column -->
              <template v-else-if="isIgnored(col.column_name)">
                <span class="text-disabled">—</span>
              </template>

              <!-- External factor: editable assumption -->
              <template v-else-if="col.covariate_type === 'unknown_past'">
                <v-tooltip location="top" text="Your assumption — the model responds to the pattern before it">
                  <template #activator="{ props: tipProps }">
                    <input
                      v-if="gridData[col.column_name]"
                      v-model.number="gridData[col.column_name]![idx]"
                      v-bind="tipProps"
                      class="future-input"
                      placeholder="0"
                      type="number"
                      @input="onCellInput(col.column_name)"
                    >
                    <span v-else class="text-disabled">—</span>
                  </template>
                </v-tooltip>
              </template>

              <!-- Planned driver: editable -->
              <template v-else>
                <input
                  v-if="gridData[col.column_name]"
                  v-model.number="gridData[col.column_name]![idx]"
                  class="future-input"
                  placeholder="0"
                  type="number"
                  @input="onCellInput(col.column_name)"
                >
                <span v-else class="text-disabled">—</span>
              </template>
            </td>
          </tr>
        </template>
      </tbody>
    </v-table>
  </v-card>
</template>

<script setup lang="ts">
  import type { SentenceState } from './OntologySentence.vue'
  import type { ColumnOntology, CovariateState, CovariateType, ForecastOntology } from '@/types'
  import { addDays, addHours, addMinutes, addMonths, addWeeks, addYears, format, parseISO } from 'date-fns'
  import { computed, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import { formatNumber } from '@/utils/formatters'

  const store = useForecastStore()

  const props = defineProps<{
    ontology: ForecastOntology
    sentenceState: SentenceState
    covariateStates: Record<string, CovariateState>
  }>()

  const emit = defineEmits<{
    (e: 'toggle-ignore', colName: string, ignored: boolean): void
    (e: 'change-type', colName: string, newType: CovariateType): void
    (e: 'update-override', colName: string, values: number | number[] | 'seasonal' | null): void
  }>()

  // ─── Column ordering ───

  const timeColName = computed(() => props.sentenceState.time_col)
  const targetColName = computed(() => props.sentenceState.target_col)

  const orderedColumns = computed((): ColumnOntology[] => {
    const all = props.ontology.columns
    const timeCol = all.find(c => c.column_name === timeColName.value)
    const targetCol = all.find(c => c.column_name === targetColName.value)
    const others = all.filter(c =>
      c.column_name !== timeColName.value
      && c.column_name !== targetColName.value,
    )
    const active = others.filter(c => !isIgnored(c.column_name))
    const ignored = others.filter(c => isIgnored(c.column_name))
    const result: ColumnOntology[] = []
    if (timeCol) result.push(timeCol)
    if (targetCol) result.push(targetCol)
    result.push(...active, ...ignored)
    return result
  })

  // ─── Helpers ───

  function getColumnRole (colName: string): string {
    if (colName === props.sentenceState.target_col) return 'target'
    if (colName === props.sentenceState.time_col) return 'time_index'
    const col = props.ontology.columns.find(c => c.column_name === colName)
    return col?.role || ''
  }

  function isIgnored (colName: string): boolean {
    return props.covariateStates[colName]?.isIgnored === true
  }

  const hasCovariates = computed(() => {
    return props.ontology.columns.some(c =>
      c.role === 'covariate' && !isIgnored(c.column_name),
    )
  })

  function formatVal (val: any) {
    if (val === undefined || val === null) return '—'
    if (typeof val === 'string') {
      if (val.length > 20) return val.slice(0, 17) + '...'
      return val
    }
    return formatNumber(val)
  }

  function roundTo (val: number, decimals = 2): number {
    const factor = 10 ** decimals
    return Math.round(val * factor) / factor
  }

  // ─── Historical rows ───

  const headRows = computed(() => {
    const data = props.ontology.sample_data || []
    return data.slice(0, 2)
  })

  const tailRows = computed(() => {
    const tail = props.ontology.historical_tail
    if (tail && tail.length > 0) return tail.slice(-3)
    const data = props.ontology.sample_data || []
    return data.slice(-3)
  })

  // ─── Date generation ───

  function getLastHistoricalDate (): Date | null {
    const tCol = timeColName.value
    if (store.historyResults.length > 0) {
      const lastRow = store.historyResults.at(-1)
      if (lastRow) {
        const raw = lastRow[tCol]
        if (raw) {
          const d = new Date(raw)
          if (!Number.isNaN(d.getTime())) return d
          const p = parseISO(String(raw))
          if (!Number.isNaN(p.getTime())) return p
        }
      }
    }
    const tail = props.ontology.historical_tail || props.ontology.sample_data
    if (tail && tail.length > 0) {
      const lastRow = tail.at(-1)
      if (lastRow) {
        const raw = lastRow[tCol]
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
    const horizon = props.sentenceState.horizon || 12
    const frequency = props.sentenceState.frequency || 'month'
    for (let i = 1; i <= horizon; i++) {
      switch (frequency.toLowerCase()) {
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
        default: { current = addDays(current, 1) }
      }
      dates.push(new Date(current))
    }
    return dates
  })

  function formatDate (date: Date) {
    try {
      const freq = props.sentenceState.frequency || 'month'
      if (['month', 'quarter', 'year'].includes(freq)) {
        return format(date, 'MMM yyyy')
      }
      return format(date, 'MMM d, yyyy')
    } catch {
      return date.toLocaleDateString()
    }
  }

  // ─── Value helpers (ported from FutureDataGrid) ───

  function getLastKnownValue (colName: string): number {
    let raw: any
    if (store.historyResults.length > 0) {
      const lastRow = store.historyResults.at(-1)
      if (lastRow) raw = lastRow[colName]
    }
    if (raw === undefined) {
      const tail = props.ontology.historical_tail || props.ontology.sample_data
      if (tail && tail.length > 0) {
        const lastRow = tail.at(-1)
        if (lastRow) raw = lastRow[colName]
      }
    }
    return roundTo(Number(raw) || 0)
  }

  function getPeriod (): number | null {
    switch ((props.sentenceState.frequency || 'month').toLowerCase()) {
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
    const tail = props.ontology.historical_tail || props.ontology.sample_data
    if (tail) {
      for (const row of tail) {
        series.push(Number(row[colName]) || 0)
      }
    }
    return series
  }

  function getSeasonalValues (colName: string): number[] {
    const history = getHistorySeries(colName)
    const period = getPeriod()
    const horizon = props.sentenceState.horizon || 12
    if (!period || history.length < period) {
      return Array.from({ length: horizon }, () => getLastKnownValue(colName))
    }
    const values: number[] = []
    for (let i = 0; i < horizon; i++) {
      let idx = history.length + i - period
      while (idx >= history.length) {
        idx -= period
      }
      if (idx >= 0) {
        values.push(roundTo(history[idx]!))
      } else {
        values.push(roundTo(history.at(-1)!))
      }
    }
    return values
  }

  // ─── Strategy management ───

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

  function availableStrategies (covType?: CovariateType) {
    return covType === 'known_future' ? plannedStrategies : externalStrategies
  }

  function strategyFor (colName: string): 'default' | 'constant' | 'custom' | 'seasonal' {
    const item = props.ontology.scenario_overrides?.find(o => o.column_name === colName)
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
      case 'seasonal': { return 'Same as Last Period'
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

  function buildColumnData (colName: string): number[] {
    const item = props.ontology.scenario_overrides?.find(o => o.column_name === colName)
    const override = item?.values
    const horizon = props.sentenceState.horizon || 12
    if (override === 'seasonal') {
      return getSeasonalValues(colName)
    }
    if (Array.isArray(override)) {
      const arr = override.map(v => roundTo(v))
      while (arr.length < horizon) arr.push(arr.at(-1) || 0)
      return arr.slice(0, horizon)
    }
    if (typeof override === 'number') {
      return Array.from({ length: horizon }, () => roundTo(override))
    }
    const lastVal = getLastKnownValue(colName)
    return Array.from({ length: horizon }, () => lastVal)
  }

  // ─── Grid data ───

  const gridData = ref<Record<string, number[]>>({})
  const constantInputs = ref<Record<string, number>>({})

  function initGrid () {
    const newGrid: Record<string, number[]> = {}
    for (const col of props.ontology.columns) {
      if (col.role === 'covariate' && !isIgnored(col.column_name)) {
        newGrid[col.column_name] = buildColumnData(col.column_name)
        const item = props.ontology.scenario_overrides?.find(o => o.column_name === col.column_name)
        const override = item?.values
        if (typeof override === 'number') {
          constantInputs.value[col.column_name] = roundTo(override)
        }
      }
    }
    gridData.value = newGrid
  }

  const activeCovariateCols = computed(() => {
    return props.ontology.columns
      .filter(c => c.role === 'covariate' && !isIgnored(c.column_name))
      .map(c => c.column_name)
      .toSorted()
      .join(',')
  })

  watch(() => props.ontology.scenario_overrides, initGrid, { deep: true, immediate: true })
  watch(() => props.sentenceState.horizon, initGrid, { immediate: true })
  watch(activeCovariateCols, initGrid)

  // ─── Actions ───

  function setStrategy (colName: string, strategy: 'default' | 'constant' | 'custom' | 'seasonal') {
    let values: number | number[] | 'seasonal' | null = null

    switch (strategy) {
      case 'constant': {
        const lastVal = getLastKnownValue(colName)
        values = lastVal
        constantInputs.value[colName] = lastVal
        break
      }
      case 'seasonal': {
        values = 'seasonal'
        break
      }
      case 'custom': {
        const lastVal = getLastKnownValue(colName)
        values = Array.from({ length: props.sentenceState.horizon || 12 }, () => lastVal)
        break
      }
      default: {
        values = null
      }
    }

    emit('update-override', colName, values)
  }

  function applyConstant (colName: string) {
    const val = constantInputs.value[colName]
    if (val === undefined || val === null) return
    emit('update-override', colName, roundTo(val))
  }

  function onCellInput (colName: string) {
    const data = gridData.value[colName]
    if (!data) return
    emit('update-override', colName, data.map(v => roundTo(v)))
  }
</script>

<style scoped>
.unified-table-card {
  border-radius: 16px;
  overflow: hidden;
  background: var(--v-theme-surface);
}

.unified-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.unified-table :deep(thead th) {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--v-theme-surface-light) !important;
  border-bottom: 2px solid rgba(var(--v-theme-on-surface), 0.08);
  font-weight: 600;
  font-size: 0.85rem;
  vertical-align: middle;
  text-align: center;
}

.unified-table :deep(tbody td) {
  padding: 10px 18px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.04);
  font-size: 0.85rem;
  font-family: 'JetBrains Mono', monospace;
  white-space: nowrap;
  text-align: center;
}

/* Sticky first column */
.sticky-col {
  position: sticky;
  left: 0;
  background: var(--v-theme-surface);
  z-index: 1;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.unified-table :deep(thead th.sticky-col) {
  z-index: 3;
}

.th-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  padding-bottom: 46px;
}

.th-btn {
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
}

.th-name {
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

/* Ellipsis row */
.ellipsis-row {
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.ellipsis-cell {
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.45);
  font-size: 1.1rem;
  font-weight: 500;
  letter-spacing: 4px;
  padding: 6px 18px !important;
}

/* Divider row */
.divider-row {
  height: 2px;
}

.divider-cell {
  position: relative;
  border-bottom: 2px dashed rgba(var(--v-theme-on-surface), 0.15);
  padding: 0 !important;
  text-align: center;
}

.divider-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--v-theme-surface);
  padding: 0 12px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  white-space: nowrap;
}

/* Behaviour row */
.behaviour-row {
  background: var(--v-theme-surface-light) !important;
}

.behaviour-row :deep(td) {
  border-top: 2px solid rgba(var(--v-theme-on-surface), 0.08);
  border-bottom: 2px solid rgba(var(--v-theme-on-surface), 0.08);
}

.behaviour-cell {
  vertical-align: top;
  padding: 20px 18px !important;
}

.behaviour-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 140px;
  min-height: 100px;
  gap: 4px;
}

.behaviour-meta {
  margin-top: 6px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

/* Target highlighting */
.target-cell {
  background: rgba(var(--v-theme-primary), 0.04);
  font-weight: 600;
}

/* Ignored columns */
.ignored-col {
  opacity: 0.4;
}

/* Future rows */
.future-cell {
  background: rgba(var(--v-theme-success), 0.015);
  font-size: 0.85rem;
}

/* Forecasted indicator (subtle crystal ball) */
.forecasted-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: help;
}

/* Editable future inputs */
.future-input {
  width: 100%;
  height: 32px;
  border: none;
  background: transparent;
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  outline: none;
  transition: background 0.15s;
  border-radius: 4px;
}

.future-input:focus {
  background-color: rgba(var(--v-theme-primary), 0.08);
  box-shadow: inset 0 0 0 1px rgb(var(--v-theme-primary));
}

.future-input::-webkit-inner-spin-button,
.future-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

/* Constant input in behaviour row */
.constant-input :deep(input) {
  text-align: center;
  font-size: 0.8rem;
  padding: 0 4px;
}
</style>
