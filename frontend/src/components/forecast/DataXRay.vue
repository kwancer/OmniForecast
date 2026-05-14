<template>
  <v-expansion-panels class="mb-6" outlined>
    <v-expansion-panel>
      <v-expansion-panel-title>
        <div class="d-flex align-center">
          <v-icon class="mr-3" color="primary">mdi-chart-box-outline</v-icon>
          <span class="text-subtitle-1 font-weight-bold">Advanced Data Inspection</span>
          <v-chip class="ml-3" color="primary" size="x-small" variant="tonal">
            {{ ontology.meta.domain_inference }}
          </v-chip>
        </div>
      </v-expansion-panel-title>

      <v-expansion-panel-text>
        <v-row class="mb-2 mt-2">
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis mb-1">Data Completeness</div>
            <div class="d-flex align-center">
              <v-icon class="mr-1" :color="ontology.meta.completeness_check === 'complete' ? 'success' : 'warning'" icon="mdi-circle-medium" />
              <span class="font-weight-bold text-capitalize">{{ ontology.meta.completeness_check }}</span>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis mb-1">Time Regularity</div>
            <div class="d-flex align-center">
              <v-icon class="mr-1" :color="ontology.problem.granularity.is_regular ? 'success' : 'error'" icon="mdi-circle-medium" />
              <span class="font-weight-bold">{{ ontology.problem.granularity.is_regular ? 'Regular Intervals' : 'Irregular/Gaps' }}</span>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-caption text-medium-emphasis mb-1">Target Sparsity</div>
            <div class="d-flex align-center">
              <v-progress-linear
                class="mr-3"
                color="primary"
                height="8"
                :model-value="sparsityPercent"
                rounded
                style="width: 80px"
              />
              <span class="font-weight-bold">{{ formatNumber(sparsityPercent, { decimals: 1 }) }}% Zeros</span>
            </div>
          </v-col>
        </v-row>

        <v-divider class="mb-4 mt-2" />

        <!-- Column details table -->
        <div class="text-overline mb-3">Column Metadata</div>
        <v-table class="bg-transparent text-caption" density="compact">
          <thead>
            <tr>
              <th class="text-left">Column</th>
              <th class="text-left">Role</th>
              <th class="text-left">Data Type</th>
              <th class="text-left hidden-sm-and-down">How It Is Used</th>
              <th class="text-left hidden-sm-and-down">
                <v-tooltip location="top">
                  <template #activator="{ props: tip }">
                    <span v-bind="tip" class="cursor-help">Resampling <v-icon size="12" color="medium-emphasis">mdi-information-outline</v-icon></span>
                  </template>
                  <span>How values were combined when multiple rows fall into the same time period (e.g., daily data grouped into months).</span>
                </v-tooltip>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="col in ontology.columns" :key="col.column_name" :class="{ 'opacity-40': col.role === 'ignore' }">
              <td class="font-weight-bold font-mono">{{ col.display_name || col.column_name }}</td>
              <td>
                <v-tooltip location="top">
                  <template #activator="{ props: tip }">
                    <span v-bind="tip">
                      <v-chip
                        :color="getRoleColor(col.role)"
                        size="x-small"
                        :variant="col.role === 'ignore' ? 'outlined' : 'flat'"
                      >
                        {{ formatRoleLabel(col.role) }}
                      </v-chip>
                    </span>
                  </template>
                  <span>{{ getRoleTooltip(col.role) }}</span>
                </v-tooltip>
              </td>
              <td class="text-capitalize">{{ col.data_type }}</td>
              <td class="hidden-sm-and-down">
                <v-tooltip v-if="col.covariate_type" location="top">
                  <template #activator="{ props: tip }">
                    <span v-bind="tip">
                      <v-chip
                        :color="getCovariateColor(col.covariate_type)"
                        size="x-small"
                        variant="tonal"
                      >
                        {{ formatCovariateType(col.covariate_type) }}
                      </v-chip>
                    </span>
                  </template>
                  <span>{{ getCovariateTooltip(col.covariate_type) }}</span>
                </v-tooltip>
                <span v-else class="text-medium-emphasis">—</span>
              </td>
              <td class="hidden-sm-and-down text-capitalize">{{ col.resampling_method || '—' }}</td>
            </tr>
          </tbody>
        </v-table>

      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup lang="ts">
  import type { ColumnRole, CovariateType, ForecastOntology } from '@/types'
  import { computed } from 'vue'
  import { formatNumber } from '@/utils/formatters'

  const props = defineProps<{
    ontology: ForecastOntology
  }>()

  const sparsityPercent = computed(() => {
    const target = props.ontology.columns.find(c => c.role === 'target')
    const ratio = target?.constraints?.sparsity_ratio ?? 0
    return ratio * 100
  })

  function getRoleColor (role: ColumnRole): string {
    switch (role) {
      case 'target': { return 'primary'
      }
      case 'time_index': { return 'secondary'
      }
      case 'group_id': { return 'warning'
      }
      case 'covariate': { return 'info'
      }
      case 'ignore': { return 'grey'
      }
      default: { return 'grey'
      }
    }
  }

  function formatRoleLabel (role: ColumnRole): string {
    switch (role) {
      case 'time_index': { return 'TIMELINE'
      }
      case 'group_id': { return 'GROUP'
      }
      case 'covariate': { return 'FACTOR'
      }
      default: { return role.replace('_', ' ').toUpperCase()
      }
    }
  }

  function getRoleTooltip (role: ColumnRole): string {
    switch (role) {
      case 'target': { return 'The value you want to forecast'
      }
      case 'time_index': { return 'The date or time column that defines the sequence'
      }
      case 'group_id': { return 'Identifies separate series when you have multiple items'
      }
      case 'covariate': { return 'An additional factor that may help explain or predict the target'
      }
      case 'ignore': { return 'This column is not being used in the forecast'
      }
      default: { return ''
      }
    }
  }

  function getCovariateColor (type?: CovariateType): string {
    switch (type) {
      case 'known_future':
      case 'controllable': { return 'success'
      }
      case 'unknown_past':
      case 'exogenous': { return 'info'
      }
      case 'static': { return 'grey'
      }
      default: { return 'grey'
      }
    }
  }

  function formatCovariateType (type?: CovariateType): string {
    switch (type) {
      case 'known_future':
      case 'controllable': { return 'Planned'
      }
      case 'unknown_past':
      case 'exogenous': { return 'External'
      }
      case 'static': { return 'Static'
      }
      default: { return '—'
      }
    }
  }

  function getCovariateTooltip (type?: CovariateType): string {
    switch (type) {
      case 'known_future':
      case 'controllable': { return 'You can control or plan this factor (e.g., marketing spend, price)'
      }
      case 'unknown_past':
      case 'exogenous': { return 'You cannot control this factor (e.g., weather, market index)'
      }
      case 'static': { return 'A fixed property that does not change over time'
      }
      default: { return ''
      }
    }
  }
</script>

<style scoped>
.font-mono {
  font-family: 'Roboto Mono', monospace;
}
</style>
