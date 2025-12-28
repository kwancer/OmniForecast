<template>
  <v-app :theme="appStore.theme">
    <router-view />
    <NotificationHost />
  </v-app>
</template>

<script setup lang="ts">
import { useAppStore } from './stores/app'
import NotificationHost from './components/NotificationHost.vue'

const appStore = useAppStore()
</script>
