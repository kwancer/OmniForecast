<template>
  <v-card class="future-data-grid border rounded-lg" variant="flat">
    <div class="pa-4 bg-surface-light border-b d-flex align-center">
      <v-icon class="mr-2" color="primary">mdi-table-edit</v-icon>
      <span class="text-subtitle-2 font-weight-bold">Scenario Spreadsheet</span>
      <v-spacer />
      <v-chip size="x-small" variant="tonal">{{ horizon }} steps</v-chip>
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
            >
              <div class="d-flex align-center justify-center">
                <v-icon class="mr-1" color="success" size="14">mdi-account-cog-outline</v-icon>
                {{ col.display_name || col.column_name }}
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(timestamp, rowIdx) in futureTimestamps" :key="rowIdx">
            <td class="time-col text-caption font-mono">{{ formatDate(timestamp) }}</td>
            <td
              v-for="col in columns"
              :key="col.column_name"
              class="pa-0"
            >
              <input
                v-model.number="gridData[col.column_name][rowIdx]"
                class="spreadsheet-input"
                placeholder="0.0"
                type="number"
                @input="emitChange"
              >
            </td>
          </tr>
        </tbody>
      </v-table>
    </div>

    <!-- Quick Actions -->
    <div class="pa-2 bg-surface-light border-t d-flex justify-end gap-2">
      <v-btn
        density="compact"
        prepend-icon="mdi-content-copy"
        size="x-small"
        variant="text"
        @click="fillDown"
      >
        Fill Down
      </v-btn>
      <v-btn
        color="error"
        density="compact"
        prepend-icon="mdi-eraser"
        size="x-small"
        variant="text"
        @click="clearAll"
      >
        Clear
      </v-btn>
    </div>
  </v-card>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import { addDays, addHours, addMinutes, addMonths, addWeeks, addYears, format, parseISO } from 'date-fns'

  const store = useForecastStore()
  const props = defineProps<{
    columns: any[]
    horizon: number
    frequency: string
  }>()

  const emit = defineEmits(['update:overrides'])

  const gridData = ref<Record<string, number[]>>({})

  // Generate future timestamps
  const futureTimestamps = computed(() => {
    if (store.historyResults.length === 0) return []
    
    const timeCol = store.timeCol
    const lastRow = store.historyResults[store.historyResults.length - 1]
    const lastDateRaw = lastRow[timeCol]
    
    let current = new Date(lastDateRaw)
    if (Number.isNaN(current.getTime())) {
       // Try parsing ISO
       current = parseISO(lastDateRaw)
    }

    const dates: Date[] = []
    for (let i = 1; i <= props.horizon; i++) {
      switch (props.frequency.toLowerCase()) {
        case 'minute': current = addMinutes(current, 1); break
        case 'hour': current = addHours(current, 1); break
        case 'day': current = addDays(current, 1); break
        case 'week': current = addWeeks(current, 1); break
        case 'month': current = addMonths(current, 1); break
        case 'quarter': current = addMonths(current, 3); break
        case 'year': current = addYears(current, 1); break
        default: current = addDays(current, 1)
      }
      dates.push(new Date(current))
    }
    return dates
  })

  function formatDate (date: Date) {
    try {
      if (props.frequency === 'month' || props.frequency === 'quarter' || props.frequency === 'year') {
        return format(date, 'MMM yyyy')
      }
      return format(date, 'MMM d, yyyy')
    } catch {
      return date.toLocaleDateString()
    }
  }

  function initGrid () {
    const newGrid: Record<string, number[]> = {}
    for (const col of props.columns) {
      // Check if we already have overrides in store
      const existing = store.ontology?.scenario_overrides?.[col.column_name]
      if (Array.isArray(existing)) {
        newGrid[col.column_name] = [...existing]
        // Pad if horizon grew
        while (newGrid[col.column_name].length < props.horizon) {
          newGrid[col.column_name].push(existing[existing.length - 1] || 0)
        }
        // Truncate if horizon shrank
        if (newGrid[col.column_name].length > props.horizon) {
          newGrid[col.column_name] = newGrid[col.column_name].slice(0, props.horizon)
        }
      } else if (typeof existing === 'number') {
        newGrid[col.column_name] = Array(props.horizon).fill(existing)
      } else {
        // Fallback: use last known value from history if possible
        const lastVal = store.historyResults.length > 0 ? store.historyResults[store.historyResults.length - 1][col.column_name] : 0
        newGrid[col.column_name] = Array(props.horizon).fill(Number(lastVal) || 0)
      }
    }
    gridData.value = newGrid
    emitChange()
  }

  watch(() => props.columns, initGrid, { deep: true })
  watch(() => props.horizon, initGrid)

  onMounted(() => {
    initGrid()
  })

  function emitChange () {
    emit('update:overrides', { ...gridData.value })
  }

  function fillDown () {
    for (const colName in gridData.value) {
      const firstVal = gridData.value[colName][0] || 0
      gridData.value[colName] = Array(props.horizon).fill(firstVal)
    }
    emitChange()
  }

  function clearAll () {
    for (const colName in gridData.value) {
      gridData.value[colName] = Array(props.horizon).fill(0)
    }
    emitChange()
  }
</script>

<style scoped>
.spreadsheet-container {
  max-height: 400px;
  overflow: auto;
}

.compact-table :deep(th) {
  height: 32px !important;
  font-size: 0.75rem !important;
  background-color: var(--v-theme-surface-light) !important;
}

.compact-table :deep(td) {
  height: 28px !important;
  padding: 0 !important;
}

.time-col {
  width: 120px;
  background-color: var(--v-theme-surface-light);
  padding: 0 8px !important;
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.spreadsheet-input {
  width: 100%;
  height: 28px;
  border: none;
  background: transparent;
  text-align: center;
  font-family: monospace;
  font-size: 0.875rem;
  outline: none;
}

.spreadsheet-input:focus {
  background-color: rgba(var(--v-theme-primary), 0.05);
  box-shadow: inset 0 0 0 1px rgb(var(--v-theme-primary));
}

.spreadsheet-input::-webkit-inner-spin-button,
.spreadsheet-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
