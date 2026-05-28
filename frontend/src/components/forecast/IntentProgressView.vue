<template>
  <v-container class="fill-height d-flex flex-column align-center justify-center pa-4">
    <v-row class="ma-0 w-100" justify="center">
      <v-col cols="12" lg="6" md="8">
        <!-- Progress Card -->
        <v-card class="pa-8 d-flex flex-column align-center text-center" elevation="8">
          <v-progress-circular
            class="mb-6"
            color="primary"
            indeterminate
            size="64"
            width="6"
          />
          <h2 class="text-h4 font-header mb-4">Analysing Your Data</h2>

          <v-card class="w-100 text-left" color="primary" variant="tonal">
            <v-card-text>
              <transition mode="out-in" name="fade-slide">
                <div :key="currentMessageIndex" class="message-container">
                  <div class="d-flex align-start">
                    <v-icon class="mr-3 mt-1" color="primary" size="20">mdi-information</v-icon>
                    <p class="text-body-2 ma-0 font-weight-medium">{{ messages[currentMessageIndex] }}</p>
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
  import { onBeforeUnmount, onMounted, ref } from 'vue'

  const messages = [
    'Reading your data and getting a first look at the numbers...',
    'Identifying which columns are dates, targets, and supporting factors...',
    'Understanding your forecast goal and how the columns relate to each other...',
    'Preparing everything for the forecasting step...',
  ]

  const currentMessageIndex = ref(0)
  let messageInterval: number | null = null

  onMounted(() => {
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
