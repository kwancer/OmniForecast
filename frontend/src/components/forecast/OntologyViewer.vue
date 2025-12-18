<template>
  <v-card variant="flat" border class="pa-4 bg-surface-variant">
    <div class="text-overline text-primary mb-4">Data Mapping Strategy</div>
    
    <v-list lines="two" class="bg-transparent pa-0">
      <v-list-item
        v-for="col in ontology?.columns"
        :key="col.column_name"
        class="mb-2 border rounded bg-surface"
      >
        <template v-slot:prepend>
          <v-avatar :color="getRoleColor(col.role)" size="40" variant="tonal">
            <v-icon :icon="getRoleIcon(col.role)"></v-icon>
          </v-avatar>
        </template>

        <v-list-item-title class="font-mono text-subtitle-1 font-weight-bold">
          {{ col.column_name }}
        </v-list-item-title>
        
        <v-list-item-subtitle class="d-flex align-center mt-1">
          <v-chip size="x-small" label class="mr-2" :color="getTypeColor(col.data_type)">
            {{ col.data_type.toUpperCase() }}
          </v-chip>
          <span class="text-caption text-medium-emphasis">{{ getRoleDescription(col.role) }}</span>
        </v-list-item-subtitle>

        <template v-slot:append>
          <v-chip size="small" variant="outlined" :color="getRoleColor(col.role)">
            {{ formatRole(col.role) }}
          </v-chip>
        </template>
      </v-list-item>
    </v-list>

    <div class="mt-4 pt-4 border-t d-flex align-center justify-space-between">
      <div>
        <span class="text-caption text-medium-emphasis mr-2">Detected Cadence:</span>
        <v-chip size="small" color="secondary" variant="tonal">
          {{ ontology?.problem.granularity.unit || 'Unknown' }}
        </v-chip>
      </div>
      <div class="text-caption text-medium-emphasis">
        {{ ontology?.columns.length }} total dimensions identified
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
    case 'feature': return 'Factor influencing the prediction'
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
