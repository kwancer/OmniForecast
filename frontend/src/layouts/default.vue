<template>
  <AppHeader @toggle-drawer="drawer = !drawer" />

  <v-navigation-drawer v-model="drawer" temporary>
    <v-list>
      <v-list-item
        prepend-icon="mdi-home"
        title="Home"
        to="/"
      ></v-list-item>
      <!-- Placeholder for future functionality -->
      <v-list-item
        prepend-icon="mdi-history"
        title="Past Forecasts"
        disabled
      ></v-list-item>
    </v-list>
  </v-navigation-drawer>

  <v-main>
    <router-view />
  </v-main>

  <AppFooter />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'

const drawer = ref(false)
</script>
