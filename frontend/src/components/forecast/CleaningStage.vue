<template>
  <v-container class="fill-height d-flex flex-column">
    <div class="d-flex align-center mb-6">
      <v-btn icon="mdi-arrow-left" variant="text" @click="store.setStep('plan')"></v-btn>
      <h2 class="text-h5 font-header ml-2">Data Preparation</h2>
    </div>

    <v-row class="flex-grow-1 overflow-hidden">
      <v-col cols="12" md="8" class="h-100 overflow-y-auto">
        <v-card variant="outlined" class="mb-4 bg-surface">
          <v-card-title class="text-subtitle-1 font-weight-bold d-flex align-center">
            <v-icon start color="primary">mdi-format-list-checks</v-icon>
            System Corrections Report
          </v-card-title>
          <v-divider></v-divider>
          
          <v-list lines="two" v-if="store.cleaningReport?.actions.length">
            <template v-for="(action, index) in store.cleaningReport?.actions" :key="index">
              <v-list-item>
                <template v-slot:prepend>
                  <v-avatar :color="getActionColor(action.action)" size="40" variant="tonal">
                    <v-icon :icon="getActionIcon(action.action)"></v-icon>
                  </v-avatar>
                </template>
                
                <v-list-item-title class="font-weight-bold">
                  {{ action.column }}: {{ formatActionName(action.action) }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-wrap">
                  {{ action.description }}
                </v-list-item-subtitle>
              </v-list-item>
              <v-divider v-if="index < (store.cleaningReport?.actions.length ?? 0) - 1" inset></v-divider>
            </template>
          </v-list>
          
          <v-card-text v-else class="text-center py-8 text-medium-emphasis">
            No specific transformations were required. The dataset was already in a model-ready state.
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4" class="d-flex flex-column">

        <v-card color="primary" variant="tonal" class="pa-4 mb-4">
          <div class="text-overline mb-2">Preparation Summary</div>

          <div class="d-flex justify-space-between mb-1">
            <span class="text-caption">Original Shape:</span>
            <span class="text-caption font-weight-bold">{{ store.cleaningReport?.initial_shape.join(' x ') }}</span>
          </div>
          <div class="d-flex justify-space-between mb-3">
            <span class="text-caption">Final Shape:</span>
            <span class="text-caption font-weight-bold">{{ store.cleaningReport?.final_shape.join(' x ') }}</span>
          </div>
          <p class="text-body-2 mb-0">
            {{ store.cleaningReport?.summary }}
          </p>
        </v-card>

        <v-spacer></v-spacer>

        <v-card variant="flat" border class="pa-4 bg-surface">
          <p class="text-caption text-medium-emphasis mb-4">
            The system has prepared your data for modelling. Proceed to view the forecast results.
          </p>
          <v-btn
            color="primary"
            block
            size="large"
            @click="store.setStep('results')"
            elevation="2"
          >
            Continue
            <v-icon end>mdi-chevron-right</v-icon>
          </v-btn>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useForecastStore } from '@/stores/forecast'

const store = useForecastStore()

const getActionIcon = (action: string) => {
  switch (action) {
    case 'normalization': return 'mdi-format-letter-case'
    case 'type_conversion': return 'mdi-variable'
    case 'aggregation': return 'mdi-layers-triple'
    case 'resampling': return 'mdi-calendar-clock'
    case 'gap_filling': return 'mdi-plus-box'
    case 'imputation': return 'mdi-eyedropper'
    default: return 'mdi-wrench'
  }
}

const getActionColor = (action: string) => {
  switch (action) {
    case 'imputation': return 'orange'
    case 'resampling': return 'blue'
    case 'gap_filling': return 'purple'
    default: return 'primary'
  }
}

const formatActionName = (name: string) => {
  return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}
</script>
