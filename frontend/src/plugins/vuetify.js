/**
 * plugins/vuetify.js
 *
 * Framework documentation: https://vuetifyjs.com`
 */

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

// Composables
import { createVuetify } from 'vuetify'

// https://vuetifyjs.com/en/introduction/why-vuetify/#feature-guides
export default createVuetify({
  theme: {
    defaultTheme: 'omniTheme',
    themes: {
      omniTheme: {
        dark: true,
        colors: {
          background: '#0F172A', // Void Slate
          surface: '#1E293B',    // Lighter Slate for cards
          primary: '#F97316',    // Signal Orange
          secondary: '#6366F1',  // Neural Violet
          error: '#EF4444',
          info: '#3B82F6',
          success: '#22C55E',
          warning: '#F59E0B',
        },
      },
    },
  },
  defaults: {
    VCard: {
      elevation: 0,
      border: 'thin',
    },
    VBtn: {
      variant: 'flat',
      height: 44,
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VTextarea: {
      variant: 'outlined',
    },
    VFileInput: {
      variant: 'outlined',
    }
  }
})
