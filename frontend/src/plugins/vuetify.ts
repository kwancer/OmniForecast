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
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          'primary': '#6366F1', // Neural Violet — AI/Intent Layer
          'secondary': '#F97316', // Signal Orange — Forecast/Action
          'surface': '#FFFFFF', // Paper White — Clarity
          'background': '#FAFAFA',
          'surface-light': '#F1F0FB', // Violet-tinted light surface
          'on-background': '#0F172A', // Void Slate text
          'on-surface': '#0F172A', // Void Slate text
          'error': '#EF4444',
          'info': '#6366F1', // Neural Violet for info
          'success': '#10B981',
          'warning': '#F97316', // Signal Orange
          'void-slate': '#0F172A',
          'signal-orange': '#F97316',
          'neural-violet': '#6366F1',
        },
      },
      dark: {
        dark: true,
        colors: {
          'primary': '#818CF8', // Neural Violet — brighter for dark bg
          'secondary': '#FB923C', // Signal Orange — brighter for dark bg
          'surface': '#1E293B', // Slate-800
          'background': '#0F172A', // Void Slate — calm authority
          'surface-light': '#334155', // Slate-700
          'on-background': '#F1F5F9',
          'on-surface': '#F1F5F9',
          'error': '#F87171',
          'info': '#818CF8', // Neural Violet
          'success': '#34D399',
          'warning': '#FB923C', // Signal Orange
          'void-slate': '#0F172A',
          'signal-orange': '#FB923C',
          'neural-violet': '#818CF8',
        },
      },
    },
  },
  defaults: {
    VApp: {
      class: 'font-body',
    },
    VCard: {
      rounded: 'xl',
      border: true,
      elevation: 0,
      class: 'border-opacity-50 border-s-sm border-s-white',
    },
    VBtn: {
      variant: 'flat',
      rounded: 'lg',
      class: 'font-weight-bold text-none',
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
