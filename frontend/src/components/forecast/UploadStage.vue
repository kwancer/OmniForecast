<template>
  <v-container class="bg-background fill-height d-flex flex-column justify-center" fluid>
    <v-row class="flex-grow-0 w-100" justify="center">
      <v-col cols="12" md="8" sm="10">
        <div class="text-center mb-6">
          <h2 class="text-h4 font-header mb-2">Start Prediction</h2>
          <p class="text-body-1 text-medium-emphasis">Upload historical data and define your prediction objective. </p>
        </div>

        <v-alert
          border="start"
          class="mb-6"
          density="compact"
          type="info"
          variant="outlined"
        >
          <div class="text-body-2">
            AI assists in understanding your intent and converting it into a computer-usable format, but all forecasting logic and code execution are deterministic. No code is generated on-the-fly.
          </div>
        </v-alert>

        <div class="d-flex align-center mb-1">
          <v-file-input
            v-model="file"
            accept=".csv"
            class="w-100"
            color="primary"
            hide-details
            label="Historical Data (CSV)"
            prepend-icon="mdi-database"
          />
          <v-tooltip location="top">
            <template #activator="{ props }">
              <v-icon v-bind="props" class="ml-2" color="medium-emphasis">mdi-help-circle-outline</v-icon>
            </template>
            <span>Upload a CSV file containing at least one date column and one numeric value column.</span>
          </v-tooltip>
        </div>

        <div class="d-flex justify-end mb-4">
          <v-btn
            class="text-none"
            color="secondary"
            prepend-icon="mdi-auto-fix"
            size="small"
            variant="text"
            @click="store.loadSampleData"
          >
            Try with Sample Sales Data
          </v-btn>
        </div>

        <v-textarea
          v-model="intent"
          class="w-100 mb-6"
          color="primary"
          hint="Describe what you want to predict in plain English."
          persistent-hint
          placeholder="e.g. Forecast sales for the next 12 months, focusing on seasonal trends..."
          prepend-icon="mdi-text-box-search-outline"
          rows="4"
        />

        <v-btn
          block
          color="primary"
          :disabled="!file || !intent"
          elevation="2"
          :loading="store.loading"
          size="x-large"
          @click="store.analyzeIntent"
        >
          Continue
          <v-icon end>mdi-chevron-right</v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { useForecastStore } from '@/stores/forecast'

  const store = useForecastStore()

  const file = computed({
    get: () => store.file,
    set: val => store.setFile(val),
  })

  const intent = computed({
    get: () => store.intent,
    set: val => store.setIntent(val),
  })
</script>
