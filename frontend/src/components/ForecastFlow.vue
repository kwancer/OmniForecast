<template>
  <v-container class="fill-height pa-0" fluid>
    <v-row justify="center" class="fill-height ma-0">
      <v-col cols="12" class="fill-height pa-0">
        <div class="fill-height d-flex flex-column">
          <!-- Custom Stepper Header for Mobile/Desktop Stability -->
          <div class="d-flex align-center flex-shrink-0 bg-surface border-b px-4 py-2 overflow-x-auto" style="min-height: 64px; gap: 8px">
            <template v-for="(step, i) in ['Data Upload', 'Mission Plan', 'Data Cleaning', 'Analytic Output']" :key="i">
              <div
                class="d-flex align-center cursor-pointer"
                :class="{'text-primary': Number(currentStepIndex) >= i + 1, 'text-medium-emphasis': Number(currentStepIndex) < i + 1}"
                style="white-space: nowrap;"
              >
                <v-avatar
                  size="24"
                  :color="Number(currentStepIndex) > i + 1 ? 'success' : (Number(currentStepIndex) === i + 1 ? 'primary' : 'grey')"
                  variant="tonal"
                  class="mr-2"
                >
                  <v-icon size="16" v-if="Number(currentStepIndex) > i + 1">mdi-check</v-icon>
                  <span class="text-caption font-weight-bold" v-else>{{ i + 1 }}</span>
                </v-avatar>
                <span class="text-caption font-weight-medium hidden-xs">{{ step }}</span>
                <span class="text-caption font-weight-medium d-sm-none" v-if="Number(currentStepIndex) === i + 1">{{ step }}</span>
              </div>
              <v-divider vertical class="mx-2" v-if="i < 3" style="height: 24px"></v-divider>
            </template>
          </div>

          <v-window v-model="currentStepIndex" class="flex-grow-1" style="height: 100%" :touch="false">
            <v-window-item value="1" class="fill-height">
              <UploadStage v-if="currentStepIndex === '1'" />
            </v-window-item>

            <v-window-item value="2" class="fill-height">
              <PlanStage v-if="currentStepIndex === '2'" />
            </v-window-item>

            <v-window-item value="3" class="fill-height">
              <CleaningStage v-if="currentStepIndex === '3'" />
            </v-window-item>

            <v-window-item value="4" class="fill-height">
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
import { useDisplay } from 'vuetify'

// Components
import UploadStage from './forecast/UploadStage.vue'
import PlanStage from './forecast/PlanStage.vue'
import CleaningStage from './forecast/CleaningStage.vue'
import ResultStage from './forecast/ResultStage.vue'

const store = useForecastStore()
const { mobile } = useDisplay()

const steps = ['upload', 'plan', 'cleaning', 'results'] as const

const currentStepIndex = computed({
  get: () => {
    const idx = steps.indexOf(store.step as any)
    return (idx !== -1 ? idx + 1 : 1).toString()
  },
  set: (val: string | number) => {
    const index = (typeof val === 'string' ? parseInt(val) : val) - 1
    if (steps[index]) {
      const targetStep = steps[index]
      if (targetStep === 'plan' && !store.ontology) return
      if (targetStep === 'cleaning' && !store.cleaningReport) return
      if (targetStep === 'results' && store.forecastResults.length === 0) return

      store.setStep(targetStep)
    }
  }
})
</script>
