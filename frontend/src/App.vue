<template>
  <v-app :theme="appStore.theme">
    <router-view />
    <NotificationHost />
  </v-app>
</template>

<script setup lang="ts">
  import NotificationHost from './components/NotificationHost.vue'
  import { useAppStore } from './stores/app'

  const appStore = useAppStore()
</script>
