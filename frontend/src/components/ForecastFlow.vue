<template>
  <v-container class="fill-height pa-0" fluid>
    <v-row justify="center" align="center" class="fill-height ma-0">
      <v-col cols="12" md="10" lg="8" class="fill-height d-flex flex-column py-8">
        
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

const store = useForecastStore()
</script>

<style>
.font-header {
  font-family: 'Space Grotesk', sans-serif !important;
}
.font-mono {
  font-family: 'JetBrains Mono', monospace !important;
}
</style>
