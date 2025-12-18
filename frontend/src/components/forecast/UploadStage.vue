<template>
  <v-container style="max-width: 600px;">
    <div class="text-center mb-6">
      <h2 class="text-h4 font-header mb-2">Start Forecasting</h2>
      <p class="text-body-1 text-medium-emphasis">Upload historical data and define your forecasting objective.</p>
    </div>

    <v-alert
      type="info"
      variant="outlined"
      class="mb-6"
      border="start"
      density="compact"
    >
      <div class="text-body-2">
        <strong>Deterministic Workflow:</strong> AI assists in understanding your intent and mapping the data ontology, but all forecasting logic and code execution are deterministic. No code is generated on-the-fly.
      </div>
    </v-alert>

    <div class="d-flex align-center mb-1">
      <v-file-input
        v-model="file"
        label="Historical Data (CSV)"
        prepend-icon="mdi-database"
        accept=".csv"
        class="w-100"
        color="primary"
        hide-details
      ></v-file-input>
      <v-tooltip location="top">
        <template v-slot:activator="{ props }">
          <v-icon v-bind="props" color="medium-emphasis" class="ml-2">mdi-help-circle-outline</v-icon>
        </template>
        <span>Upload a CSV file containing at least one date column and one numeric value column.</span>
      </v-tooltip>
    </div>

    <div class="d-flex justify-end mb-4">
      <v-btn
        variant="text"
        size="small"
        color="secondary"
        prepend-icon="mdi-auto-fix"
        @click="store.loadSampleData"
        class="text-none"
      >
        Try with Sample Sales Data
      </v-btn>
    </div>

    <v-textarea
      v-model="intent"
      label="Your Prediction Goal"
      placeholder="e.g. Forecast sales for the next 12 months, focusing on seasonal trends..."
      prepend-icon="mdi-text-box-search-outline"
      rows="4"
      class="w-100 mb-6"
      color="primary"
      hint="Describe what you want to predict in plain English."
      persistent-hint
    ></v-textarea>

    <v-btn
      color="primary"
      block
      @click="store.analyzeIntent"
      :loading="store.loading"
      :disabled="!file || !intent"
      size="x-large"
      elevation="2"
    >
      Check Data & Continue
      <v-icon end>mdi-chevron-right</v-icon>
    </v-btn>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useForecastStore } from '@/stores/forecast'

const store = useForecastStore()

const file = computed({
  get: () => store.file,
  set: (val) => store.setFile(val)
})

const intent = computed({
  get: () => store.intent,
  set: (val) => store.setIntent(val)
})
</script>
