<template>
  <v-container class="fill-height d-flex flex-column pa-2 pa-md-4">
    <div class="d-flex align-center mb-6">
      <v-btn icon="mdi-arrow-left" variant="text" @click="store.setStep('upload')" />
      <h2 class="text-h5 font-header ml-2">Mission Plan</h2>
    </div>

    <v-row class="ma-0 overflow-y-auto w-100">
      <v-col cols="12" md="10" offset-md="1">

        <div class="mb-2 text-caption text-medium-emphasis">INTENT DEFINITION</div>
        <OntologySentence
          v-if="sentenceState"
          v-model="sentenceState"
          :all-columns="allColumns"
          class="mb-8"
        />

        <div v-if="covariates.length > 0" class="mb-2 text-caption text-medium-emphasis">SCENARIO CONFIGURATION</div>
        <div v-for="col in covariates" :key="col" class="mb-2">
          <CovariateSentence
            v-if="covariateStates[col]"
            v-model="covariateStates[col]"
            :column="col"
          />
        </div>

        <DataXRay v-if="store.ontology" class="mb-4" :ontology="store.ontology" />

        <v-card class="d-flex justify-end align-center bg-transparent mt-4" variant="flat">
          <div class="text-caption text-medium-emphasis mr-4 text-right hidden-sm-and-down">
            The AI has mapped your data structure.<br>Click Execute to begin deterministic modelling.
          </div>
          <v-btn
            class="font-weight-bold"
            color="primary"
            elevation="2"
            size="x-large"
            width="200"
            @click="confirmAndProceed"
          >
            Execute
            <v-icon end>mdi-rocket-launch</v-icon>
          </v-btn>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, onMounted, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import CovariateSentence, { type CovariateState } from './CovariateSentence.vue'
  import DataXRay from './DataXRay.vue'
  import OntologySentence, { type SentenceState } from './OntologySentence.vue'

  const store = useForecastStore()

  const allColumns = computed(() => store.ontology?.columns.map(c => c.column_name) || [])
  const sentenceState = ref<SentenceState | null>(null)
  const covariateStates = ref<Record<string, CovariateState>>({})

  const covariates = computed(() => {
    if (!store.ontology || !sentenceState.value) return []
    return store.ontology.columns
      .map(c => c.column_name)
      .filter(c => c !== sentenceState.value?.target_col && c !== sentenceState.value?.time_col)
  })

  // Initialize covariate states when covariates change
  watch(covariates, newCovs => {
    for (const col of newCovs) {
      if (!covariateStates.value[col]) {
        covariateStates.value[col] = { override: null, isIgnored: false }
      }
    }
    // Clean up old
    for (const key in covariateStates.value) {
      if (!newCovs.includes(key)) delete covariateStates.value[key]
    }
  }, { immediate: true })

  onMounted(() => {
    if (!store.ontology) return
    const targetCol = store.ontology.columns.find(c => c.role === 'target')
    const timeCol = store.ontology.columns.find(c => c.role === 'time_index')
    const isPositive = targetCol?.constraints?.min_value !== null

    sentenceState.value = {
      target_col: targetCol?.column_name || '',
      time_col: timeCol?.column_name || '',
      horizon: store.ontology.requirements.horizon_requirement.steps || 12,
      frequency: store.ontology.problem.granularity.unit || 'month',
      is_positive: isPositive,
      risk_preference: store.ontology.risk_preference || 'balanced',
    }
  })

  function confirmAndProceed () {
    if (!sentenceState.value || !store.ontology) return

    // Logic to update ontology remains the same as previous step
    for (const col of store.ontology.columns) {
      if (col.role === 'target') col.role = 'ignore'
      if (col.role === 'time_index') col.role = 'ignore'

      if (col.column_name === sentenceState.value?.target_col) {
        col.role = 'target'
        if (!col.constraints) col.constraints = {}
        col.constraints.min_value = sentenceState.value?.is_positive ? 0 : null
      }
      if (col.column_name === sentenceState.value?.time_col) {
        col.role = 'time_index'
      }
    }

    store.ontology.requirements.horizon_requirement.steps = sentenceState.value.horizon
    store.ontology.problem.granularity.unit = sentenceState.value.frequency as any
    store.ontology.risk_preference = sentenceState.value.risk_preference

    // Scenario Overrides & Ignores
    const overrides: Record<string, number | number[] | null> = {}
    const ignores: string[] = []

    for (const [col, state] of Object.entries(covariateStates.value)) {
      if (state.isIgnored) {
        ignores.push(col)
      } else {
        overrides[col] = state.override
      }
    }

    store.ontology.scenario_overrides = overrides
    store.ontology.ignored_columns = ignores

    store.executeForecast()
  }
</script>
