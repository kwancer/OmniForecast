import type { CleaningReport, DataHealthReport, ForecastMetric, ForecastOntology, ForecastResponse, ForecastResult, ModelMetadata } from '@/types'
import { defineStore } from 'pinia'
import { useAppStore } from './app'

export const useForecastStore = defineStore('forecast', {
  state: () => ({
    file: null as File | null,
    intent: '',
    ontology: null as ForecastOntology | null,
    cleaningReport: null as CleaningReport | null,
    forecastResults: [] as ForecastResult[],
    metrics: [] as ForecastMetric[],
    explanation: '',
    loading: false,
    historyResults: [] as ForecastResult[], // <--- New State
    dataHealthReport: null as DataHealthReport | null,
    step: 'upload' as 'upload' | 'plan' | 'cleaning' | 'results',
    modelMetadata: null as ModelMetadata | null, // <--- ADDED
  }),

  getters: {
    timeCol (): string {
      if (!this.ontology) {
        return 'Date'
      }
      const col = this.ontology.columns.find(c => c.role === 'time_index')
      return col ? col.column_name : 'Date'
    },
    targetCol (): string {
      if (!this.ontology) {
        return 'Value'
      }
      const col = this.ontology.columns.find(c => c.role === 'target')
      return col ? col.column_name : 'Value'
    },
  },

  actions: {
    setFile (file: File | null) {
      this.file = file
    },

    setIntent (intent: string) {
      this.intent = intent
    },

    setStep (step: 'upload' | 'plan' | 'cleaning' | 'results') {
      this.step = step
    },

    async analyzeIntent () {
      if (!this.file || !this.intent) {
        return
      }

      const appStore = useAppStore()
      this.loading = true
      try {
        const formData = new FormData()
        formData.append('file', this.file)
        formData.append('prompt', this.intent)

        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8002'}/plan`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Analysis failed')
        }

        this.ontology = await response.json()
        console.log('Analysed Data Ontology:', this.ontology)
        this.step = 'plan'
        appStore.notify('Signal analysis complete.', 'success')
      } catch (error: any) {
        appStore.notify(error.message || 'Analysis failed', 'error')
      } finally {
        this.loading = false
      }
    },

    async executeForecast () {
      if (!this.file || !this.ontology) {
        return
      }

      const appStore = useAppStore()
      this.loading = true
      try {
        const formData = new FormData()
        formData.append('file', this.file)
        formData.append('ontology_json', JSON.stringify(this.ontology))

        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8002'}/forecast`, {
          method: 'POST',
          body: formData,
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Forecast failed')
        }

        const data: ForecastResponse = await response.json()
        this.forecastResults = data.forecast
        this.explanation = data.explanation
        this.cleaningReport = data.cleaning_report
        this.metrics = data.metrics
        this.historyResults = data.history
        this.modelMetadata = data.model_metadata ?? null
        this.dataHealthReport = data.data_health_report ?? null
        // Move to cleaning step first to show what happened
        this.step = 'cleaning'
        appStore.notify('Modelling sequence complete.', 'success')
      } catch (error: any) {
        appStore.notify(error.message || 'Forecast failed', 'error')
      } finally {
        this.loading = false
      }
    },

    loadSampleData () {
      const csvContent = `Date,Daily_Sales,Store_Region,Promotional_Active
2023-01-01,120.5,North,No
2023-01-02,135.2,North,No
2023-01-03,110.8,North,Yes
2023-01-04,145.0,North,No
2023-01-05,160.2,North,No
2023-01-06,155.5,North,No
2023-01-07,140.1,North,No
2023-01-08,125.4,North,No
2023-01-09,130.2,North,No
2023-01-10,142.1,North,Yes`

      const blob = new Blob([csvContent], { type: 'text/csv' })
      const file = new File([blob], 'sample_sales_data.csv', { type: 'text/csv' })

      this.file = file
      this.intent = 'Forecast daily sales for the next 7 days, considering the recent promotional activity.'
      this.setStep('upload')

      const appStore = useAppStore()
      appStore.notify('Sample sales data loaded successfully.', 'success')
    },

    reset () {
      this.file = null
      this.intent = ''
      this.ontology = null
      this.cleaningReport = null
      this.forecastResults = []
      this.metrics = []
      this.explanation = ''
      this.dataHealthReport = null
      this.step = 'upload'
      this.modelMetadata = null // ADDED
    },
  },
})
