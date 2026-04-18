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
  import { useRouter } from 'vue-router'
  import { useAppStore } from '@/stores/app'

  const appStore = useAppStore()
  const router = useRouter()

  defineEmits(['toggle-drawer'])
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
