<template>
  <v-app-bar
    border
    :color="appStore.theme === 'dark' ? 'rgba(24, 24, 27, 0.8)' : 'rgba(255, 255, 255, 0.8)'"
    elevation="0"
    style="backdrop-filter: blur(12px);"
  >
    <template #prepend>
      <v-app-bar-nav-icon
        class="d-md-none"
        variant="text"
        @click="$emit('toggle-drawer')"
      />
    </template>

    <v-container class="fill-height d-flex align-center py-0" fluid>
      <div class="d-flex align-center cursor-pointer group" @click="router.push('/')">
        <v-img
          alt="OmniForecast"
          class="mr-3 rounded-circle"
          contain
          src="@/assets/logo.png"
          transition="scale-transition"
          width="40"
        />
        <span class="text-h6 font-weight-bold font-header d-none d-sm-block text-primary">OmniForecast</span>
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
