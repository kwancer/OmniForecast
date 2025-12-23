<template>
  <v-container class="fill-height d-flex flex-column bg-background pa-2 pa-md-4" fluid>
    <div class="d-flex align-center mb-2 mb-md-6 flex-shrink-0">
      <v-btn icon="mdi-arrow-left" variant="text" @click="store.setStep('upload')"></v-btn>
      <h2 class="text-h5 font-header ml-2">Forecasting Strategy</h2>
    </div>

    <v-row class="flex-grow-1 overflow-hidden ma-0">
      <v-col cols="12" md="7" class="h-100 overflow-y-auto pr-md-4 pb-4">
        <OntologyViewer :ontology="store.ontology" />
      </v-col>
      
      <v-col cols="12" md="5" class="h-100 d-flex flex-column justify-start overflow-y-auto mt-0 mt-md-0">
        <v-card variant="outlined" border class="pa-4 pa-md-6 bg-surface mb-6">
          <div class="d-flex align-center mb-4">
            <v-avatar color="secondary" variant="tonal" size="48" class="mr-4">
              <v-icon icon="mdi-robot-confused-outline" size="28" v-if="!store.ontology"></v-icon>
              <v-icon icon="mdi-robot-check-outline" size="28" v-else></v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold">Strategy Overview</div>
              <div class="text-caption text-medium-emphasis">Modelling Strategy Initialised</div>
            </div>
          </div>

          <p class="text-body-2 mb-2 text-primary font-weight-bold">
            Selected: {{ store.ontology?.model_metadata?.name || 'Standard Model' }}
          </p>

          <p class="text-body-2 mb-4 text-medium-emphasis">
            {{ store.ontology?.model_metadata?.rationale || 'The system has mapped your data structure. We are now ready to execute the prediction engine using a customised regression model.' }}
          </p>
          
          <v-alert
            v-if="store.ontology?.model_metadata?.description"
            variant="tonal"
            color="info"
            density="compact"
            class="mb-6"
          >
            <div class="text-caption">
              <strong>How it works:</strong> {{ store.ontology?.model_metadata?.description }}
            </div>
            <v-btn
              v-if="store.ontology?.model_metadata?.educational_video_url"
              :href="store.ontology.model_metadata.educational_video_url"
              target="_blank"
              variant="text"
              size="x-small"
              class="mt-2 text-none"
              prepend-icon="mdi-youtube"
            >
              Learn the mathematical foundation (Video)
            </v-btn>
          </v-alert>

          <v-btn
            color="primary"
            size="x-large"
            block
            @click="store.executeForecast"
            :loading="store.loading"
            elevation="2"
          >
            Execute & Continue
            <v-icon end>mdi-chevron-right</v-icon>
          </v-btn>
        </v-card>

        <v-alert
          color="info"
          variant="tonal"
          icon="mdi-information-outline"
          class="mb-4"
          density="compact"
        >
          <div class="text-caption">
            All operations are now deterministic based on the confirmed ontology.
          </div>
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useForecastStore } from '@/stores/forecast'
import OntologyViewer from './OntologyViewer.vue'

const store = useForecastStore()
</script>
