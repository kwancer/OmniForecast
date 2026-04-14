<template>
  <v-container class="fill-height pa-0" fluid>
    <v-row class="fill-height ma-0" justify="center">
      <v-col class="fill-height pa-0" cols="12">
        <div class="fill-height d-flex flex-column">
          <!-- Custom Stepper Header for Mobile/Desktop Stability -->
          <div class="d-flex align-center flex-shrink-0 bg-surface border-b px-4 py-2 overflow-x-auto" style="min-height: 64px; gap: 8px">
            <template v-for="(step, i) in ['Data Upload', 'Mission Plan', 'Data Cleaning', 'Analytic Output']" :key="i">
              <div
                class="d-flex align-center cursor-pointer hover-lift rounded-pill px-2 py-1"
                :class="{
                  'text-primary font-weight-bold': Number(currentStepIndex) === i + 1,
                  'text-medium-emphasis': Number(currentStepIndex) !== i + 1,
                  'opacity-60': Number(currentStepIndex) < i + 1
                }"
                style="white-space: nowrap; transition: all 0.3s ease;"
              >
                <v-avatar
                  class="mr-2"
                  :color="Number(currentStepIndex) > i + 1 ? 'success' : (Number(currentStepIndex) === i + 1 ? 'primary' : 'grey')"
                  size="24"
                  :variant="Number(currentStepIndex) === i + 1 ? 'flat' : 'tonal'"
                >
                  <v-icon v-if="Number(currentStepIndex) > i + 1" size="16">mdi-check</v-icon>
                  <span v-else class="text-caption font-weight-bold">{{ i + 1 }}</span>
                </v-avatar>
                <span class="text-caption hidden-xs" :class="{'font-weight-bold': Number(currentStepIndex) === i + 1, 'font-weight-medium': Number(currentStepIndex) !== i + 1}">{{ step }}</span>
                <span v-if="Number(currentStepIndex) === i + 1" class="text-caption font-weight-bold d-sm-none">{{ step }}</span>
              </div>
              <v-divider v-if="i < 3" class="mx-2" style="height: 24px; opacity: 0.3;" vertical />
            </template>
          </div>

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
              <CleaningStage v-if="currentStepIndex === '3'" />
            </v-window-item>

            <v-window-item class="fill-height" value="4">
              <ResultStage v-if="currentStepIndex === '4'" />
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

  import CleaningStage from './forecast/CleaningStage.vue'
  import PlanStage from './forecast/PlanStage.vue'
  import ProgressView from './forecast/ProgressView.vue'
  import ResultStage from './forecast/ResultStage.vue'
  // Components
  import UploadStage from './forecast/UploadStage.vue'

  const store = useForecastStore()

  const steps = ['upload', 'plan', 'cleaning', 'results'] as const

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
        if (targetStep === 'cleaning' && !store.cleaningReport) return
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
