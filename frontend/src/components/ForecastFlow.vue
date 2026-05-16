<template>
  <v-container class="fill-height pa-0" fluid>
    <v-row class="fill-height ma-0" justify="center">
      <v-col class="fill-height pa-0" cols="12">
        <div class="fill-height d-flex flex-column">
          <!-- Progress Overlay (shown when forecast is running) -->
          <transition name="fade">
            <div v-if="store.showProgress" class="flex-grow-1 fill-height">
              <ProgressView
                :completed="store.progressCompleted"
                :current="store.progressCurrent"
                :current-model="store.progressCurrentModel"
                :total="store.progressTotal"
              />
            </div>
          </transition>

          <!-- Main Content Windows -->
          <v-window
            v-show="!store.showProgress"
            v-model="currentStepIndex"
            class="flex-grow-1"
            style="height: 100%"
            :touch="false"
          >
            <v-window-item class="fill-height" value="1">
              <UploadStage v-if="currentStepIndex === '1'" />
            </v-window-item>

            <v-window-item class="fill-height" value="2">
              <PlanStage v-if="currentStepIndex === '2'" />
            </v-window-item>

            <v-window-item class="fill-height" value="3">
              <ResultStage v-if="currentStepIndex === '3'" />
            </v-window-item>
          </v-window>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { useForecastStore } from '@/stores/forecast'

  import PlanStage from './forecast/PlanStage.vue'
  import ProgressView from './forecast/ProgressView.vue'
  import ResultStage from './forecast/ResultStage.vue'
  // Components
  import UploadStage from './forecast/UploadStage.vue'

  const store = useForecastStore()

  const steps = ['upload', 'plan', 'results'] as const

  const currentStepIndex = computed({
    get: () => {
      const idx = steps.indexOf(store.step as any)
      return (idx === -1 ? 1 : idx + 1).toString()
    },
    set: (val: string | number) => {
      const index = (typeof val === 'string' ? Number.parseInt(val) : val) - 1
      if (steps[index]) {
        const targetStep = steps[index]
        if (targetStep === 'plan' && !store.ontology) return
        if (targetStep === 'results' && store.forecastResults.length === 0) return

        store.setStep(targetStep)
      }
    },
  })
</script>

<style scoped>
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.4s ease;
  }

  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }

  .fade-enter-to,
  .fade-leave-from {
    opacity: 1;
  }
</style>
