<template>
  <v-card class="pa-8 bg-surface text-center position-relative" variant="outlined">

    <v-btn
      class="position-absolute top-0 right-0 ma-2"
      color="medium-emphasis"
      icon
      size="small"
      variant="text"
      @click="isEditing = !isEditing"
    >
      <v-icon>{{ isEditing ? 'mdi-check' : 'mdi-pencil' }}</v-icon>
      <v-tooltip activator="parent" location="top">
        {{ isEditing ? 'Finish Editing' : 'Edit Mission' }}
      </v-tooltip>
    </v-btn>

    <div v-if="!isEditing" class="text-h5 font-weight-light" style="line-height: 1.8;">
      <span class="text-medium-emphasis">Based on the data, I will forecast </span>

      <b class="text-primary font-weight-bold">{{ modelValue.target_col }}</b>

      <span class="text-medium-emphasis"> for the next </span>

      <b class="text-primary font-weight-bold">{{ modelValue.horizon }} {{ formatUnit(modelValue.frequency) }}s</b>

      <span class="text-medium-emphasis">, using </span>

      <b class="text-medium-emphasis text-decoration-underline">{{ modelValue.time_col }}</b>

      <span class="text-medium-emphasis"> as the timeline.</span>
      <br>
      <span class="text-medium-emphasis">I will assume future values are </span>

      <v-chip class="font-weight-bold" :color="modelValue.is_positive ? 'success' : 'warning'" size="small" variant="tonal">
        {{ modelValue.is_positive ? 'Strictly Positive' : 'Can be Negative' }}
      </v-chip>

      <span class="text-medium-emphasis"> to </span>

      <v-chip class="font-weight-bold" :color="getRiskColor(modelValue.risk_preference)" size="small" variant="tonal">
        {{ getRiskLabel(modelValue.risk_preference) }}
      </v-chip>
    </div>

    <div v-else class="text-h5 font-weight-light d-flex flex-wrap align-center justify-center gap-2" style="gap: 8px; line-height: 2.5;">
      <span class="text-medium-emphasis">I will forecast </span>

      <v-menu>
        <template #activator="{ props }">
          <v-chip
            v-bind="props"
            class="font-weight-bold"
            color="primary"
            size="large"
            variant="flat"
          >
            {{ modelValue.target_col }} <v-icon end icon="mdi-chevron-down" />
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
          <v-chip v-bind="props" color="secondary" size="large" variant="tonal">
            {{ formatUnit(modelValue.frequency) }}s <v-icon end icon="mdi-chevron-down" />
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
          <v-chip v-bind="props" color="grey-darken-1" size="large" variant="outlined">
            {{ modelValue.time_col }} <v-icon end icon="mdi-chevron-down" />
          </v-chip>
        </template>
        <v-list density="compact" max-height="300">
          <v-list-item v-for="col in allColumns" :key="col" :active="col === modelValue.time_col" @click="updateTime(col)">
            <v-list-item-title>{{ col }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <span class="text-medium-emphasis" style="width: 100%; display: block; margin-top: 8px;" />
      <span class="text-medium-emphasis">Assuming values are </span>

      <v-menu>
        <template #activator="{ props }">
          <v-chip v-bind="props" :color="modelValue.is_positive ? 'success' : 'warning'" size="large" variant="tonal">
            {{ modelValue.is_positive ? 'Strictly Positive' : 'Can be Negative' }} <v-icon end icon="mdi-chevron-down" />
          </v-chip>
        </template>
        <v-list density="compact">
          <v-list-item subtitle="e.g. Sales" title="Strictly Positive (+)" @click="updateConstraint(true)" />
          <v-list-item subtitle="e.g. Profit" title="Can be Negative (±)" @click="updateConstraint(false)" />
        </v-list>
      </v-menu>

      <span class="text-medium-emphasis"> to </span>

      <v-menu>
        <template #activator="{ props }">
          <v-chip v-bind="props" :color="getRiskColor(modelValue.risk_preference)" size="large" variant="tonal">
            {{ getRiskLabel(modelValue.risk_preference) }} <v-icon end icon="mdi-chevron-down" />
          </v-chip>
        </template>
        <v-list density="compact">
          <v-list-item
            subtitle="Average prediction"
            title="Achieve a balanced plan"
            @click="updateRiskPreference('balanced')"
          />
          <v-list-item
            subtitle="Upper bound (Safety Stock)"
            title="Minimize risk of stockouts"
            @click="updateRiskPreference('under_penalty')"
          />
          <v-list-item
            subtitle="Lower bound (Conservative)"
            title="Minimize risk of waste"
            @click="updateRiskPreference('over_penalty')"
          />
        </v-list>
      </v-menu>
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
</script>

<style scoped>
.centered-input :deep(input) {
  text-align: center;
}
</style>
