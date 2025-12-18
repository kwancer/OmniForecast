<template>
  <v-app :theme="appStore.theme">
    <AppHeader />
    
    <v-main>
      <router-view />
    </v-main>

    <NotificationHost />
    <AppFooter />
  </v-app>
</template>

<script setup lang="ts">
import { useAppStore } from './stores/app'
import AppHeader from './components/AppHeader.vue'
import NotificationHost from './components/NotificationHost.vue'

const appStore = useAppStore()
</script>
