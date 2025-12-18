import { defineStore } from 'pinia'
import type { AppNotification, NotificationType } from '@/types'

export const useAppStore = defineStore('app', {
  state: () => ({
    notifications: [] as AppNotification[],
    theme: 'dark' as 'light' | 'dark',
  }),

  actions: {
    notify(message: string, type: NotificationType = 'info', timeout = 5000) {
      const id = Math.random().toString(36).substring(2, 9)
      this.notifications.push({ id, message, type, timeout })
    },

    removeNotification(id: string) {
      this.notifications = this.notifications.filter(n => n.id !== id)
    },

    setTheme(theme: 'light' | 'dark') {
      this.theme = theme
    },

    toggleTheme() {
      this.theme = this.theme === 'light' ? 'dark' : 'light'
    }
  },
})
