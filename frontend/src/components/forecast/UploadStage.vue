<template>
  <v-container style="max-width: 600px;">
    <div class="text-center mb-8">
      <h2 class="text-h4 font-header mb-2">Start Forecasting</h2>
      <p class="text-body-1 text-medium-emphasis">Upload historical data and define your forecasting objective.</p>
    </div>

    <v-file-input
      v-model="file"
      label="Historical Data (CSV)"
      prepend-icon="mdi-database"
      accept=".csv"
      class="w-100 mb-4"
      color="primary"
    ></v-file-input>

    <v-textarea
      v-model="intent"
      label="Operational Intent"
      placeholder="e.g., Forecast sales for the next 12 months focusing on seasonality..."
      prepend-icon="mdi-text-box-search-outline"
      rows="4"
      class="w-100 mb-6"
      color="primary"
    ></v-textarea>

    <v-btn
      color="primary"
      block
      @click="store.analyzeIntent"
      :loading="store.loading"
      :disabled="!file || !intent"
      size="large"
    >
      <v-icon start>mdi-radar</v-icon>
      Analyze Signal
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
