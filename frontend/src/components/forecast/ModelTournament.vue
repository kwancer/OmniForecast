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
          <th class="text-center">MAE (Error)</th>
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
            <code>{{ res.mae.toFixed(4) }}</code>
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
      The tournament uses a <strong>Rashomon Set</strong> approach: we consider all models within 5% of the lowest error, and then select the one with the <strong>lowest complexity</strong> (Occam's Razor).
    </div>
  </v-card>
</template>

<script setup lang="ts">
  import type { TournamentResult } from '@/types'
  import { computed } from 'vue'

  const props = defineProps<{
    results: TournamentResult[]
  }>()

  const sortedResults = computed(() => {
    return [...props.results].sort((a, b) => a.mae - b.mae)
  })

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
