<template>
  <v-container class="fill-height pa-0" fluid>
    <v-row justify="center" align="center" class="fill-height ma-0">
      <v-col cols="12" md="10" lg="8" class="fill-height d-flex flex-column py-8">
        
        <!-- Journey Progress Tracker -->
        <v-card class="mb-6 pa-2" border flat bg-surface>
          <v-tabs
            v-model="store.step"
            align-tabs="center"
            color="primary"
            height="60"
            grow
          >
            <v-tab value="upload">
              <v-icon start icon="mdi-upload" class="d-none d-sm-flex"></v-icon>
              Data Upload
            </v-tab>
            <v-tab value="plan" :disabled="!store.ontology">
              <v-icon start icon="mdi-map-search-outline" class="d-none d-sm-flex"></v-icon>
              Mission Plan
            </v-tab>
            <v-tab value="cleaning" :disabled="!store.cleaningReport">
              <v-icon start icon="mdi-broom" class="d-none d-sm-flex"></v-icon>
              Data Cleaning
            </v-tab>
            <v-tab value="results" :disabled="store.forecastResults.length === 0">
              <v-icon start icon="mdi-chart-timeline-variant" class="d-none d-sm-flex"></v-icon>
              Analytic Output
            </v-tab>
          </v-tabs>
        </v-card>

        <v-card class="flex-grow-1 d-flex flex-column mb-6 overflow-hidden" color="surface" border elevation="2">
          <v-window
            v-model="store.step"
            class="fill-height"
            touchless
          >
            <v-window-item value="upload" class="fill-height">
              <UploadStage />
            </v-window-item>

            <v-window-item value="plan" class="fill-height">
              <PlanStage />
            </v-window-item>

            <v-window-item value="cleaning" class="fill-height">
              <CleaningStage />
            </v-window-item>

            <v-window-item value="results" class="fill-height">
              <ResultStage />
            </v-window-item>
          </v-window>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useForecastStore } from '@/stores/forecast'
import CleaningStage from './forecast/CleaningStage.vue'

const store = useForecastStore()
</script>


