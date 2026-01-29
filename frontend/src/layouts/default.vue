<template>
  <AppHeader @toggle-drawer="drawer = !drawer" />

  <v-navigation-drawer v-model="drawer" temporary>
    <v-list>
      <v-list-item
        prepend-icon="mdi-home"
        title="Home"
        to="/"
      />
      <!-- Placeholder for future functionality -->
      <v-list-item
        disabled
        prepend-icon="mdi-history"
        title="Past Forecasts"
      />
    </v-list>
  </v-navigation-drawer>

  <v-main>
    <router-view />
  </v-main>

  <AppFooter />
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import AppFooter from '@/components/AppFooter.vue'
  import AppHeader from '@/components/AppHeader.vue'

  const drawer = ref(false)
</script>
