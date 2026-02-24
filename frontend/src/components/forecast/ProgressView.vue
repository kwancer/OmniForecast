<template>
  <v-container class="fill-height d-flex flex-column align-center justify-center pa-4">
    <v-row class="ma-0 w-100" justify="center">
      <v-col cols="12" lg="6" md="8">
        <!-- Progress Card -->
        <v-card class="pa-8" elevation="8">
          <div class="text-center mb-8">
            <v-icon color="primary" size="64">mdi-chart-timeline-variant</v-icon>
            <h2 class="text-h4 font-header mt-4">Running Forecast</h2>
            <p class="text-body-1 text-medium-emphasis mt-2">
              Evaluating models to find the optimal forecast...
            </p>
          </div>

          <!-- Progress Bar -->
          <div class="mb-6">
            <div class="d-flex justify-space-between align-center mb-2">
              <span class="text-caption text-medium-emphasis">Progress</span>
              <span class="text-caption font-weight-bold">
                {{ progressPercent }}%
              </span>
            </div>
            <v-progress-linear
              color="primary"
              height="12"
              :model-value="progressPercent"
              rounded
              striped
            />
            <div class="text-center mt-2 text-caption text-medium-emphasis">
              {{ current }} of {{ total }} models evaluated
            </div>
          </div>

          <!-- Current Model -->
          <v-card class="mb-6" color="primary" variant="tonal">
            <v-card-text>
              <div class="text-caption text-medium-emphasis mb-1">CURRENT MODEL</div>
              <div class="d-flex align-center">
                <v-progress-circular
                  v-if="!completed"
                  class="mr-3"
                  color="primary"
                  indeterminate
                  size="24"
                  width="3"
                />
                <v-icon v-else class="mr-3" color="success" size="24">mdi-check-circle</v-icon>
                <span class="text-h6 font-weight-medium">{{ currentModel }}</span>
              </div>
            </v-card-text>
          </v-card>

          <!-- Rotating Messages -->
          <v-card color="primary" variant="tonal">
            <v-card-text>
              <transition mode="out-in" name="fade-slide">
                <div :key="currentMessageIndex" class="message-container">
                  <div class="d-flex align-start">
                    <v-icon class="mr-3 mt-1" color="primary" size="20">mdi-information</v-icon>
                    <p class="text-body-2 ma-0">{{ messages[currentMessageIndex] }}</p>
                  </div>
                </div>
              </transition>
            </v-card-text>
          </v-card>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
  import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

  const props = defineProps<{
    current: number
    total: number
    currentModel: string
    completed: boolean
  }>()

  const progressPercent = computed(() => {
    if (props.total === 0) return 0
    return Math.round((props.current / props.total) * 100)
  })

  const messages = [
    'Our forecasting pipeline is fully reproducible, unlike famous LLMs which can give different forecasts from the same data.',
    'We run a frugal tournament across multiple models, selecting the winner based on both accuracy and simplicity using Occam\'s Razor.',
    'All forecasts include confidence intervals calibrated to your data, helping you understand the uncertainty in predictions.',
  ]

  const currentMessageIndex = ref(0)
  let messageInterval: number | null = null

  onMounted(() => {
    // Rotate messages every 4 seconds
    messageInterval = window.setInterval(() => {
      currentMessageIndex.value = (currentMessageIndex.value + 1) % messages.length
    }, 4000)
  })

  onBeforeUnmount(() => {
    if (messageInterval !== null) {
      clearInterval(messageInterval)
    }
  })
</script>

<style scoped>
  .message-container {
    min-height: 60px;
    display: flex;
    align-items: center;
  }

  .fade-slide-enter-active,
  .fade-slide-leave-active {
    transition: opacity 0.35s ease, transform 0.35s ease;
  }

  .fade-slide-enter-from,
  .fade-slide-leave-to {
    opacity: 0;
    transform: translateY(6px);
  }

  .fade-slide-enter-to,
  .fade-slide-leave-from {
    opacity: 1;
    transform: translateY(0);
  }
</style>
