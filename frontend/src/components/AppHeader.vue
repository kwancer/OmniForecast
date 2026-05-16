<template>
  <v-app-bar
    border
    :color="appStore.theme === 'dark' ? 'rgba(15, 23, 42, 0.85)' : 'rgba(255, 255, 255, 0.85)'"
    elevation="0"
    style="backdrop-filter: blur(16px);"
  >
    <template #prepend>
      <v-app-bar-nav-icon
        class="d-md-none"
        variant="text"
        @click="$emit('toggle-drawer')"
      />
    </template>

    <v-container class="fill-height d-flex align-center py-0" fluid>
      <div class="d-flex align-center cursor-pointer brand-group" @click="router.push('/')">
        <v-img
          alt="AskForecast"
          class="mr-2 brand-symbol"
          contain
          src="/askforecast_symbol.png"
          transition="scale-transition"
          width="72"
        />
        <span class="brand-wordmark d-none d-sm-flex align-center">
          <span class="brand-ask">Ask</span><span class="brand-forecast">Forecast</span>
        </span>
      </div>

      <!-- Stepper -->
      <template v-if="isHome">
        <div class="d-flex align-center ps-4 ms-6 ms-sm-3" style="gap: 4px;">
          <template v-for="(label, i) in stepLabels" :key="i">
            <div
              class="d-flex align-center cursor-pointer hover-lift rounded-pill px-1 px-md-2 py-1"
              :class="{
                'text-primary font-weight-bold': currentStep === i + 1,
                'text-medium-emphasis': currentStep !== i + 1,
                'opacity-60': currentStep < i + 1
              }"
              style="white-space: nowrap; transition: all 0.3s ease;"
              @click="handleStepClick(i + 1)"
            >
              <v-avatar
                class="me-0 me-md-2"
                :color="currentStep > i + 1 ? 'success' : (currentStep === i + 1 ? 'primary' : 'grey')"
                size="22"
                :variant="currentStep === i + 1 ? 'flat' : 'tonal'"
              >
                <v-icon v-if="currentStep > i + 1" size="14">mdi-check</v-icon>
                <span v-else class="text-caption font-weight-bold">{{ i + 1 }}</span>
              </v-avatar>
              <span class="text-caption d-none d-md-inline" :class="{'font-weight-bold': currentStep === i + 1, 'font-weight-medium': currentStep !== i + 1}">
                {{ label }}
              </span>
            </div>
            <v-divider v-if="i < 2" class="mx-1 mx-md-2" style="height: 20px; opacity: 0.3;" vertical />
          </template>
        </div>
      </template>

      <v-spacer />

      <v-btn
        class="ml-2 hover-lift"
        color="medium-emphasis"
        :icon="appStore.theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night'"
        variant="text"
        @click="appStore.toggleTheme"
      />

      <v-btn class="hover-lift" color="medium-emphasis" icon="mdi-account-circle" variant="text" />
    </v-container>
  </v-app-bar>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useAppStore } from '@/stores/app'
  import { useForecastStore } from '@/stores/forecast'

  const appStore = useAppStore()
  const forecastStore = useForecastStore()
  const router = useRouter()
  const route = useRoute()

  defineEmits(['toggle-drawer'])

  const isHome = computed(() => route.path === '/')

  const stepLabels = ['Upload', 'Review', 'Forecast']

  const currentStep = computed(() => {
    const steps = ['upload', 'plan', 'results'] as const
    const idx = steps.indexOf(forecastStore.step as any)
    return idx === -1 ? 1 : idx + 1
  })

  function handleStepClick (stepNum: number) {
    const steps = ['upload', 'plan', 'results'] as const
    const targetStep = steps[stepNum - 1]
    if (!targetStep) return
    if (targetStep === 'plan' && !forecastStore.ontology) return
    if (targetStep === 'results' && forecastStore.forecastResults.length === 0) return
    forecastStore.setStep(targetStep)
  }
</script>

<style scoped>
  .brand-group {
    transition: opacity 0.2s ease;
  }

  .brand-group:hover {
    opacity: 0.85;
  }

  .brand-symbol {
    transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  }

  .brand-group:hover .brand-symbol {
    transform: scale(1.05);
  }

  .brand-wordmark {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    line-height: 1;
  }

  .brand-ask {
    color: #6366F1; /* Neural Violet */
  }

  .brand-forecast {
    color: #F97316; /* Signal Orange */
  }

  /* Dark mode override via v-theme */
  :root .v-theme--dark .brand-ask {
    color: #818CF8;
  }

  :root .v-theme--dark .brand-forecast {
    color: #FB923C;
  }
</style>
