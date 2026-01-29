<template>
  <v-card border class="pa-2 pa-md-4" variant="flat">
    <div class="text-overline text-primary mb-2 mb-md-4">Data Mapping Strategy</div>

    <v-list class="bg-transparent pa-0" lines="two">
      <v-list-item
        v-for="col in ontology?.columns"
        :key="col.column_name"
        class="mb-2 border rounded bg-surface px-2 px-md-4"
      >
        <template #prepend>
          <v-avatar class="mr-2" :color="getRoleColor(col.role)" size="40" variant="tonal">
            <v-icon :icon="getRoleIcon(col.role)" />
          </v-avatar>
        </template>

        <div class="d-flex flex-column py-1">
          <div class="d-flex align-center flex-wrap mb-1">
            <div class="font-mono text-subtitle-1 font-weight-bold mr-2 text-truncate">
              {{ col.column_name }}
            </div>
            <v-chip class="flex-shrink-0" :color="getRoleColor(col.role)" size="x-small" variant="outlined">
              {{ formatRole(col.role) }}
            </v-chip>
          </div>

          <div class="d-flex align-center flex-wrap">
            <v-chip class="mr-2 mb-1" :color="getTypeColor(col.data_type)" label size="x-small">
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
        <span class="text-caption text-medium-emphasis mr-2">Resolution</span>
        <v-chip color="secondary" size="small" variant="tonal">
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

  function getRoleIcon (role: string) {
    switch (role) {
      case 'time_index': { return 'mdi-clock-outline'
      }
      case 'target': { return 'mdi-target'
      }
      case 'feature': { return 'mdi-plus-box-outline'
      }
      default: { return 'mdi-database-outline'
      }
    }
  }

  function getRoleColor (role: string) {
    switch (role) {
      case 'time_index': { return 'primary'
      }
      case 'target': { return 'error'
      }
      case 'feature': { return 'success'
      }
      default: { return 'medium-emphasis'
      }
    }
  }

  function getTypeColor (type: string) {
    switch (type) {
      case 'datetime': { return 'blue'
      }
      case 'numeric': { return 'amber'
      }
      case 'categorical': { return 'purple'
      }
      default: { return 'grey'
      }
    }
  }

  function getRoleDescription (role: string) {
    switch (role) {
      case 'time_index': { return 'Timeline for the forecast'
      }
      case 'target': { return 'Value we are predicting'
      }
      case 'feature': { return 'Factor influencing prediction'
      }
      default: { return 'Extra information'
      }
    }
  }

  function formatRole (role: string) {
    switch (role) {
      case 'time_index': { return 'Date/Time'
      }
      case 'target': { return 'Result'
      }
      case 'feature': { return 'Influencer'
      }
      default: { return 'Metadata'
      }
    }
  }
</script>
