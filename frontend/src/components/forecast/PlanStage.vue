<template>
  <v-container class="fill-height d-flex flex-column">
    <div class="d-flex align-center mb-6">
      <v-btn icon="mdi-arrow-left" variant="text" @click="store.setStep('upload')"></v-btn>
      <h2 class="text-h5 font-header ml-2">Mission Plan</h2>
    </div>

    <v-row class="fill-height overflow-y-auto">
      <v-col cols="12" md="6">
        <v-card variant="outlined" class="h-100 pa-4">
          <div class="text-overline text-secondary mb-2">DETECTED ONTOLOGY</div>
          <pre class="font-mono text-body-2" style="white-space: pre-wrap;">{{ JSON.stringify(store.ontology, null, 2) }}</pre>
        </v-card>
      </v-col>
      <v-col cols="12" md="6" class="d-flex flex-column justify-center">
        <v-alert
          color="secondary"
          variant="tonal"
          icon="mdi-robot"
          title="System Analysis"
          class="mb-6"
        >
          The Intent Layer has mapped your request. The system is ready to execute the forecasting engine using an Additive Regression Model.
        </v-alert>

        <v-btn
          color="primary"
          size="x-large"
          block
          @click="store.executeForecast"
          :loading="store.loading"
        >
          <v-icon start>mdi-rocket-launch</v-icon>
          Execute Forecast
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useForecastStore } from '@/stores/forecast'

const store = useForecastStore()
</script>
