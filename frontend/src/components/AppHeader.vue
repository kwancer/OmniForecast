<template>
  <v-app-bar border elevation="1">
    <template #prepend>
      <v-app-bar-nav-icon
        class="d-md-none"
        variant="text"
        @click="$emit('toggle-drawer')"
      />
    </template>

    <v-container class="fill-height d-flex align-center py-0" fluid>
      <div class="d-flex align-center cursor-pointer" @click="router.push('/')">
        <v-img
          alt="OmniForecast"
          class="mr-3"
          contain
          src="@/assets/logo.png"
          transition="scale-transition"
          width="40"
        />
        <span class="text-h6 font-weight-bold font-header d-none d-sm-block">OmniForecast</span>
      </div>

      <v-spacer />

      <v-btn
        class="ml-2"
        color="medium-emphasis"
        :icon="appStore.theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night'"
        variant="text"
        @click="appStore.toggleTheme"
      />

      <v-btn color="medium-emphasis" icon="mdi-account-circle" variant="text" />
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
