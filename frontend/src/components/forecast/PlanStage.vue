<template>
  <v-container class="fill-height d-flex flex-column bg-background pa-2 pa-md-4" fluid>
    <div class="d-flex align-center mb-2 mb-md-6 flex-shrink-0">
      <v-btn icon="mdi-arrow-left" variant="text" @click="store.setStep('upload')" />
      <h2 class="text-h5 font-header ml-2">Forecasting Strategy</h2>
    </div>

    <v-row class="ma-0 overflow-y-auto">
      <v-col class="h-md-100" cols="12" md="6">
        <OntologyViewer :ontology="store.ontology" />
      </v-col>

      <v-col class="h-md-100" cols="12" md="6">
        <v-card border class="pa-4 pa-md-6 bg-surface mb-6" variant="outlined">
          <div class="d-flex align-center mb-4">
            <div>
              <div class="text-h6 font-weight-bold">Modelling Strategy</div>
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
            class="mb-6"
            color="info"
            density="compact"
            variant="tonal"
          >
            <div class="text-caption">
              <strong>How it works:</strong> {{ store.ontology?.model_metadata?.description }}
            </div>
            <v-btn
              v-if="store.ontology?.model_metadata?.educational_video_url"
              class="mt-2 text-none"
              :href="store.ontology.model_metadata.educational_video_url"
              prepend-icon="mdi-youtube"
              size="x-small"
              target="_blank"
              variant="text"
            >
              Learn the mathematical foundation (Video)
            </v-btn>
          </v-alert>

          <v-btn
            block
            color="primary"
            elevation="2"
            :loading="store.loading"
            size="x-large"
            @click="store.executeForecast"
          >
            Continue
            <v-icon end>mdi-chevron-right</v-icon>
          </v-btn>
        </v-card>

        <v-alert
          class="mb-4"
          color="info"
          density="compact"
          icon="mdi-information-outline"
          variant="tonal"
        >
          <div class="text-caption">
            All operations are deterministic based on the confirmed ontology.
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
