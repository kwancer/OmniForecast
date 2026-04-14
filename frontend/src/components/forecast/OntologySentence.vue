<template>
  <v-card class="ontology-sentence-card pa-6 pa-md-8 bg-surface text-center position-relative" variant="outlined">

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

    <!-- ═══ READING MODE ═══ -->
    <div v-if="!isEditing" class="text-h5 font-weight-light" style="line-height: 1.8;">
      <span class="text-medium-emphasis">Based on the data, I will forecast </span>
      <v-chip
        class="font-weight-bold mx-1"
        color="primary"
        size="large"
        style="vertical-align: baseline;"
        variant="tonal"
      >
        <v-icon size="16" start>mdi-target</v-icon>
        {{ modelValue.target_col }}
      </v-chip>
      <span class="text-medium-emphasis"> for the next </span>
      <span class="text-primary font-weight-bold">{{ modelValue.horizon }}</span>
      <span class="text-primary font-weight-bold"> {{ formatUnit(modelValue.frequency) }}s</span>
      <span class="text-medium-emphasis">, using </span>
      <v-chip
        class="font-weight-bold mx-1"
        color="secondary"
        size="small"
        style="vertical-align: baseline;"
        variant="outlined"
      >
        <v-icon size="14" start>mdi-clock-outline</v-icon>
        {{ modelValue.time_col }}
      </v-chip>
      <span class="text-medium-emphasis"> as the timeline.</span>

      <span class="d-block mt-4" />

      <span class="text-medium-emphasis">I expect these projections to be </span>
      <v-chip
        class="font-weight-bold"
        :color="modelValue.is_positive ? 'success' : 'warning'"
        size="small"
        style="vertical-align: middle; margin-top: -4px;"
        variant="tonal"
      >
        <v-icon size="14" start>{{ modelValue.is_positive ? 'mdi-trending-up' : 'mdi-swap-vertical' }}</v-icon>
        {{ modelValue.is_positive ? 'strictly positive' : 'positive or negative' }}
      </v-chip>
      <span class="text-medium-emphasis">, and my main objective is to </span>
      <v-chip
        class="font-weight-bold"
        :color="getRiskColor(modelValue.risk_preference)"
        size="small"
        style="vertical-align: middle; margin-top: -4px;"
        variant="tonal"
      >
        <v-icon size="14" start>{{ getRiskIcon(modelValue.risk_preference) }}</v-icon>
        {{ getRiskLabel(modelValue.risk_preference).toLowerCase() }}
      </v-chip>
      <span class="text-medium-emphasis">.</span>
    </div>

    <!-- ═══ EDITING MODE ═══ -->
    <div v-else class="text-h5 font-weight-light d-flex flex-wrap align-center justify-center gap-2" style="gap: 8px; line-height: 2.5;">
      <span class="text-medium-emphasis">I will forecast </span>

      <v-menu>
        <template #activator="{ props }">
          <v-chip
            v-bind="props"
            class="font-weight-bold editable-chip"
            color="primary"
            size="large"
            variant="flat"
          >
            <v-icon size="16" start>mdi-target</v-icon>
            {{ modelValue.target_col }} <v-icon end icon="mdi-chevron-down" size="16" />
          </v-chip>
        </template>
        <v-list density="compact" max-height="300">
          <v-list-item v-for="col in allColumns" :key="col" :active="col === modelValue.target_col" @click="updateTarget(col)">
            <v-list-item-title>{{ col }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <span class="text-medium-emphasis"> for the next </span>

      <div style="width: 80px; display: inline-block;">
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
          <v-chip
            v-bind="props"
            class="editable-chip"
            color="secondary"
            size="large"
            variant="tonal"
          >
            {{ formatUnit(modelValue.frequency) }}s <v-icon end icon="mdi-chevron-down" size="16" />
          </v-chip>
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
          <v-chip
            v-bind="props"
            class="editable-chip"
            color="grey-darken-1"
            size="large"
            variant="outlined"
          >
            <v-icon size="14" start>mdi-clock-outline</v-icon>
            {{ modelValue.time_col }} <v-icon end icon="mdi-chevron-down" size="16" />
          </v-chip>
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
          <v-chip
            v-bind="props"
            class="editable-chip"
            :color="modelValue.is_positive ? 'success' : 'warning'"
            size="large"
            variant="tonal"
          >
            <v-icon size="14" start>{{ modelValue.is_positive ? 'mdi-trending-up' : 'mdi-swap-vertical' }}</v-icon>
            {{ modelValue.is_positive ? 'strictly positive' : 'positive or negative' }} <v-icon end icon="mdi-chevron-down" size="16" />
          </v-chip>
        </template>
        <v-list density="compact">
          <v-list-item subtitle="e.g. Sales" title="Strictly positive (+)" @click="updateConstraint(true)" />
          <v-list-item subtitle="e.g. Profit" title="Positive or negative (±)" @click="updateConstraint(false)" />
        </v-list>
      </v-menu>

      <span class="text-medium-emphasis">, and my main objective is to </span>

      <v-menu>
        <template #activator="{ props }">
          <v-chip
            v-bind="props"
            class="editable-chip"
            :color="getRiskColor(modelValue.risk_preference)"
            size="large"
            variant="tonal"
          >
            <v-icon size="14" start>{{ getRiskIcon(modelValue.risk_preference) }}</v-icon>
            {{ getRiskLabel(modelValue.risk_preference).toLowerCase() }} <v-icon end icon="mdi-chevron-down" size="16" />
          </v-chip>
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

  </v-card>
</template>

<script setup lang="ts">
  import type { RiskPreference } from '@/types'
  import { ref, watch } from 'vue'

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
  }>()

  const emit = defineEmits(['update:modelValue'])

  const isEditing = ref(false)
  const localHorizon = ref(sentenceProps.modelValue.horizon)

  watch(() => sentenceProps.modelValue.horizon, val => localHorizon.value = val)

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

.centered-input :deep(input) {
  text-align: center;
}
</style>
