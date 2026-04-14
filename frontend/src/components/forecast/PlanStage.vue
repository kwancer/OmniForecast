<template>
  <v-container class="fill-height d-flex flex-column pa-0" fluid>
    <!-- ═══════════════ TOP BAR (mirrors CleaningStage) ═══════════════ -->
    <div class="d-flex align-center px-4 py-4 w-100 bg-surface border-b">
      <v-btn
        class="hover-lift"
        icon="mdi-arrow-left"
        size="small"
        variant="tonal"
        @click="store.setStep('upload')"
      />
      <div class="ml-4">
        <h2 class="text-h6 font-weight-bold font-header mb-0">Mission Plan</h2>
      </div>
      <v-spacer />

      <!-- Stat pills – mirrors CleaningStage's shape display -->
      <div class="hidden-sm-and-down d-flex align-center bg-surface-light px-4 py-2 rounded-lg border">
        <div class="text-center mx-2">
          <div class="text-caption text-medium-emphasis text-uppercase" style="font-size: 10px;">Columns</div>
          <div class="font-weight-bold font-mono">{{ totalColumns }}</div>
        </div>
        <v-divider class="mx-2" vertical />
        <div class="text-center mx-2">
          <div class="text-caption text-medium-emphasis text-uppercase" style="font-size: 10px;">Features</div>
          <div class="font-weight-bold font-mono text-secondary">{{ totalFeatures }}</div>
        </div>
        <v-divider class="mx-2" vertical />
        <div class="text-center mx-2">
          <div class="text-caption text-medium-emphasis text-uppercase" style="font-size: 10px;">Domain</div>
          <div class="font-weight-bold font-mono text-primary">{{ store.ontology?.meta.domain_inference || '—' }}</div>
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
        <v-icon end>mdi-rocket-launch</v-icon>
      </v-btn>
    </div>

    <!-- ═══════════════ MAIN TWO-PANEL BODY ═══════════════ -->
    <v-row class="flex-grow-1 ma-0 w-100 bg-background panel-row">

      <!-- ─────── LEFT PANEL: Column Ontology Pipeline ─────── -->
      <v-col class="panel-col overflow-y-auto border-r bg-surface" cols="12" md="4" style="border-right-width: 1px !important;">
        <div class="pa-4">
          <h3 class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center">
            <v-icon color="secondary" start>mdi-sitemap-outline</v-icon>
            Column Ontology
          </h3>
          <div class="text-caption text-medium-emphasis mb-5">
            How each column in your dataset has been classified. Click to reassign.
          </div>

          <!-- TIMELINE of columns -->
          <v-timeline
            align="start"
            density="compact"
            side="end"
            truncate-line="both"
          >
            <!-- Time Index Column -->
            <v-timeline-item
              v-if="timeColumn"
              dot-color="secondary"
              fill-dot
              size="x-small"
            >
              <template #icon>
                <v-icon color="white" size="10">mdi-clock</v-icon>
              </template>
              <div
                class="column-card pa-3 rounded-lg mb-1 hover-lift"
                :class="{ 'column-card--active': editingColumn === timeColumn.column_name }"
                @click="toggleColumnEdit(timeColumn.column_name)"
              >
                <div class="d-flex align-center justify-space-between mb-1">
                  <span class="font-weight-bold text-subtitle-2">{{ timeColumn.display_name || timeColumn.column_name }}</span>
                  <v-chip color="secondary" size="x-small" variant="flat">TIMELINE</v-chip>
                </div>
                <div class="text-caption text-medium-emphasis">
                  {{ timeColumn.data_type }} · {{ timeColumn.date_format || 'auto-detected' }}
                </div>

                <!-- Inline editor -->
                <v-expand-transition>
                  <div v-if="editingColumn === timeColumn.column_name" class="mt-3" @click.stop>
                    <v-select
                      v-model="sentenceState!.time_col"
                      class="text-caption"
                      density="compact"
                      hide-details
                      :items="allColumns"
                      label="Time column"
                      variant="outlined"
                    />
                  </div>
                </v-expand-transition>
              </div>
            </v-timeline-item>

            <!-- Target Column -->
            <v-timeline-item
              v-if="targetColumn"
              dot-color="primary"
              fill-dot
              size="x-small"
            >
              <template #icon>
                <v-icon color="white" size="10">mdi-target</v-icon>
              </template>
              <div
                class="column-card column-card--target pa-3 rounded-lg mb-1 hover-lift"
                :class="{ 'column-card--active': editingColumn === targetColumn.column_name }"
                @click="toggleColumnEdit(targetColumn.column_name)"
              >
                <div class="d-flex align-center justify-space-between mb-1">
                  <span class="font-weight-bold text-subtitle-2 text-primary">{{ targetColumn.display_name || targetColumn.column_name }}</span>
                  <v-chip color="primary" size="x-small" variant="flat">TARGET</v-chip>
                </div>
                <div class="text-caption text-medium-emphasis">
                  {{ targetColumn.data_type }} · {{ targetColumn.constraints?.min_value !== null && targetColumn.constraints?.min_value !== undefined ? 'positive only' : '± values' }}
                </div>
                <v-expand-transition>
                  <div v-if="editingColumn === targetColumn.column_name" class="mt-3" @click.stop>
                    <v-select
                      v-model="sentenceState!.target_col"
                      class="text-caption"
                      density="compact"
                      hide-details
                      :items="allColumns"
                      label="Target column"
                      variant="outlined"
                    />
                  </div>
                </v-expand-transition>
              </div>
            </v-timeline-item>

            <!-- Group ID Column (if present) -->
            <v-timeline-item
              v-for="grp in groupColumns"
              :key="grp.column_name"
              dot-color="warning"
              fill-dot
              size="x-small"
            >
              <template #icon>
                <v-icon color="white" size="10">mdi-group</v-icon>
              </template>
              <div class="column-card pa-3 rounded-lg mb-1 hover-lift">
                <div class="d-flex align-center justify-space-between mb-1">
                  <span class="font-weight-bold text-subtitle-2">{{ grp.display_name || grp.column_name }}</span>
                  <v-chip color="warning" size="x-small" variant="flat">GROUP</v-chip>
                </div>
                <div class="text-caption text-medium-emphasis">
                  {{ grp.data_type }} · series identifier
                </div>
              </div>
            </v-timeline-item>

            <!-- Feature / Covariate Columns -->
            <v-timeline-item
              v-for="feat in featureColumns"
              :key="feat.column_name"
              :dot-color="getCovariateColor(feat.covariate_type)"
              fill-dot
              size="x-small"
            >
              <template #icon>
                <v-icon color="white" size="10">{{ getCovariateIcon(feat.covariate_type) }}</v-icon>
              </template>
              <div
                class="column-card pa-3 rounded-lg mb-1 hover-lift"
                :class="{
                  'column-card--ignored': isColumnIgnored(feat.column_name),
                  'column-card--active': editingColumn === feat.column_name,
                }"
                @click="toggleColumnEdit(feat.column_name)"
              >
                <div class="d-flex align-center justify-space-between mb-1">
                  <span class="font-weight-bold text-subtitle-2" :class="{ 'text-disabled text-decoration-line-through': isColumnIgnored(feat.column_name) }">
                    {{ feat.display_name || feat.column_name }}
                  </span>
                  <v-chip
                    :color="getCovariateColor(feat.covariate_type)"
                    size="x-small"
                    :variant="isColumnIgnored(feat.column_name) ? 'outlined' : 'flat'"
                  >
                    {{ formatCovariateType(feat.covariate_type) }}
                  </v-chip>
                </div>
                <div class="text-caption text-medium-emphasis" :class="{ 'text-disabled': isColumnIgnored(feat.column_name) }">
                  {{ feat.data_type }}{{ feat.future_availability ? ' · future: ' + feat.future_availability.status : '' }}
                </div>

                <!-- Inline override controls -->
                <v-expand-transition>
                  <div v-if="editingColumn === feat.column_name && !isColumnIgnored(feat.column_name)" class="mt-3" @click.stop>
                    <CovariateSentence
                      v-if="covariateStates[feat.column_name]"
                      v-model="covariateStates[feat.column_name]!"
                      :column="feat.column_name"
                      :type="feat.covariate_type || 'exogenous'"
                    />
                  </div>
                </v-expand-transition>
              </div>
            </v-timeline-item>

            <!-- Ignored Columns -->
            <v-timeline-item
              v-for="ign in ignoredColumns"
              :key="ign.column_name"
              dot-color="grey"
              size="x-small"
            >
              <div class="column-card column-card--ignored pa-3 rounded-lg mb-1">
                <div class="d-flex align-center justify-space-between mb-1">
                  <span class="text-subtitle-2 text-disabled text-decoration-line-through">{{ ign.display_name || ign.column_name }}</span>
                  <v-chip color="grey" size="x-small" variant="outlined">IGNORED</v-chip>
                </div>
                <div class="text-caption text-disabled">
                  {{ ign.data_type }} · excluded from model
                </div>
              </div>
            </v-timeline-item>
          </v-timeline>
        </div>
      </v-col>

      <!-- ─────── RIGHT PANEL: Intent + Scenarios + Table + DataXRay ─────── -->
      <v-col class="panel-col overflow-y-auto d-flex flex-column" cols="12" md="8">
        <div class="pa-4 pa-md-6 d-flex flex-column">

          <!-- SECTION 1: Forecast Intent (Natural Language) -->
          <div class="mb-6">
            <div class="d-flex align-center mb-4">
              <div>
                <h3 class="text-subtitle-1 font-weight-bold d-flex align-center ma-0">
                  <v-icon color="primary" start>mdi-target-account</v-icon>
                  Forecast Intent
                </h3>
                <div class="text-caption text-medium-emphasis mt-1">
                  This is what we understood from your prompt. Click edit to adjust.
                </div>
              </div>
              <v-spacer />
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
            />
          </div>

          <v-divider class="mb-6" />

          <!-- SECTION 2: Scenario Overrides -->
          <div v-if="controllableCovariates.length > 0 || exogenousCovariates.length > 0" class="mb-6">
            <h3 class="text-subtitle-1 font-weight-bold mb-4 d-flex align-center">
              <v-icon color="secondary" start>mdi-tune-variant</v-icon>
              Scenario Configuration
            </h3>
            <div class="text-caption text-medium-emphasis mb-4">
              Define how external and controllable factors behave in the forecast window. You can also configure these from the column timeline on the left.
            </div>

            <!-- Controllable Covariates -->
            <div v-if="controllableCovariates.length > 0" class="mb-5">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2" color="success" size="18">mdi-account-cog-outline</v-icon>
                <span class="text-body-2 font-weight-bold">My Decisions</span>
                <v-chip class="ml-2" color="success" size="x-small" variant="tonal">{{ controllableCovariates.length }}</v-chip>
              </div>
              <div v-for="col in controllableCovariates" :key="col.column_name" class="mb-2">
                <CovariateSentence
                  v-if="covariateStates[col.column_name]"
                  v-model="covariateStates[col.column_name]!"
                  :column="col.column_name"
                  :type="'controllable'"
                />
              </div>
            </div>

            <!-- Exogenous Covariates -->
            <div v-if="exogenousCovariates.length > 0" class="mb-5">
              <div class="d-flex align-center mb-3">
                <v-icon class="mr-2" color="info" size="18">mdi-weather-partly-cloudy</v-icon>
                <span class="text-body-2 font-weight-bold">External Assumptions</span>
                <v-chip class="ml-2" color="info" size="x-small" variant="tonal">{{ exogenousCovariates.length }}</v-chip>
              </div>
              <div v-for="col in exogenousCovariates" :key="col.column_name" class="mb-2">
                <CovariateSentence
                  v-if="covariateStates[col.column_name]"
                  v-model="covariateStates[col.column_name]!"
                  :column="col.column_name"
                  :type="'exogenous'"
                />
              </div>
            </div>
          </div>

          <!-- SECTION 3: Static Attributes -->
          <div v-if="staticCovariates.length > 0" class="mb-6">
            <v-divider class="mb-6" />
            <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
              <v-icon color="medium-emphasis" start>mdi-tag-multiple-outline</v-icon>
              Static Attributes
            </h3>
            <div class="text-caption text-medium-emphasis mb-3">
              Time-invariant descriptors that characterize the data but do not change during the forecast window.
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

          <v-divider class="mb-6" />

          <!-- SECTION 4: Dataset Snapshot (reactive to ontology) -->
          <div class="mb-6">
            <div class="d-flex align-center mb-4">
              <div>
                <h3 class="text-subtitle-1 font-weight-bold d-flex align-center ma-0">
                  <v-icon color="primary" start>mdi-table-large</v-icon>
                  Dataset Snapshot
                </h3>
                <div class="text-caption text-medium-emphasis mt-1">
                  Preview based on the current ontology configuration. First {{ sampleRows.length }} rows.
                </div>
              </div>
              <v-spacer />
              <v-chip v-if="activeColumnNames.length > 0" size="small" variant="tonal">
                {{ activeColumnNames.length }} active columns
              </v-chip>
            </div>

            <v-card class="d-flex flex-column text-body-2 border layout-card bg-surface" style="border-radius: 8px; overflow-x: auto;" variant="flat">
              <v-table v-if="sampleRows.length > 0 && activeColumnNames.length > 0" density="comfortable" hover style="background: transparent;">
                <thead class="bg-surface-light">
                  <tr>
                    <th
                      v-for="col in activeColumnNames"
                      :key="col"
                      class="font-weight-bold font-mono"
                      :class="getColumnHeaderClass(col)"
                      style="white-space: nowrap; background: var(--v-theme-surface-light) !important;"
                    >
                      <v-icon v-if="getColumnRole(col) === 'target'" class="mr-1" color="primary" size="small">mdi-target</v-icon>
                      <v-icon v-else-if="getColumnRole(col) === 'time_index'" class="mr-1" color="secondary" size="small">mdi-clock-outline</v-icon>
                      <v-icon v-else-if="isColumnIgnored(col)" class="mr-1" size="small">mdi-eye-off</v-icon>
                      {{ getColumnDisplayName(col) }}
                      <v-chip v-if="getColumnRole(col) === 'target'" class="ml-2 font-weight-bold" color="primary" size="x-small">TARGET</v-chip>
                      <v-chip v-else-if="getColumnRole(col) === 'time_index'" class="ml-2 font-weight-bold" color="secondary" size="x-small">TIME</v-chip>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in sampleRows" :key="idx">
                    <td
                      v-for="col in activeColumnNames"
                      :key="col"
                      :class="getColumnCellClass(col)"
                      style="white-space: nowrap;"
                    >
                      {{ formatVal(row[col]) }}
                    </td>
                  </tr>
                </tbody>
              </v-table>
              <div v-else class="ma-auto text-center text-medium-emphasis pa-8">
                <v-icon class="mb-4" size="32">mdi-file-delimited-outline</v-icon>
                <div>No sample data available.</div>
                <div class="text-caption mt-2">The data preview will appear once the backend provides sample rows.</div>
              </div>
            </v-card>
          </div>

          <v-divider class="mb-6" />

          <!-- SECTION 5: Advanced Data Inspection (expandable, metadata only) -->
          <div class="mb-4">
            <DataXRay v-if="store.ontology" :ontology="store.ontology" />
          </div>

        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import type { CovariateType } from '@/types'
  import { computed, onMounted, ref, watch } from 'vue'
  import { useForecastStore } from '@/stores/forecast'
  import CovariateSentence, { type CovariateState } from './CovariateSentence.vue'
  import DataXRay from './DataXRay.vue'
  import OntologySentence, { type SentenceState } from './OntologySentence.vue'

  const store = useForecastStore()

  const allColumns = computed(() => store.ontology?.columns.map(c => c.column_name) || [])
  const sentenceState = ref<SentenceState | null>(null)
  const covariateStates = ref<Record<string, CovariateState>>({})
  const editingColumn = ref<string | null>(null)

  // ─── Column Categorisation ───
  const timeColumn = computed(() => store.ontology?.columns.find(c => c.role === 'time_index') || null)
  const targetColumn = computed(() => store.ontology?.columns.find(c => c.role === 'target') || null)
  const groupColumns = computed(() => store.ontology?.columns.filter(c => c.role === 'group_id') || [])

  const featureColumns = computed(() => {
    if (!store.ontology || !sentenceState.value) return []
    return store.ontology.columns.filter(c =>
      c.role === 'covariate'
      && c.column_name !== sentenceState.value?.target_col
      && c.column_name !== sentenceState.value?.time_col,
    )
  })

  const ignoredColumns = computed(() => store.ontology?.columns.filter(c => c.role === 'ignore') || [])

  const covariates = computed(() => {
    if (!store.ontology || !sentenceState.value) return []
    return store.ontology.columns
      .filter(c => c.role !== 'group_id' && c.column_name !== sentenceState.value?.target_col && c.column_name !== sentenceState.value?.time_col)
  })

  const controllableCovariates = computed(() => {
    return covariates.value.filter(c => c.role === 'covariate' && c.covariate_type === 'controllable')
  })

  const exogenousCovariates = computed(() => {
    return covariates.value.filter(c => c.role === 'covariate' && c.covariate_type === 'exogenous')
  })

  const staticCovariates = computed(() => {
    return covariates.value.filter(c => c.role === 'covariate' && c.covariate_type === 'static')
  })

  // ─── Stats for header ───
  const totalColumns = computed(() => store.ontology?.columns.length || 0)
  const totalFeatures = computed(() => featureColumns.value.length + staticCovariates.value.length)

  // ─── Reactive Data Snapshot ───
  const sampleRows = computed(() => store.ontology?.sample_data || [])

  // Active columns: columns that aren't ignored (reactive to ontology + covariateStates)
  const activeColumnNames = computed(() => {
    if (!store.ontology) return []
    return store.ontology.columns
      .filter(c => c.role !== 'ignore' && !covariateStates.value[c.column_name]?.isIgnored)
      .map(c => c.column_name)
  })

  function getColumnRole (colName: string): string {
    if (!store.ontology) return ''
    // Account for sentence state overrides (user may have changed target/time via the intent editor)
    if (sentenceState.value?.target_col === colName) return 'target'
    if (sentenceState.value?.time_col === colName) return 'time_index'
    const col = store.ontology.columns.find(c => c.column_name === colName)
    return col?.role || ''
  }

  function getColumnDisplayName (colName: string): string {
    if (!store.ontology) return colName
    const col = store.ontology.columns.find(c => c.column_name === colName)
    return col?.display_name || col?.column_name || colName
  }

  function getColumnHeaderClass (colName: string): string {
    const role = getColumnRole(colName)
    if (role === 'target') return 'text-primary'
    if (role === 'time_index') return 'text-secondary'
    if (isColumnIgnored(colName)) return 'opacity-40 text-decoration-line-through'
    return 'text-medium-emphasis'
  }

  function getColumnCellClass (colName: string): string {
    const role = getColumnRole(colName)
    if (role === 'target') return 'font-weight-medium text-primary bg-primary-lighten-5'
    if (role === 'time_index') return 'text-secondary'
    if (isColumnIgnored(colName)) return 'opacity-40 text-decoration-line-through text-disabled'
    return 'text-medium-emphasis'
  }

  function formatVal (val: any) {
    if (val === null || val === undefined) return '-'
    if (typeof val === 'number') return Number.isInteger(val) ? val : val.toFixed(2)
    if (typeof val === 'string' && val.length > 20) return val.slice(0, 17) + '...'
    return val
  }

  // ─── Helpers ───
  function isColumnIgnored (colName: string): boolean {
    return covariateStates.value[colName]?.isIgnored === true
  }

  function toggleColumnEdit (colName: string) {
    editingColumn.value = editingColumn.value === colName ? null : colName
  }

  function getCovariateColor (type?: CovariateType): string {
    switch (type) {
      case 'controllable': { return 'success'
      }
      case 'exogenous': { return 'info'
      }
      case 'static': { return 'grey'
      }
      default: { return 'grey'
      }
    }
  }

  function getCovariateIcon (type?: CovariateType): string {
    switch (type) {
      case 'controllable': { return 'mdi-cog'
      }
      case 'exogenous': { return 'mdi-cloud'
      }
      case 'static': { return 'mdi-tag'
      }
      default: { return 'mdi-circle'
      }
    }
  }

  function formatCovariateType (type?: CovariateType): string {
    switch (type) {
      case 'controllable': { return 'CONTROLLABLE'
      }
      case 'exogenous': { return 'EXOGENOUS'
      }
      case 'static': { return 'STATIC'
      }
      default: { return 'FEATURE'
      }
    }
  }

  // Initialize covariate states when covariates change
  watch(covariates, newCovs => {
    for (const col of newCovs) {
      if (!covariateStates.value[col.column_name]) {
        covariateStates.value[col.column_name] = { override: null, isIgnored: false }
      }
    }
    // Clean up old
    const newNames = new Set(newCovs.map(c => c.column_name))
    for (const key in covariateStates.value) {
      if (!newNames.has(key)) delete covariateStates.value[key]
    }
  }, { immediate: true })

  onMounted(() => {
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

<style scoped>
/* ─── Mobile responsive panels ─── */
.panel-row {
  overflow: hidden;
}

/* On desktop: panels fill height and scroll independently */
@media (min-width: 960px) {
  .panel-row {
    height: 0;
    flex: 1 1 auto;
  }
  .panel-col {
    height: 100%;
  }
}

/* On mobile: panels stack, each scrolls naturally */
@media (max-width: 959px) {
  .panel-row {
    overflow-y: auto;
    flex: 1 1 auto;
  }
  .panel-col {
    height: auto !important;
    max-height: none !important;
    overflow-y: visible !important;
  }
}

.column-card {
  background: rgba(var(--v-theme-surface-light), 0.6);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.column-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background: rgba(var(--v-theme-primary), 0.04);
}

.column-card--active {
  border-color: rgba(var(--v-theme-primary), 0.5) !important;
  background: rgba(var(--v-theme-primary), 0.06) !important;
  box-shadow: 0 0 0 1px rgba(var(--v-theme-primary), 0.15);
}

.column-card--target {
  border-left: 3px solid rgb(var(--v-theme-primary)) !important;
}

.column-card--ignored {
  opacity: 0.5;
  cursor: default;
}

/* Timeline: force items to take full available width */
:deep(.v-timeline-item__body) {
  padding-inline-start: 12px !important;
  width: 100%;
  min-width: 0;
}

:deep(.v-timeline--vertical .v-timeline-item .v-timeline-item__body) {
  padding-block-start: 0;
  padding-block-end: 4px;
}

:deep(.v-timeline--vertical.v-timeline--side-end .v-timeline-item) {
  grid-template-columns: 0 min-content 1fr;
}

/* Table chrome */
.layout-card {
  box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02) !important;
}

:deep(thead tr th) {
  border-bottom: 2px solid var(--v-border-color) !important;
}
</style>
