/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Composables
import { createVuetify } from 'vuetify'
// Styles
import '@mdi/font/css/materialdesignicons.css'

import 'vuetify/styles'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'dark',
    themes: {
      light: {
        dark: false,
        colors: {
          'primary': '#4F46E5', // Indigo
          'secondary': '#0D9488', // Teal
          'surface': '#FFFFFF',
          'background': '#FAFAFA',
          'surface-light': '#F3F4F6', // Lighter background
          'error': '#EF4444',
          'info': '#3B82F6',
          'success': '#10B981',
          'warning': '#F59E0B',
        },
      },
      dark: {
        dark: true,
        colors: {
          'primary': '#6366F1', // Indigo a bit lighter
          'secondary': '#14B8A6', // Vibrant Teal
          'surface': '#18181B', // Zinc-900
          'background': '#09090B', // Zinc-950
          'surface-light': '#27272A', // Zinc-800
          'error': '#F87171',
          'info': '#60A5FA',
          'success': '#34D399',
          'warning': '#FBBF24',
        },
      },
    },
  },
  defaults: {
    VApp: {
      class: 'font-body', // Hook to our main font implicitly or relying on SASS
    },
    VCard: {
      rounded: 'xl',
      border: true,
      elevation: 0,
      class: 'border-opacity-50 border-s-sm border-s-white', // Slight glass touch
    },
    VBtn: {
      variant: 'flat',
      rounded: 'lg',
      class: 'font-weight-bold text-none', // Removes uppercase text standard
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
      rounded: 'lg',
    },
  },
})
