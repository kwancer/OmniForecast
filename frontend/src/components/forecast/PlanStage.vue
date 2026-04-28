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
        <h2 class="text-h6 font-weight-bold font-header mb-0">Mission Plan</h2>
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
        <v-icon end>mdi-rocket-launch</v-icon>
      </v-btn>
    </div>

    <!-- ═══════════════ MAIN TWO-PANEL BODY ═══════════════ -->
    <v-row class="flex-grow-1 ma-0 w-100 bg-background panel-row">

      <!-- ─────── LEFT PANEL: Column Ontology Pipeline ─────── -->
      <v-col class="panel-col overflow-y-auto border-r bg-surface" cols="12" md="4" style="border-right-width: 1px !important;">
        <div class="pa-4">
          <div class="section-header mb-4">
            <div class="section-header__icon section-header__icon--secondary">
              <v-icon color="white" size="18">mdi-sitemap-outline</v-icon>
            </div>
            <div>
              <h3 class="text-subtitle-1 font-weight-bold mb-0">Column Ontology</h3>
              <div class="text-caption text-medium-emphasis">
                How each column has been classified. Click to reassign.
              </div>
            </div>
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
                  <div class="d-flex align-center">
                    <span class="font-weight-bold text-subtitle-2">{{ timeColumn.display_name || timeColumn.column_name }}</span>
                    <v-tooltip v-if="(timeColumn.confidence_score || 1) < 0.9" location="top">
                      <template #activator="{ props }">
                        <v-icon v-bind="props" class="ml-1" color="warning" size="14">mdi-alert-circle-outline</v-icon>
                      </template>
                      <span>Low confidence ({{ Math.round(timeColumn.confidence_score! * 100) }}%): {{ timeColumn.confidence_rationale }}</span>
                    </v-tooltip>
                  </div>
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
                  <div class="d-flex align-center">
                    <span class="font-weight-bold text-subtitle-2 text-primary">{{ targetColumn.display_name || targetColumn.column_name }}</span>
                    <v-tooltip v-if="(targetColumn.confidence_score || 1) < 0.9" location="top">
                      <template #activator="{ props }">
                        <v-icon v-bind="props" class="ml-1" color="warning" size="14">mdi-alert-circle-outline</v-icon>
                      </template>
                      <span>Low confidence ({{ Math.round(targetColumn.confidence_score! * 100) }}%): {{ targetColumn.confidence_rationale }}</span>
                    </v-tooltip>
                  </div>
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
                  <div class="d-flex align-center">
                    <span class="font-weight-bold text-subtitle-2" :class="{ 'text-disabled text-decoration-line-through': isColumnIgnored(feat.column_name) }">
                      {{ feat.display_name || feat.column_name }}
                    </span>
                    <v-tooltip v-if="(feat.confidence_score || 1) < 0.9" location="top">
                      <template #activator="{ props }">
                        <v-icon v-bind="props" class="ml-1" color="warning" size="14">mdi-alert-circle-outline</v-icon>
                      </template>
                      <span>Low confidence ({{ Math.round(feat.confidence_score! * 100) }}%): {{ feat.confidence_rationale }}</span>
                    </v-tooltip>
                  </div>
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
              :horizon-confidence-rationale="store.ontology?.requirements.horizon_requirement.confidence_rationale"
              :horizon-confidence-score="store.ontology?.requirements.horizon_requirement.confidence_score"
            />
          </div>

          <!-- SECTION 1.5: Clarification Hub (Multi-turn) -->
          <div v-if="needsClarification" class="section-card section-card--highlight mb-6">
            <div class="section-header mb-4">
              <div class="section-header__icon section-header__icon--warning">
                <v-icon color="white" size="18">mdi-chat-question-outline</v-icon>
              </div>
              <div>
                <h3 class="text-subtitle-1 font-weight-bold ma-0">Clarification Hub</h3>
                <div class="text-caption text-medium-emphasis mt-1">
                  Confidence: {{ Math.round((store.ontology?.meta.confidence_score || 0) * 100) }}%
                  <template v-if="lowConfidenceColumns.length > 0">
                    · {{ lowConfidenceColumns.length }} column{{ lowConfidenceColumns.length > 1 ? 's' : '' }} need{{ lowConfidenceColumns.length === 1 ? 's' : '' }} review
                  </template>
                  <template v-if="(store.ontology?.requirements.horizon_requirement.confidence_score ?? 1) < 0.85">
                    · Horizon needs review
                  </template>
                </div>
              </div>
            </div>

            <div class="clarification-content pa-4 rounded-lg bg-surface border mb-4">
              <div v-for="(msg, idx) in store.clarificationHistory" :key="idx" class="mb-3">
                <div v-if="msg.role === 'assistant'" class="d-flex align-start">
                  <v-avatar class="mr-2" color="primary" size="24">
                    <v-icon color="white" size="14">mdi-robot-outline</v-icon>
                  </v-avatar>
                  <div class="msg-bubble assistant-bubble pa-2 rounded-lg text-body-2">
                    {{ msg.content }}
                  </div>
                </div>
                <div v-else class="d-flex align-start justify-end">
                  <div class="msg-bubble user-bubble pa-2 rounded-lg text-body-2 bg-primary text-white">
                    {{ msg.content }}
                  </div>
                  <v-avatar class="ml-2" color="secondary" size="24">
                    <v-icon color="white" size="14">mdi-account</v-icon>
                  </v-avatar>
                </div>
              </div>

              <div v-if="store.loading" class="d-flex align-center justify-center py-4">
                <v-progress-circular color="primary" indeterminate size="24" width="2" />
                <span class="ml-3 text-caption text-medium-emphasis">Re-analyzing intent...</span>
              </div>
            </div>

            <!-- Suggested Questions -->
            <div v-if="!store.loading" class="d-flex flex-wrap mb-4" style="gap: 8px;">
              <v-btn
                v-for="q in store.ontology?.meta.clarification_questions"
                :key="q"
                class="text-none"
                color="primary"
                density="comfortable"
                rounded="pill"
                size="small"
                variant="tonal"
                @click="submitClarification(q)"
              >
                {{ q }}
              </v-btn>
            </div>

            <v-text-field
              v-model="clarificationInput"
              append-inner-icon="mdi-send"
              bg-color="surface"
              class="rounded-xl"
              density="comfortable"
              flat
              hide-details
              label="Type your answer..."
              placeholder="e.g., Use 'Sales' as target and 'Price' as controllable."
              variant="solo"
              @click:append-inner="submitClarification()"
              @keyup.enter="submitClarification()"
            />
          </div>

          <!-- SECTION 2: Scenario Overrides -->
          <div v-if="controllableCovariates.length > 0 || exogenousCovariates.length > 0" class="section-card mb-6">
            <div class="section-header mb-4">
              <div class="section-header__icon section-header__icon--secondary">
                <v-icon color="white" size="18">mdi-tune-variant</v-icon>
              </div>
              <div>
                <h3 class="text-subtitle-1 font-weight-bold mb-0">Scenario Configuration</h3>
                <div class="text-caption text-medium-emphasis mt-1">
                  Define how external and controllable factors behave in the forecast window.
                </div>
              </div>
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

          <!-- SECTION 4: Dataset Snapshot -->
          <div class="section-card mb-6">
            <div class="d-flex align-center mb-4">
              <div class="section-header">
                <div class="section-header__icon section-header__icon--primary">
                  <v-icon color="white" size="18">mdi-table-large</v-icon>
                </div>
                <div>
                  <h3 class="text-subtitle-1 font-weight-bold ma-0">Dataset Snapshot</h3>
                  <div class="text-caption text-medium-emphasis mt-1">
                    Preview based on the current ontology. First {{ sampleRows.length }} rows.
                  </div>
                </div>
              </div>
              <v-spacer />
              <v-chip v-if="activeColumnNames.length > 0" size="small" variant="tonal">
                {{ activeColumnNames.length }} active columns
              </v-chip>
            </div>

            <v-card class="d-flex flex-column text-body-2 border layout-card bg-surface" style="border-radius: 12px; overflow-x: auto;" variant="flat">
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

          <!-- SECTION 5: Advanced Data Inspection -->
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
  const clarificationInput = ref('')

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

  // Re-initialize sentenceState whenever ontology changes (initial load + re-analysis)
  watch(() => store.ontology, () => {
    initSentenceState()
  }, { immediate: true })

  onMounted(() => {
    initSentenceState()
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

  async function submitClarification (val?: string) {
    const text = val || clarificationInput.value
    if (!text.trim() || store.loading) return

    await store.analyzeIntent(text)
    clarificationInput.value = ''
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

.section-card--highlight {
  background: rgba(var(--v-theme-primary), 0.05);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.msg-bubble {
  max-width: 80%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.assistant-bubble {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.user-bubble {
  background: rgb(var(--v-theme-primary));
}

/* ─── Column cards ─── */
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
