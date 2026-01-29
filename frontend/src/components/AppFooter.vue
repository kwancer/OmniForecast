<template>
  <v-footer border class="text-caption text-medium-emphasis justify-center">
    <div class="d-flex align-center">
      <span>&copy; {{ new Date().getFullYear() }} — OmniForecast</span>
      <v-divider class="mx-3" vertical />
      <router-link class="text-decoration-none text-medium-emphasis" to="/help">Help</router-link>
      <v-divider class="mx-3" vertical />
      <router-link class="text-decoration-none text-medium-emphasis" to="/privacy">Privacy</router-link>
    </div>
  </v-footer>
</template>

<script setup lang="ts">
</script>
