<template>
  <div>
    <v-snackbar
      v-for="note in appStore.notifications"
      :key="note.id"
      v-model="activeNotes[note.id]"
      :color="note.type"
      location="top right"
      :timeout="note.timeout"
      @update:model-value="(val) => !val && appStore.removeNotification(note.id)"
    >
      {{ note.message }}

      <template #actions>
        <v-btn
          variant="text"
          @click="appStore.removeNotification(note.id)"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
  import { reactive, watch } from 'vue'
  import { useAppStore } from '@/stores/app'

  const appStore = useAppStore()
  const activeNotes = reactive<Record<string, boolean>>({})

  watch(() => appStore.notifications, newNotes => {
    for (const note of newNotes) {
      if (activeNotes[note.id] === undefined) {
        activeNotes[note.id] = true
      }
    }
  }, { deep: true })
</script>
