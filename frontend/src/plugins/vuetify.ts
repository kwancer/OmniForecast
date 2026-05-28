import { createVuetify } from 'vuetify'
import '@mdi/font/css/materialdesignicons.css'

import 'vuetify/styles'

export default createVuetify({
  theme: {
    defaultTheme: 'omniTheme',
    themes: {
      omniTheme: {
        dark: true,
        colors: {
          background: '#0F172A',
          surface: '#1E293B',
          primary: '#F97316',
          secondary: '#6366F1',
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
    },
  },
})
