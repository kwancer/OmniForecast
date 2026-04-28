<template>
  <v-card class="ontology-sentence-card pa-6 pa-md-8 bg-surface position-relative" :class="{ 'text-center': uiMode === 'madlibs' }" variant="outlined">

    <!-- Edit toggle chip (top right) -->
    <v-chip
      class="position-absolute edit-toggle"
      :color="isEditing ? 'primary' : 'default'"
      :prepend-icon="isEditing ? 'mdi-check' : 'mdi-pencil'"
      size="small"
      :variant="isEditing ? 'flat' : 'tonal'"
      @click="isEditing = !isEditing"
    >
      {{ isEditing ? 'Done' : 'Edit' }}
    </v-chip>

    <!-- ═══ MADLIBS MODE (Option 1) ═══ -->
    <template v-if="uiMode === 'madlibs'">
      <!-- READING MODE -->
      <div v-if="!isEditing" class="text-h5 font-weight-light" style="line-height: 1.8;">
        <span class="text-medium-emphasis">Based on the data, I will forecast </span>
        <span class="font-weight-medium text-primary variable-text px-1">{{ modelValue.target_col }}</span>
        <span class="text-medium-emphasis"> for the next </span>
        <span class="text-primary font-weight-medium px-1">{{ modelValue.horizon }} {{ formatUnit(modelValue.frequency) }}s</span>
        <v-tooltip v-if="horizonConfidence < 0.9" location="top">
          <template #activator="{ props }">
            <v-icon
              v-bind="props"
              class="ml-1"
              color="warning"
              size="16"
              style="vertical-align: middle; margin-top: -4px;"
            >mdi-alert-circle-outline</v-icon>
          </template>
          <span>Horizon confidence: {{ Math.round(horizonConfidence * 100) }}% — {{ horizonRationale || 'The system guessed this horizon from context.' }}</span>
        </v-tooltip>
        <span class="text-medium-emphasis">, using </span>
        <span class="font-weight-medium text-secondary variable-text px-1">{{ modelValue.time_col }}</span>
        <span class="text-medium-emphasis"> as the timeline.</span>

        <span class="d-block mt-4" />

        <span class="text-medium-emphasis">I expect these projections to be </span>
        <span class="font-weight-medium px-1" :class="modelValue.is_positive ? 'text-success' : 'text-warning'">
          {{ modelValue.is_positive ? 'strictly positive' : 'positive or negative' }}
        </span>
        <span class="text-medium-emphasis">, and my main objective is to </span>
        <span class="font-weight-medium px-1" :class="'text-' + getRiskColor(modelValue.risk_preference)">
          {{ getRiskLabel(modelValue.risk_preference).toLowerCase() }}
        </span>
        <span class="text-medium-emphasis">.</span>
      </div>

      <!-- EDITING MODE -->
      <div v-else class="text-h5 font-weight-light d-flex flex-wrap align-center justify-center gap-2" style="gap: 8px; line-height: 2.5;">
        <span class="text-medium-emphasis">I will forecast </span>

        <v-menu>
          <template #activator="{ props }">
            <span v-bind="props" class="font-weight-medium text-primary variable-text px-1 editable-item">
              {{ modelValue.target_col }} <v-icon size="16">mdi-chevron-down</v-icon>
            </span>
          </template>
          <v-list density="compact" max-height="300">
            <v-list-item v-for="col in allColumns" :key="col" :active="col === modelValue.target_col" @click="updateTarget(col)">
              <v-list-item-title>{{ col }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <span class="text-medium-emphasis"> for the next </span>

        <div style="width: 60px; display: inline-block;">
          <v-text-field
            v-model.number="localHorizon"
            class="centered-input text-h6 font-weight-bold text-primary"
            density="compact"
            hide-details
            single-line
            type="number"
            variant="underlined"
            @update:model-value="updateHorizon"
          />
        </div>

        <v-menu>
          <template #activator="{ props }">
            <span v-bind="props" class="font-weight-medium text-primary variable-text px-1 editable-item">
              {{ formatUnit(modelValue.frequency) }}s <v-icon size="16">mdi-chevron-down</v-icon>
            </span>
          </template>
          <v-list density="compact">
            <v-list-item v-for="unit in ['day', 'week', 'month', 'quarter', 'year']" :key="unit" @click="updateFrequency(unit)">
              <v-list-item-title>{{ formatUnit(unit) }}s</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <span class="text-medium-emphasis"> using </span>

        <v-menu>
          <template #activator="{ props }">
            <span v-bind="props" class="font-weight-medium text-secondary variable-text px-1 editable-item">
              {{ modelValue.time_col }} <v-icon size="16">mdi-chevron-down</v-icon>
            </span>
          </template>
          <v-list density="compact" max-height="300">
            <v-list-item v-for="col in allColumns" :key="col" :active="col === modelValue.time_col" @click="updateTime(col)">
              <v-list-item-title>{{ col }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <span class="text-medium-emphasis"> as the timeline.</span>

        <span class="text-medium-emphasis" style="width: 100%; display: block; margin-top: 8px;" />

        <span class="text-medium-emphasis">I expect these projections to be </span>

        <v-menu>
          <template #activator="{ props }">
            <span v-bind="props" class="font-weight-medium variable-text px-1 editable-item" :class="modelValue.is_positive ? 'text-success' : 'text-warning'">
              {{ modelValue.is_positive ? 'strictly positive' : 'positive or negative' }} <v-icon size="16">mdi-chevron-down</v-icon>
            </span>
          </template>
          <v-list density="compact">
            <v-list-item subtitle="e.g. Sales" title="Strictly positive (+)" @click="updateConstraint(true)" />
            <v-list-item subtitle="e.g. Profit" title="Positive or negative (±)" @click="updateConstraint(false)" />
          </v-list>
        </v-menu>

        <span class="text-medium-emphasis">, and my main objective is to </span>

        <v-menu>
          <template #activator="{ props }">
            <span v-bind="props" class="font-weight-medium variable-text px-1 editable-item" :class="'text-' + getRiskColor(modelValue.risk_preference)">
              {{ getRiskLabel(modelValue.risk_preference).toLowerCase() }} <v-icon size="16">mdi-chevron-down</v-icon>
            </span>
          </template>
          <v-list density="compact">
            <v-list-item
              subtitle="Average prediction"
              title="Achieve a balanced forecast"
              @click="updateRiskPreference('balanced')"
            />
            <v-list-item
              subtitle="Upper bound (Safety Stock)"
              title="Minimize the risk of stockouts"
              @click="updateRiskPreference('under_penalty')"
            />
            <v-list-item
              subtitle="Lower bound (Conservative)"
              title="Minimize the risk of waste"
              @click="updateRiskPreference('over_penalty')"
            />
          </v-list>
        </v-menu>
        <span class="text-medium-emphasis">.</span>
      </div>
    </template>

    <!-- ═══ GRID MODE (Option 2) ═══ -->
    <template v-else-if="uiMode === 'grid'">
      <v-row class="ma-0 align-center">
        <!-- Target -->
        <v-col class="py-2" cols="12" md="4" sm="6">
          <div class="text-caption text-medium-emphasis mb-1">Target Metric</div>
          <div v-if="!isEditing" class="text-body-1 font-weight-bold text-primary">{{ modelValue.target_col }}</div>
          <v-select
            v-else
            v-model="localModelValue.target_col"
            density="compact"
            hide-details
            :items="allColumns"
            variant="outlined"
            @update:model-value="(v) => updateTarget(v)"
          />
        </v-col>

        <!-- Horizon & Frequency -->
        <v-col class="py-2" cols="12" md="4" sm="6">
          <div class="text-caption text-medium-emphasis mb-1">Time Horizon</div>
          <div v-if="!isEditing" class="text-body-1 font-weight-bold">
            {{ modelValue.horizon }} {{ formatUnit(modelValue.frequency) }}s
          </div>
          <div v-else class="d-flex align-center gap-2" style="gap: 8px;">
            <v-text-field
              v-model.number="localHorizon"
              density="compact"
              hide-details
              style="width: 80px;"
              type="number"
              variant="outlined"
              @update:model-value="updateHorizon"
            />
            <v-select
              v-model="localModelValue.frequency"
              density="compact"
              hide-details
              :item-title="(item) => formatUnit(item) + 's'"
              :items="['day', 'week', 'month', 'quarter', 'year']"
              style="flex-grow: 1;"
              variant="outlined"
              @update:model-value="(v) => updateFrequency(v)"
            />
          </div>
        </v-col>

        <!-- Timeline -->
        <v-col class="py-2" cols="12" md="4" sm="6">
          <div class="text-caption text-medium-emphasis mb-1">Timeline Index</div>
          <div v-if="!isEditing" class="text-body-1 font-weight-bold text-secondary">{{ modelValue.time_col }}</div>
          <v-select
            v-else
            v-model="localModelValue.time_col"
            density="compact"
            hide-details
            :items="allColumns"
            variant="outlined"
            @update:model-value="(v) => updateTime(v)"
          />
        </v-col>

        <!-- Constraints -->
        <v-col class="py-2 mt-sm-2" cols="12" md="4" sm="6">
          <div class="text-caption text-medium-emphasis mb-1">Value Constraint</div>
          <div v-if="!isEditing" class="text-body-1 font-weight-bold" :class="modelValue.is_positive ? 'text-success' : 'text-warning'">
            {{ modelValue.is_positive ? 'Strictly positive (+)' : 'Positive or negative (±)' }}
          </div>
          <v-select
            v-else
            v-model="localModelValue.is_positive"
            density="compact"
            hide-details
            :items="[{ title: 'Strictly positive (+)', value: true }, { title: 'Positive or negative (±)', value: false }]"
            variant="outlined"
            @update:model-value="(v) => updateConstraint(v)"
          />
        </v-col>

        <!-- Objective -->
        <v-col class="py-2 mt-sm-2" cols="12" md="8" sm="6">
          <div class="text-caption text-medium-emphasis mb-1">Main Objective</div>
          <div v-if="!isEditing" class="text-body-1 font-weight-bold" :class="'text-' + getRiskColor(modelValue.risk_preference)">
            {{ getRiskLabel(modelValue.risk_preference) }}
          </div>
          <v-select
            v-else
            v-model="localModelValue.risk_preference"
            density="compact"
            hide-details
            :items="[
              { title: 'Balanced Plan (Average prediction)', value: 'balanced' },
              { title: 'Minimize Stockouts (Safety Stock)', value: 'under_penalty' },
              { title: 'Minimize Waste (Conservative)', value: 'over_penalty' }
            ]"
            variant="outlined"
            @update:model-value="(v) => updateRiskPreference(v)"
          />
        </v-col>
      </v-row>
    </template>

  </v-card>
</template>

<script setup lang="ts">
  import type { RiskPreference } from '@/types'
  import { computed, ref, watch } from 'vue'

  const isAlternativeUi = import.meta.env.VITE_ALTERNATIVE_UI === 'true'
  const uiMode = isAlternativeUi ? 'grid' : 'madlibs'

  export interface SentenceState {
    target_col: string
    time_col: string
    horizon: number
    frequency: string
    is_positive: boolean
    risk_preference: RiskPreference
  }

  const sentenceProps = defineProps<{
    modelValue: SentenceState
    allColumns: string[]
    horizonConfidenceScore?: number
    horizonConfidenceRationale?: string
  }>()

  const emit = defineEmits(['update:modelValue'])

  const isEditing = ref(false)
  const localHorizon = ref(sentenceProps.modelValue.horizon)
  const localModelValue = ref({ ...sentenceProps.modelValue })

  const horizonConfidence = computed(() => sentenceProps.horizonConfidenceScore ?? 1)
  const horizonRationale = computed(() => sentenceProps.horizonConfidenceRationale ?? '')

  watch(() => sentenceProps.modelValue.horizon, val => localHorizon.value = val)
  watch(() => sentenceProps.modelValue, val => {
    localModelValue.value = { ...val }
  }, { deep: true })

  const updateTarget = (col: string) => emit('update:modelValue', { ...sentenceProps.modelValue, target_col: col })
  const updateTime = (col: string) => emit('update:modelValue', { ...sentenceProps.modelValue, time_col: col })
  const updateFrequency = (unit: string) => emit('update:modelValue', { ...sentenceProps.modelValue, frequency: unit })
  const updateConstraint = (isPositive: boolean) => emit('update:modelValue', { ...sentenceProps.modelValue, is_positive: isPositive })
  const updateHorizon = (val: string | number) => emit('update:modelValue', { ...sentenceProps.modelValue, horizon: Number(val) })
  const updateRiskPreference = (pref: RiskPreference) => emit('update:modelValue', { ...sentenceProps.modelValue, risk_preference: pref })

  const formatUnit = (unit: string) => unit ? unit.charAt(0).toUpperCase() + unit.slice(1) : ''

  function getRiskLabel (pref: RiskPreference | undefined) {
    switch (pref) {
      case 'under_penalty': {
        return 'Minimize Stockouts'
      }
      case 'over_penalty': {
        return 'Minimize Waste'
      }
      default: {
        return 'Balanced Plan'
      }
    }
  }

  function getRiskColor (pref: RiskPreference | undefined) {
    switch (pref) {
      case 'under_penalty': {
        return 'error'
      }
      case 'over_penalty': {
        return 'info'
      }
      default: {
        return 'accent'
      }
    }
  }

  function getRiskIcon (pref: RiskPreference | undefined) {
    switch (pref) {
      case 'under_penalty': {
        return 'mdi-shield-alert-outline'
      }
      case 'over_penalty': {
        return 'mdi-leaf'
      }
      default: {
        return 'mdi-scale-balance'
      }
    }
  }
</script>

<style scoped>
.ontology-sentence-card {
  border-color: rgba(var(--v-theme-primary), 0.15) !important;
  background: linear-gradient(
    135deg,
    rgba(var(--v-theme-primary), 0.02) 0%,
    rgba(var(--v-theme-surface), 1) 50%,
    rgba(var(--v-theme-secondary), 0.02) 100%
  ) !important;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.ontology-sentence-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.25) !important;
}

.edit-toggle {
  top: 12px;
  right: 12px;
  z-index: 1;
  cursor: pointer;
}

.editable-chip {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.editable-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.variable-text {
  border-bottom: 2px dashed rgba(var(--v-theme-primary), 0.3);
  transition: all 0.2s ease;
}

.editable-item {
  cursor: pointer;
}

.editable-item:hover {
  border-bottom-style: solid;
  border-bottom-color: rgba(var(--v-theme-primary), 0.8);
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-radius: 4px;
}

.centered-input :deep(input) {
  text-align: center;
}
</style>
