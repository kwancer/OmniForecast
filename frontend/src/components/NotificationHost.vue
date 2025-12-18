<template>
  <div>
    <v-snackbar
      v-for="note in appStore.notifications"
      :key="note.id"
      v-model="activeNotes[note.id]"
      :color="note.type"
      :timeout="note.timeout"
      location="top right"
      @update:model-value="(val) => !val && appStore.removeNotification(note.id)"
    >
      {{ note.message }}
      
      <template v-slot:actions>
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
import { useAppStore } from '@/stores/app'
import { reactive, watch } from 'vue'

const appStore = useAppStore()
const activeNotes = reactive<Record<string, boolean>>({})

watch(() => appStore.notifications, (newNotes) => {
  newNotes.forEach(note => {
    if (activeNotes[note.id] === undefined) {
      activeNotes[note.id] = true
    }
  })
}, { deep: true })
</script>
