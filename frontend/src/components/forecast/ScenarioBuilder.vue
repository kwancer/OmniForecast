<template>
  <div class="scenario-builder">
    <!-- Section 1: Environmental Factors (Read-Only) -->
    <div v-if="unknownColumns.length > 0" class="mb-6">
      <div class="d-flex align-center mb-4">
        <v-icon color="info" size="20">mdi-weather-partly-cloudy</v-icon>
        <h3 class="text-subtitle-2 font-weight-bold ml-2">Environmental Factors</h3>
        <v-tooltip location="top">
          <template #activator="{ props }">
            <v-icon v-bind="props" class="ml-1" color="medium-emphasis" size="14">mdi-help-circle-outline</v-icon>
          </template>
          <span>Historical context used to stabilize the forecast. Shifting is applied to prevent leakage.</span>
        </v-tooltip>
      </div>

      <v-row dense>
        <v-col v-for="col in unknownColumns" :key="col.column_name" cols="12" sm="6">
          <v-card class="pa-3 bg-surface border rounded-lg" variant="flat">
            <div class="d-flex justify-space-between align-center mb-2">
              <span class="text-caption font-weight-bold text-truncate" style="max-width: 120px;">
                {{ col.display_name || col.column_name }}
              </span>
              <v-chip color="info" size="x-small" variant="tonal">OBSERVED</v-chip>
            </div>
            <v-sparkline
              auto-draw
              :color="sparklineColor"
              height="40"
              line-width="2"
              :model-value="getHistoricalValues(col.column_name)"
              padding="4"
              smooth
            />
          </v-card>
        </v-col>
      </v-row>
    </div>

    <v-divider class="mb-6" />

    <!-- Section 2: Planned Drivers (Interactive) -->
    <div v-if="knownColumns.length > 0">
      <div class="d-flex align-center mb-4">
        <v-icon color="success" size="20">mdi-account-cog-outline</v-icon>
        <h3 class="text-subtitle-2 font-weight-bold ml-2">Planned Drivers</h3>
        <v-spacer />
        <v-btn
          v-if="hasChanges"
          class="recalculate-btn"
          color="primary"
          density="compact"
          prepend-icon="mdi-refresh"
          size="small"
          variant="flat"
          @click="emit('recalculate')"
        >
          Recalculate
        </v-btn>
      </div>

      <div v-for="col in knownColumns" :key="col.column_name" class="mb-4">
        <div class="d-flex align-center mb-2">
          <span class="text-caption font-weight-bold">{{ col.display_name || col.column_name }}</span>
          <v-spacer />
          <v-btn-toggle
            v-model="inputModes[col.column_name]"
            class="input-mode-toggle"
            density="compact"
            mandatory
            variant="tonal"
          >
            <v-btn icon="mdi-numeric" size="x-small" value="constant" />
            <v-btn icon="mdi-chart-line-variant" size="x-small" value="series" />
          </v-btn-toggle>
        </div>

        <v-expand-transition mode="out-in">
          <div :key="inputModes[col.column_name]">
            <!-- Constant Input -->
            <v-text-field
              v-if="inputModes[col.column_name] === 'constant'"
              v-model.number="localOverrides[col.column_name]"
              density="compact"
              hide-details
              label="Set constant value"
              prepend-inner-icon="mdi-equal"
              type="number"
              variant="outlined"
              @update:model-value="markChanged"
            />
            
            <!-- Series Input -->
            <v-textarea
              v-else
              v-model="seriesInputs[col.column_name]"
              auto-grow
              density="compact"
              hide-details
              label="Paste future values (CSV)"
              placeholder="e.g. 10.5, 11, 12.2..."
              rows="1"
              variant="outlined"
              @update:model-value="handleSeriesInput(col.column_name)"
            />
          </div>
        </v-expand-transition>
      </div>
    </div>

    <div v-if="unknownColumns.length === 0 && knownColumns.length === 0" class="text-center pa-8 text-disabled border-dashed rounded-lg">
      <v-icon size="32">mdi-chart-off</v-icon>
      <div class="mt-2 text-caption">No covariates detected in this model.</div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import type { ColumnOntology } from '@/types'
  import { computed, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'

  const store = useForecastStore()
  const emit = defineEmits(['recalculate'])

  const sparklineColor = 'rgba(var(--v-theme-info), 0.6)'

  // Categorize columns
  const knownColumns = computed(() => {
    return store.ontology?.columns.filter(c => c.role === 'covariate' && (c.covariate_type === 'known_future' || c.covariate_type === 'controllable')) || []
  })

  const unknownColumns = computed(() => {
    return store.ontology?.columns.filter(c => c.role === 'covariate' && (c.covariate_type === 'unknown_past' || c.covariate_type === 'exogenous')) || []
  })

  // State
  const localOverrides = ref<Record<string, number | number[] | null>>({})
  const inputModes = ref<Record<string, 'constant' | 'series'>>({})
  const seriesInputs = ref<Record<string, string>>({})
  const hasChanges = ref(false)

  // Initialize
  watch(() => store.ontology?.scenario_overrides, (overrides) => {
    if (!overrides) return
    localOverrides.value = { ...overrides }
    
    // Set modes based on existing data
    knownColumns.value.forEach(col => {
      const val = overrides[col.column_name]
      if (Array.isArray(val)) {
        inputModes.value[col.column_name] = 'series'
        seriesInputs.value[col.column_name] = val.join(', ')
      } else {
        inputModes.value[col.column_name] = 'constant'
      }
    })
  }, { immediate: true })

  function getHistoricalValues (colName: string): number[] {
    if (store.historyResults.length === 0) return []
    return store.historyResults.slice(-20).map(row => Number(row[colName] || 0))
  }

  function handleSeriesInput (colName: string) {
    const raw = seriesInputs.value[colName]
    const parsed = raw.split(',').map(s => s.trim()).filter(s => s !== '').map(Number).filter(n => !Number.isNaN(n))
    localOverrides.value[colName] = parsed
    markChanged()
  }

  function markChanged () {
    hasChanges.value = true
    // Update store immediately so recalculate uses fresh data
    if (store.ontology) {
      store.ontology.scenario_overrides = { ...localOverrides.value }
    }
  }
</script>

<style scoped>
.scenario-builder {
  user-select: none;
}

.input-mode-toggle {
  height: 24px !important;
}

.recalculate-btn {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(var(--v-theme-primary), 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(var(--v-theme-primary), 0); }
  100% { box-shadow: 0 0 0 0 rgba(var(--v-theme-primary), 0); }
}

.opacity-40 {
  opacity: 0.4;
}
</style>
