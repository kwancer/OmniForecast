<template>
  <v-footer border class="text-caption text-medium-emphasis justify-center">
    <div class="d-flex align-center">
      <span>&copy; {{ new Date().getFullYear() }} — OmniForecast</span>
      <v-divider vertical class="mx-3" />
      <router-link to="/help" class="text-decoration-none text-medium-emphasis">Help</router-link>
      <v-divider vertical class="mx-3" />
      <router-link to="/privacy" class="text-decoration-none text-medium-emphasis">Privacy</router-link>
    </div>
  </v-footer>
</template>

<script setup lang="ts">
</script>


