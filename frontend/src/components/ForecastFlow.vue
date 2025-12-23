<template>
  <v-container class="fill-height pa-0" fluid>
    <v-row justify="center" class="fill-height ma-0">
      <v-col cols="12" class="fill-height pa-0">
        <v-stepper
          v-model="currentStepIndex"
          class="fill-height d-flex flex-column"
          flat
          :mobile="mobile"
        >
          <v-stepper-header>
            <v-stepper-item
              title="Data Upload"
              value="1"
              :complete="Number(currentStepIndex) > 1"
            ></v-stepper-item>

            <v-divider></v-divider>

            <v-stepper-item
              title="Mission Plan"
              value="2"
              :complete="Number(currentStepIndex) > 2"
              :editable="!!store.ontology"
              :rules="[() => !!store.ontology]"
            ></v-stepper-item>

            <v-divider></v-divider>

            <v-stepper-item
              title="Data Cleaning"
              value="3"
              :complete="Number(currentStepIndex) > 3"
              :editable="!!store.cleaningReport"
              :rules="[() => !!store.cleaningReport]"
            ></v-stepper-item>

            <v-divider></v-divider>

            <v-stepper-item
              title="Analytic Output"
              value="4"
              :complete="Number(currentStepIndex) > 4"
              :editable="store.forecastResults.length > 0"
              :rules="[() => store.forecastResults.length > 0]"
            ></v-stepper-item>
          </v-stepper-header>

          <v-stepper-window class="flex-grow-1 overflow-y-auto" style="height: 100%">
            <v-stepper-window-item value="1" class="fill-height">
              <UploadStage />
            </v-stepper-window-item>

            <v-stepper-window-item value="2" class="fill-height">
              <PlanStage />
            </v-stepper-window-item>

            <v-stepper-window-item value="3" class="fill-height">
              <CleaningStage />
            </v-stepper-window-item>

            <v-stepper-window-item value="4" class="fill-height">
              <ResultStage />
            </v-stepper-window-item>
          </v-stepper-window>
        </v-stepper>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useForecastStore } from '@/stores/forecast'
import { useDisplay } from 'vuetify'

// Components (explicitly importing to be safe, though auto-import might work)
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
      // Logic to prevent jumping ahead if not allowed is handled by :editable / :rules in template
      // But we can double check here
      const targetStep = steps[index]
      if (targetStep === 'plan' && !store.ontology) return
      if (targetStep === 'cleaning' && !store.cleaningReport) return
      if (targetStep === 'results' && store.forecastResults.length === 0) return

      store.setStep(targetStep)
    }
  }
})
</script>
