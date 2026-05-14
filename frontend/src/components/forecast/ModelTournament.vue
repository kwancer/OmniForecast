<template>
  <v-card class="pa-4" variant="outlined">
    <div class="d-flex align-center mb-4">
      <v-icon class="mr-2" color="primary">mdi-podium-gold</v-icon>
      <div class="text-subtitle-1 font-weight-bold">Model Tournament Results</div>
      <v-spacer />
      <v-chip color="primary" size="small" variant="tonal">
        {{ results.length }} Candidates
      </v-chip>
    </div>

    <v-table density="comfortable">
      <thead>
        <tr>
          <th class="text-left">Model Architecture</th>
          <th class="text-center">Complexity</th>
          <th class="text-center">Covariates</th>
          <th class="text-center">MAE</th>
          <th class="text-center">RMSE</th>
          <th class="text-right">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="res in sortedResults" :key="res.model_name" :class="{ 'bg-blue-lighten-5': res.status === 'winner' }">
          <td>
            <div class="font-weight-medium">{{ res.model_name }}</div>
          </td>
          <td class="text-center">
            <v-rating
              active-color="warning"
              density="compact"
              length="5"
              :model-value="res.complexity"
              readonly
              size="x-small"
            />
          </td>
          <td class="text-center">
            <v-icon
              :color="res.supports_covariates ? 'success' : 'grey-lighten-1'"
              :icon="res.supports_covariates ? 'mdi-check-circle' : 'mdi-close-circle'"
              size="18"
            />
            <v-tooltip
              activator="parent"
              location="top"
            >
              {{ res.supports_covariates ? 'Uses covariates' : 'Ignores covariates' }}
            </v-tooltip>
          </td>
          <td class="text-center">
            <code>{{ formatMetric(res.mae, 'MAE') }}</code>
          </td>
          <td class="text-center">
            <code :class="res.status === 'winner' ? 'text-success font-weight-bold' : ''">
              {{ formatRmse(res.rmse, res.mse, res.metrics) }}
            </code>
          </td>
          <td class="text-right">
            <v-chip
              :color="getStatusColor(res.status)"
              label
              size="x-small"
              variant="flat"
            >
              {{ res.status.replace('_', ' ').toUpperCase() }}
            </v-chip>
          </td>
        </tr>
      </tbody>
    </v-table>

    <div class="mt-4 text-caption text-grey-darken-1">
      <v-icon class="mr-1" size="small">mdi-information-outline</v-icon>
      We test several forecasting methods and shortlist those within 5% of the best accuracy. From that shortlist, we pick the <strong>simplest</strong> method that still performs well. The <strong>Forecast Skill Score</strong> shows how much better the winner is than a basic "flat line" guess.
    </div>
  </v-card>
</template>

<script setup lang="ts">
  import type { TournamentResult } from '@/types'
  import { computed } from 'vue'
  import { formatMetric, formatNumber } from '@/utils/formatters'

  const props = defineProps<{
    results: TournamentResult[]
  }>()

  const sortedResults = computed(() => {
    // Sort by RMSE/MSE; fall back to MAE for any model without a finite MSE
    return props.results.toSorted((a: TournamentResult, b: TournamentResult) => {
      const aMse = a.mse ?? Infinity
      const bMse = b.mse ?? Infinity
      return aMse - bMse
    })
  })

  function formatRmse (val: number | undefined | null, mse?: number | undefined | null, metrics?: { name: string, value: number }[]) {
    if (val !== undefined && val !== null && Number.isFinite(val)) {
      return formatNumber(val)
    }
    // Compute RMSE from MSE if direct RMSE is not available
    if (mse !== undefined && mse !== null && Number.isFinite(mse) && mse >= 0) {
      return formatNumber(Math.sqrt(mse))
    }
    // Fallback: look for RMSE in the metrics array
    const rmseMetric = metrics?.find(m => m.name === 'RMSE')
    if (rmseMetric !== undefined && Number.isFinite(rmseMetric.value)) {
      return formatNumber(rmseMetric.value)
    }
    return '—'
  }

  function getStatusColor (status: string) {
    switch (status) {
      case 'winner': {
        return 'success'
      }
      case 'runner_up': {
        return 'primary'
      }
      default: {
        return 'grey'
      }
    }
  }
</script>

<style scoped>
.bg-blue-lighten-5 {
  background-color: rgba(227, 242, 253, 0.5) !important;
}
</style>
