import { defineStore } from 'pinia'
import { useAppStore } from './app'
import type { ForecastOntology, ForecastResult, ForecastResponse } from '@/types'

export const useForecastStore = defineStore('forecast', {
  state: () => ({
    file: null as File | null,
    intent: '',
    ontology: null as ForecastOntology | null,
    forecastResults: [] as ForecastResult[],
    explanation: '',
    loading: false,
    step: 'upload' as 'upload' | 'plan' | 'results'
  }),

  getters: {
    timeCol(): string {
      if (!this.ontology) return 'Date'
      const col = this.ontology.columns.find(c => c.role === 'time_index')
      return col ? col.column_name : 'Date'
    },
    targetCol(): string {
      if (!this.ontology) return 'Value'
      const col = this.ontology.columns.find(c => c.role === 'target')
      return col ? col.column_name : 'Value'
    }
  },

  actions: {
    setFile(file: File | null) {
      this.file = file
    },
    
    setIntent(intent: string) {
      this.intent = intent
    },

    setStep(step: 'upload' | 'plan' | 'results') {
      this.step = step
    },

    async analyzeIntent() {
      if (!this.file || !this.intent) return
      
      const appStore = useAppStore()
      this.loading = true
      try {
        const formData = new FormData()
        formData.append('file', this.file)
        formData.append('prompt', this.intent)

        const response = await fetch('http://localhost:8002/plan', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) throw new Error('Analysis failed')
        
        this.ontology = await response.json()
        this.step = 'plan'
        appStore.notify('Signal analysis complete.', 'success')
      } catch (e: any) {
        appStore.notify(e.message || 'Analysis failed', 'error')
      } finally {
        this.loading = false
      }
    },

    async executeForecast() {
      if (!this.file || !this.ontology) return

      const appStore = useAppStore()
      this.loading = true
      try {
        const formData = new FormData()
        formData.append('file', this.file)
        formData.append('ontology_json', JSON.stringify(this.ontology))

        const response = await fetch('http://localhost:8002/forecast', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) throw new Error('Forecast failed')
        
        const data: ForecastResponse = await response.json()
        this.forecastResults = data.forecast
        this.explanation = data.explanation
        this.step = 'results'
        appStore.notify('Forecast execution successful.', 'success')
      } catch (e: any) {
        appStore.notify(e.message || 'Forecast failed', 'error')
      } finally {
        this.loading = false
      }
    },

    reset() {
      this.file = null
      this.intent = ''
      this.ontology = null
      this.forecastResults = []
      this.explanation = ''
      this.step = 'upload'
    }
  }
})
