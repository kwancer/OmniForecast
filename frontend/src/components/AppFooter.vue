<template>
  <v-footer
    app
    border="top"
    class="text-caption text-medium-emphasis justify-center py-3"
    elevation="0"
    style="background-color: transparent;"
  >
    <div class="d-flex align-center">
      <span>&copy; {{ new Date().getFullYear() }} — OmniForecast</span>
      <v-divider class="mx-3" vertical />
      <router-link class="text-decoration-none text-medium-emphasis hover-lift d-inline-block" to="/help">Help</router-link>
      <v-divider class="mx-3" vertical />
      <router-link class="text-decoration-none text-medium-emphasis hover-lift d-inline-block" to="/privacy">Privacy</router-link>
    </div>
  </v-footer>
</template>

<script setup lang="ts">
</script>
