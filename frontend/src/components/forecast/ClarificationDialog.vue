<template>
  <v-dialog
    v-model="visible"
    max-width="700"
    persistent
    scrollable
    transition="dialog-bottom-transition"
  >
    <v-card class="rounded-xl overflow-hidden" elevation="24">
      <!-- Header -->
      <div class="pa-6 pb-4 bg-primary d-flex align-center">
        <div>
          <h2 class="text-h5 font-weight-bold text-white mb-0">More information need</h2>
          <div class="text-caption text-white opacity-80 mt-1">
            We need a few details to generate your forecast
          </div>
        </div>
        <v-spacer />
      </div>

      <v-card-text class="pa-0 bg-background overflow-y-auto" style="height: 450px;">
        <div class="pa-6">
          <div v-for="(msg, idx) in store.clarificationHistory" :key="idx" class="mb-4">
            <!-- Assistant Message -->
            <div v-if="msg.role === 'assistant'" class="d-flex align-start mb-2">
              <v-avatar class="mr-2 mt-1" color="primary" size="28">
                <v-icon color="white" size="16">mdi-robot-outline</v-icon>
              </v-avatar>
              <div class="msg-bubble assistant-bubble pa-4 rounded-xl text-body-2 shadow-sm border">
                <div v-html="formatMessage(msg.content)" />
              </div>
            </div>

            <!-- User Message -->
            <div v-else class="d-flex align-start justify-end mb-2">
              <div class="msg-bubble user-bubble pa-4 rounded-xl text-body-2 bg-primary text-white shadow-sm">
                {{ msg.content }}
              </div>
              <v-avatar class="ml-2 mt-1" color="secondary" size="28">
                <v-icon color="white" size="16">mdi-account</v-icon>
              </v-avatar>
            </div>
          </div>

          <div v-if="store.loading" class="d-flex align-center justify-center py-4">
            <v-progress-circular color="primary" indeterminate size="24" width="2" />
            <span class="ml-3 text-caption text-medium-emphasis">Analyzing your response...</span>
          </div>
        </div>
      </v-card-text>

      <v-divider />

      <v-card-actions class="pa-6 flex-column align-stretch">


        <!-- Input Area -->
        <div class="d-flex align-center">
          <v-text-field
            v-model="input"
            append-inner-icon="mdi-send"
            bg-color="surface"
            class="rounded-xl flex-grow-1 shadow-sm"
            density="comfortable"
            flat
            hide-details
            label="Provide more context..."
            placeholder="e.g., Use 'Sales' as target and 'Price' as a planned driver."
            variant="solo"
            :loading="store.loading"
            @click:append-inner="submit()"
            @keyup.enter="submit()"
          />
        </div>

        <div class="d-flex align-center justify-space-between mt-4">
          <v-btn
            class="text-none"
            color="medium-emphasis"
            prepend-icon="mdi-pencil-outline"
            variant="text"
            @click="bypass"
          >
            I'll edit the ontology manually
          </v-btn>

          <v-chip
            v-if="confidenceScore !== null"
            :color="confidenceColor"
            size="small"
            variant="flat"
          >
            <v-icon start size="14">{{ confidenceScore >= 0.85 ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
            Confidence: {{ Math.round(confidenceScore * 100) }}%
          </v-chip>
        </div>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useForecastStore } from '@/stores/forecast'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits(['update:modelValue', 'bypass'])

const store = useForecastStore()
const input = ref('')

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})



const confidenceScore = computed(() => {
  return store.ontology?.meta.confidence_score ?? null
})

const confidenceColor = computed(() => {
  if (confidenceScore.value === null) return 'grey'
  if (confidenceScore.value >= 0.85) return 'success'
  if (confidenceScore.value >= 0.6) return 'warning'
  return 'error'
})

async function submit(val?: string) {
  const text = (typeof val === 'string' ? val : input.value) || ''
  if (!text.trim() || store.loading) return

  await store.analyzeIntent(text)
  input.value = ''
  
  // If confidence is now high enough, we could auto-close, 
  // but let's let the parent handle the visibility based on needsClarification
}

function bypass() {
  emit('bypass')
}

function formatMessage(content: string) {
  // Simple line break replacement
  return content.replace(/\n/g, '<br>')
}
</script>

<style scoped>
.msg-bubble {
  max-width: 85%;
  line-height: 1.5;
}

.assistant-bubble {
  background: white;
  border-color: rgba(var(--v-theme-primary), 0.1) !important;
}

.user-bubble {
  background: rgb(var(--v-theme-primary));
  color: white;
}

.shadow-sm {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.15);
}
</style>
