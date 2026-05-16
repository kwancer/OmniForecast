<template>
  <v-container class="fill-height d-flex flex-column pa-0" fluid>
    <!-- ═══════════════ TOP BAR ═══════════════ -->
    <div class="d-flex align-center px-4 py-4 w-100 bg-surface border-b">
      <v-btn
        class="hover-lift"
        icon="mdi-arrow-left"
        size="small"
        variant="tonal"
        @click="store.setStep('upload')"
      />
      <div class="ml-4">
        <h2 class="text-h6 font-weight-bold font-header mb-0">Review</h2>
      </div>
      <v-spacer />

      <!-- Stat pills -->
      <div class="hidden-sm-and-down d-flex align-center stat-pills">
        <div class="stat-pill">
          <div class="stat-pill__label">Columns</div>
          <div class="stat-pill__value">{{ totalColumns }}</div>
        </div>
        <v-divider class="mx-2" vertical />
        <div class="stat-pill">
          <div class="stat-pill__label">Features</div>
          <div class="stat-pill__value text-secondary">{{ totalFeatures }}</div>
        </div>
        <v-divider class="mx-2" vertical />
        <div class="stat-pill">
          <div class="stat-pill__label">Domain</div>
          <div class="stat-pill__value text-primary">{{ store.ontology?.meta.domain_inference || '—' }}</div>
        </div>
      </div>

      <v-btn
        class="ml-6 hover-lift font-weight-bold"
        color="primary"
        elevation="0"
        :loading="store.loading"
        variant="flat"
        @click="confirmAndProceed"
      >
        Execute Run
        <v-icon end>mdi-chevron-right</v-icon>
      </v-btn>
    </div>

    <!-- ═══════════════ MAIN SINGLE-COLUMN BODY ═══════════════ -->
    <div class="flex-grow-1 overflow-y-auto w-100 bg-background">
      <div class="pa-4 pa-md-6 mx-auto" style="max-width: 1400px;">

        <!-- SECTION 1: Forecast Intent -->
        <div class="section-card mb-6">
          <div class="d-flex align-center mb-4">
            <div class="section-header">
              <div class="section-header__icon section-header__icon--primary">
                <v-icon color="white" size="18">mdi-target-account</v-icon>
              </div>
              <div>
                <h3 class="text-subtitle-1 font-weight-bold ma-0">Forecast Intent</h3>
                <div class="text-caption text-medium-emphasis mt-1">
                  This is what we understood from your prompt. Click edit to adjust.
                </div>
              </div>
            </div>
            <v-spacer />
            <v-chip
              v-if="store.ontology?.aggregate_series"
              class="mr-2"
              color="info"
              size="small"
              variant="tonal"
            >
              <v-icon size="14" start>mdi-set-all</v-icon>
              Aggregate Group
            </v-chip>
            <v-chip
              v-else-if="store.ontology?.target_series_id"
              class="mr-2"
              color="info"
              size="small"
              variant="tonal"
            >
              <v-icon size="14" start>mdi-filter-variant</v-icon>
              ID: {{ store.ontology.target_series_id }}
            </v-chip>
            <v-chip
              v-if="store.ontology?.meta.completeness_check"
              :color="store.ontology.meta.completeness_check === 'complete' ? 'success' : 'warning'"
              size="small"
              variant="tonal"
            >
              <v-icon size="14" start>{{ store.ontology.meta.completeness_check === 'complete' ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
              {{ store.ontology.meta.completeness_check === 'complete' ? 'Fully Mapped' : 'Partial Mapping' }}
            </v-chip>
          </div>

          <OntologySentence
            v-if="sentenceState"
            v-model="sentenceState"
            :all-columns="allColumns"
            :external-covariates="externalCovariateNames"
            :horizon-confidence-rationale="store.ontology?.requirements.horizon_requirement.confidence_rationale"
            :horizon-confidence-score="store.ontology?.requirements.horizon_requirement.confidence_score"
            :planned-covariates="plannedCovariateNames"
            :static-covariates="staticCovariateNames"
          />
        </div>

        <!-- SECTION 2: Static Attributes -->
        <div v-if="staticCovariates.length > 0" class="section-card mb-6">
          <div class="section-header mb-4">
            <div class="section-header__icon" style="background: rgba(var(--v-theme-on-surface), 0.12);">
              <v-icon size="18">mdi-tag-multiple-outline</v-icon>
            </div>
            <div>
              <h3 class="text-subtitle-1 font-weight-bold mb-0">Static Attributes</h3>
              <div class="text-caption text-medium-emphasis mt-1">
                Time-invariant descriptors that do not change during the forecast window.
              </div>
            </div>
          </div>
          <div class="d-flex flex-wrap" style="gap: 8px;">
            <v-chip
              v-for="col in staticCovariates"
              :key="col.column_name"
              class="hover-lift"
              color="grey"
              size="small"
              variant="tonal"
            >
              <v-icon size="14" start>mdi-tag-outline</v-icon>
              {{ col.display_name || col.column_name }}
            </v-chip>
          </div>
        </div>

        <!-- SECTION 3: Unified Data Table -->
        <div class="section-card mb-6">
          <div class="d-flex align-center mb-4">
            <div class="section-header">
              <div class="section-header__icon section-header__icon--primary">
                <v-icon color="white" size="18">mdi-table-large</v-icon>
              </div>
              <div>
                <h3 class="text-subtitle-1 font-weight-bold ma-0">
                  {{ covariates.length > 0 ? 'Data & Assumptions' : 'Dataset Preview' }}
                </h3>
                <div class="text-caption text-medium-emphasis mt-1">
                  {{ covariates.length > 0
                    ? 'Review historical data, column roles, and your future assumptions.'
                    : 'Historical data that will be used to generate the forecast.'
                  }}
                </div>
              </div>
            </div>
            <v-spacer />
            <v-chip size="small" variant="tonal">
              {{ activeColumnCount }} active / {{ totalColumns }} total
            </v-chip>
          </div>

          <UnifiedDataTable
            v-if="store.ontology && sentenceState"
            :covariate-states="covariateStates"
            :ontology="store.ontology"
            :sentence-state="sentenceState"
            @change-type="changeCovariateType"
            @toggle-ignore="toggleColumnIgnore"
            @update-override="handleUpdateOverride"
          />
        </div>

      </div>
    </div>

    <ClarificationDialog
      v-model="showClarification"
      @bypass="handleClarificationBypass"
    />
  </v-container>
</template>

<script setup lang="ts">
  import type { CovariateState } from './CovariateSentence.vue'
  import type { CovariateType } from '@/types'
  import { computed, onMounted, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import ClarificationDialog from './ClarificationDialog.vue'
  import OntologySentence, { type SentenceState } from './OntologySentence.vue'
  import UnifiedDataTable from './UnifiedDataTable.vue'

  const store = useForecastStore()

  const allColumns = computed(() => store.ontology?.columns.map(c => c.column_name) || [])
  const sentenceState = ref<SentenceState | null>(null)
  const covariateStates = ref<Record<string, CovariateState>>({})
  const clarificationInput = ref('')
  const showClarification = ref(false)
  const hasBypassedClarification = ref(false)

  // ─── Clarification Logic ───
  const lowConfidenceColumns = computed(() => {
    if (!store.ontology) return []
    return store.ontology.columns.filter(c => (c.confidence_score ?? 1) < 0.85)
  })

  const minColumnConfidence = computed(() => {
    if (!store.ontology?.columns.length) return 1
    return Math.min(...store.ontology.columns.map(c => c.confidence_score ?? 1))
  })

  const needsClarification = computed(() => {
    const globalScore = store.ontology?.meta.confidence_score ?? 1
    const horizonScore = store.ontology?.requirements.horizon_requirement.confidence_score ?? 1
    const hasQuestions = (store.ontology?.meta.clarification_questions?.length ?? 0) > 0
    return globalScore < 0.85 || minColumnConfidence.value < 0.85 || horizonScore < 0.85 || hasQuestions
  })

  // ─── Column Categorisation ───
  const covariates = computed(() => {
    if (!store.ontology || !sentenceState.value) return []
    return store.ontology.columns
      .filter(c => c.role !== 'group_id' && c.column_name !== sentenceState.value?.target_col && c.column_name !== sentenceState.value?.time_col)
  })

  const plannedCovariates = computed(() => {
    return covariates.value.filter(c => c.role === 'covariate' && c.covariate_type === 'known_future')
  })

  const externalCovariates = computed(() => {
    return covariates.value.filter(c => c.role === 'covariate' && c.covariate_type === 'unknown_past')
  })

  const staticCovariates = computed(() => {
    return covariates.value.filter(c => c.role === 'covariate' && c.covariate_type === 'static')
  })

  const plannedCovariateNames = computed(() =>
    plannedCovariates.value.map(c => c.display_name || c.column_name),
  )
  const externalCovariateNames = computed(() =>
    externalCovariates.value.map(c => c.display_name || c.column_name),
  )
  const staticCovariateNames = computed(() =>
    staticCovariates.value.map(c => c.display_name || c.column_name),
  )

  // ─── Stats for header ───
  const totalColumns = computed(() => store.ontology?.columns.length || 0)
  const totalFeatures = computed(() => covariates.value.filter(c => c.covariate_type !== 'static').length)
  const activeColumnCount = computed(() => {
    if (!store.ontology) return 0
    return store.ontology.columns.filter(c => c.role !== 'ignore' && !covariateStates.value[c.column_name]?.isIgnored).length
  })

  // ─── Helpers ───
  function isColumnIgnored (colName: string): boolean {
    return covariateStates.value[colName]?.isIgnored === true
  }

  function toggleColumnIgnore (colName: string, ignored: boolean) {
    if (!covariateStates.value[colName]) {
      covariateStates.value[colName] = { override: null, isIgnored: false }
    }
    covariateStates.value[colName].isIgnored = ignored
    if (!store.ontology) return
    const col = store.ontology.columns.find(c => c.column_name === colName)
    if (!col) return
    col.role = ignored ? 'ignore' : 'covariate'
  }

  function changeCovariateType (colName: string, newType: CovariateType) {
    if (!store.ontology) return
    const col = store.ontology.columns.find(c => c.column_name === colName)
    if (col) {
      col.covariate_type = newType
    }
  }

  function handleUpdateOverride (colName: string, values: number | number[] | 'seasonal' | null) {
    if (!covariateStates.value[colName]) {
      covariateStates.value[colName] = { override: null, isIgnored: false }
    }
    covariateStates.value[colName].override = values

    if (!store.ontology) return
    if (!store.ontology.scenario_overrides) store.ontology.scenario_overrides = []

    // Remove existing override for this column
    store.ontology.scenario_overrides = store.ontology.scenario_overrides.filter(o => o.column_name !== colName)

    // Add new override if not null
    if (values !== null) {
      store.ontology.scenario_overrides.push({ column_name: colName, values })
    }
  }

  // Initialize covariate states when covariates change
  watch(covariates, newCovs => {
    const overridesArr = store.ontology?.scenario_overrides || []
    const overrideLookup: Record<string, number | number[] | 'seasonal'> = {}
    for (const o of overridesArr) {
      overrideLookup[o.column_name] = o.values
    }

    for (const col of newCovs) {
      if (!covariateStates.value[col.column_name]) {
        const existing = overrideLookup[col.column_name]
        covariateStates.value[col.column_name] = {
          override: existing !== undefined ? existing : null,
          isIgnored: col.role === 'ignore',
        }
      }
    }
    // Clean up old
    const newNames = new Set(newCovs.map(c => c.column_name))
    for (const key in covariateStates.value) {
      if (!newNames.has(key)) delete covariateStates.value[key]
    }
  }, { immediate: true })

  function initSentenceState () {
    if (!store.ontology) return
    const targCol = store.ontology.columns.find(c => c.role === 'target')
    const timeCol = store.ontology.columns.find(c => c.role === 'time_index')
    const isPositive = targCol?.constraints?.min_value !== null && targCol?.constraints?.min_value !== undefined

    sentenceState.value = {
      target_col: targCol?.column_name || '',
      time_col: timeCol?.column_name || '',
      horizon: store.ontology.requirements.horizon_requirement.steps || 12,
      frequency: store.ontology.problem.granularity.unit || 'month',
      is_positive: isPositive,
      risk_preference: store.ontology.risk_preference || 'balanced',
    }
  }

  // Bidirectional sync: scenario_overrides → covariateStates
  watch(() => store.ontology?.scenario_overrides, overrides => {
    if (!overrides || !Array.isArray(overrides)) return
    for (const item of overrides) {
      const col = item.column_name
      const val = item.values
      if (!covariateStates.value[col]) {
        covariateStates.value[col] = { override: null, isIgnored: false }
      }
      const state = covariateStates.value[col]
      if (val === null) {
        state.override = null
        state.isIgnored = false
      } else if (val === 'seasonal') {
        state.override = 'seasonal'
        state.isIgnored = false
      } else if (typeof val === 'number') {
        state.override = val
        state.isIgnored = false
      } else if (Array.isArray(val)) {
        state.override = val
        state.isIgnored = false
      }
    }
  }, { deep: true })

  watch(() => store.ontology, () => {
    initSentenceState()
    if (needsClarification.value && !hasBypassedClarification.value) {
      showClarification.value = true
    } else if (!needsClarification.value) {
      showClarification.value = false
    }
  }, { immediate: true })

  onMounted(() => {
    initSentenceState()
  })

  function confirmAndProceed () {
    if (!sentenceState.value || !store.ontology) return

    for (const col of store.ontology.columns) {
      if ((col.role === 'target' || col.role === 'time_index')
        && col.column_name !== sentenceState.value.target_col && col.column_name !== sentenceState.value.time_col) {
        col.role = 'ignore'
      }

      if (col.column_name === sentenceState.value?.target_col) {
        col.role = 'target'
        if (!col.constraints) col.constraints = {}
        col.constraints.min_value = sentenceState.value?.is_positive ? 0 : null
      }
      if (col.column_name === sentenceState.value?.time_col) {
        col.role = 'time_index'
      }

      if (covariateStates.value[col.column_name]?.isIgnored) {
        col.role = 'ignore'
      } else if (col.role === 'ignore' && !covariateStates.value[col.column_name]?.isIgnored
        && col.column_name !== sentenceState.value.target_col && col.column_name !== sentenceState.value.time_col) {
        col.role = 'covariate'
      }
    }

    store.ontology.requirements.horizon_requirement.steps = sentenceState.value.horizon
    store.ontology.problem.granularity.unit = sentenceState.value.frequency as any
    store.ontology.risk_preference = sentenceState.value.risk_preference

    store.ontology.scenario_overrides = []
    for (const [col, state] of Object.entries(covariateStates.value)) {
      if (state.override !== null) {
        store.ontology.scenario_overrides.push({
          column_name: col,
          values: state.override as any,
        })
      }
    }

    store.executeForecast()
  }

  function handleClarificationBypass () {
    showClarification.value = false
    hasBypassedClarification.value = true
  }
</script>

<style scoped>
/* ─── Stat Pills ─── */
.stat-pills {
  background: rgba(var(--v-theme-primary), 0.04);
  border: 1px solid rgba(var(--v-theme-primary), 0.08);
  padding: 8px 16px;
  border-radius: 12px;
}

.stat-pill {
  text-align: center;
  padding: 0 8px;
}

.stat-pill__label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-weight: 500;
}

.stat-pill__value {
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.875rem;
}

/* ─── Section Cards ─── */
.section-card {
  background: rgba(var(--v-theme-primary), 0.02);
  border: 1px solid rgba(var(--v-theme-primary), 0.06);
  border-radius: 16px;
  padding: 20px 24px;
  transition: border-color 0.3s ease;
}

.section-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.12);
}

/* ─── Section Headers ─── */
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  flex-shrink: 0;
}

.section-header__icon--primary {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)), rgba(var(--v-theme-primary), 0.7));
}

.section-header__icon--secondary {
  background: linear-gradient(135deg, rgb(var(--v-theme-secondary)), rgba(var(--v-theme-secondary), 0.7));
}

.section-header__icon--warning {
  background: linear-gradient(135deg, #fb8c00, #ffb74d);
}
</style>
