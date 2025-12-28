<template>
  <v-app-bar elevation="1" border>
    <template v-slot:prepend>
      <v-app-bar-nav-icon
        variant="text"
        @click="$emit('toggle-drawer')"
        class="d-md-none"
      ></v-app-bar-nav-icon>
    </template>

    <v-container class="fill-height d-flex align-center py-0" fluid>
      <div class="d-flex align-center cursor-pointer" @click="router.push('/')">
        <v-img
          alt="OmniForecast"
          contain
          src="@/assets/logo.png"
          transition="scale-transition"
          width="40"
          class="mr-3"
        />
        <span class="text-h6 font-weight-bold font-header d-none d-sm-block">OmniForecast</span>
      </div>

      <v-spacer></v-spacer>
      
      <v-btn
        :icon="appStore.theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night'"
        variant="text"
        @click="appStore.toggleTheme"
        class="ml-2"
        color="medium-emphasis"
      ></v-btn>

      <v-btn icon="mdi-account-circle" variant="text" color="medium-emphasis"></v-btn>
    </v-container>
  </v-app-bar>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { useRouter } from 'vue-router'

const appStore = useAppStore()
const router = useRouter()

defineEmits(['toggle-drawer'])
</script>
