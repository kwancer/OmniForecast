<template>
  <v-card variant="flat" border class="pa-2 pa-md-4 bg-surface-variant">
    <div class="text-overline text-primary mb-2 mb-md-4">Data Mapping Strategy</div>
    
    <v-list lines="two" class="bg-transparent pa-0">
      <v-list-item
        v-for="col in ontology?.columns"
        :key="col.column_name"
        class="mb-2 border rounded bg-surface px-2 px-md-4"
      >
        <template v-slot:prepend>
          <v-avatar :color="getRoleColor(col.role)" size="40" variant="tonal" class="mr-2">
            <v-icon :icon="getRoleIcon(col.role)"></v-icon>
          </v-avatar>
        </template>

        <div class="d-flex flex-column py-1">
          <div class="d-flex align-center flex-wrap mb-1">
            <div class="font-mono text-subtitle-1 font-weight-bold mr-2 text-truncate">
              {{ col.column_name }}
            </div>
            <v-chip size="x-small" variant="outlined" :color="getRoleColor(col.role)" class="flex-shrink-0">
              {{ formatRole(col.role) }}
            </v-chip>
          </div>

          <div class="d-flex align-center flex-wrap">
            <v-chip size="x-small" label class="mr-2 mb-1" :color="getTypeColor(col.data_type)">
              {{ col.data_type.toUpperCase() }}
            </v-chip>
            <span class="text-caption text-medium-emphasis mb-1" style="white-space: normal; line-height: 1.2;">
              {{ getRoleDescription(col.role) }}
            </span>
          </div>
        </div>
      </v-list-item>
    </v-list>

    <div class="mt-4 pt-4 border-t d-flex align-center justify-space-between flex-wrap gap-2">
      <div class="d-flex align-center">
        <span class="text-caption text-medium-emphasis mr-2">Detected Cadence:</span>
        <v-chip size="small" color="secondary" variant="tonal">
          {{ ontology?.problem.granularity.unit || 'Unknown' }}
        </v-chip>
      </div>
      <div class="text-caption text-medium-emphasis">
        {{ ontology?.columns.length }} dimensions
      </div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import type { ForecastOntology } from '@/types'

defineProps<{
  ontology: ForecastOntology | null
}>()

const getRoleIcon = (role: string) => {
  switch (role) {
    case 'time_index': return 'mdi-clock-outline'
    case 'target': return 'mdi-target'
    case 'feature': return 'mdi-plus-box-outline'
    default: return 'mdi-database-outline'
  }
}

const getRoleColor = (role: string) => {
  switch (role) {
    case 'time_index': return 'primary'
    case 'target': return 'error'
    case 'feature': return 'success'
    default: return 'medium-emphasis'
  }
}

const getTypeColor = (type: string) => {
  switch (type) {
    case 'datetime': return 'blue'
    case 'numeric': return 'amber'
    case 'categorical': return 'purple'
    default: return 'grey'
  }
}

const getRoleDescription = (role: string) => {
  switch (role) {
    case 'time_index': return 'Timeline for the forecast'
    case 'target': return 'Value we are predicting'
    case 'feature': return 'Factor influencing prediction'
    default: return 'Extra information'
  }
}

const formatRole = (role: string) => {
  switch (role) {
    case 'time_index': return 'Date/Time'
    case 'target': return 'Result'
    case 'feature': return 'Influencer'
    default: return 'Metadata'
  }
}
</script>
