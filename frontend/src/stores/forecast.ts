import type { BacktestPoint, CleaningReport, DataHealthReport, ExplainabilityMessage, ExplainabilityResponse, ForecastMetric, ForecastOntology, ForecastResponse, ForecastResult, ModelMetadata, TournamentResult } from '@/types'
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
    step: 'upload' as 'upload' | 'plan' | 'results',
    modelMetadata: null as ModelMetadata | null,
    tournamentResults: [] as TournamentResult[],
    backtestData: [] as BacktestPoint[],
    // Progress tracking
    showProgress: false,
    progressCurrent: 0,
    progressTotal: 0,
    progressCurrentModel: '',
    progressCompleted: false,
    // Explainability chat
    explainabilityMessages: [] as ExplainabilityMessage[],
    askingExplainability: false,
    suggestedQuestions: [] as string[],
    // Multi-turn clarification
    clarificationHistory: [] as { role: 'assistant' | 'user', content: string }[],
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

    setStep (step: 'upload' | 'plan' | 'results') {
      this.step = step
    },

    async analyzeIntent (answer?: string) {
      if (!this.file || !this.intent) {
        return
      }

      const appStore = useAppStore()
      this.loading = true

      if (answer && typeof answer === 'string') {
        this.clarificationHistory.push({ role: 'user', content: answer })
      }

      try {
        const formData = new FormData()
        formData.append('file', this.file)
        formData.append('prompt', this.intent)
        if (this.clarificationHistory.length > 0) {
          formData.append('history', JSON.stringify(this.clarificationHistory))
        }

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

        // Push all new clarification questions to history as assistant messages
        const questions = this.ontology?.meta.clarification_questions ?? []
        if (questions.length > 0) {
          const combined = questions.join('\n\n')
          this.clarificationHistory.push({
            role: 'assistant',
            content: combined,
          })
        }

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
      this.showProgress = true
      this.progressCurrent = 0
      this.progressTotal = 0
      this.progressCurrentModel = 'Initializing...'
      this.progressCompleted = false

      console.log('[Forecast] Starting execution, showProgress:', this.showProgress)

      // Start SSE connection for progress updates
      const sessionId = this.ontology.session_id
      console.log('[Forecast] Session ID:', sessionId)
      if (sessionId) {
        this.connectProgressStream(sessionId)
      }

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
        this.tournamentResults = data.tournament_results ?? []
        this.backtestData = data.backtest_data ?? []

        // Hide progress and move directly to results
        this.showProgress = false
        this.step = 'results'
        appStore.notify('Modelling sequence complete.', 'success')
      } catch (error: any) {
        this.showProgress = false
        appStore.notify(error.message || 'Forecast failed', 'error')
      } finally {
        this.loading = false
      }
    },

    async initializeExplainability () {
      if (!this.ontology?.session_id) {
        return
      }

      const appStore = useAppStore()
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8002'

      try {
        const response = await fetch(`${apiUrl}/forecast/explain`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: this.ontology.session_id,
            question: '',
            history: [],
          }),
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to load explainability briefing')
        }

        const data: ExplainabilityResponse = await response.json()
        this.explainabilityMessages = [{
          role: 'assistant',
          content: data.answer,
          evidence: data.evidence,
          suggestions: data.suggestions,
        }]
        this.suggestedQuestions = data.suggestions ?? []
      } catch (error: any) {
        appStore.notify(error.message || 'Failed to load explainability briefing', 'warning')
        this.explainabilityMessages = [{
          role: 'assistant',
          content: this.explanation || 'Forecast completed. Ask a question about reliability, ontology, or model choice.',
        }]
      }
    },

    async askExplainability (question: string, useStreaming = true) {
      if (!this.ontology?.session_id || !question.trim() || this.askingExplainability) {
        return
      }

      const appStore = useAppStore()
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8002'
      this.askingExplainability = true

      const history = this.explainabilityMessages.map(m => ({ role: m.role, content: m.content }))
      this.explainabilityMessages.push({ role: 'user', content: question })

      try {
        if (useStreaming) {
          await this.askExplainabilityStream(question)
          return
        }

        const response = await fetch(`${apiUrl}/forecast/explain`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: this.ontology.session_id,
            question,
            history,
          }),
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to get explainability response')
        }

        const data: ExplainabilityResponse = await response.json()
        this.explainabilityMessages.push({
          role: 'assistant',
          content: data.answer,
          evidence: data.evidence,
          suggestions: data.suggestions,
        })
        this.suggestedQuestions = data.suggestions ?? this.suggestedQuestions
      } catch (error: any) {
        appStore.notify(error.message || 'Explainability request failed', 'error')
      } finally {
        this.askingExplainability = false
      }
    },

    async askExplainabilityStream (question: string) {
      if (!this.ontology?.session_id) {
        return
      }

      const appStore = useAppStore()
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8002'
      const assistantMsg: ExplainabilityMessage = { role: 'assistant', content: '' }
      this.explainabilityMessages.push(assistantMsg)
      const assistantIndex = this.explainabilityMessages.length - 1

      await new Promise<void>((resolve, reject) => {
        const url = `${apiUrl}/forecast/explain/stream/${this.ontology?.session_id}?question=${encodeURIComponent(question)}`
        const eventSource = new EventSource(url)

        eventSource.addEventListener('message', event => {
          try {
            const payload = JSON.parse(event.data)
            const assistantMessage = this.explainabilityMessages[assistantIndex]
            if (!assistantMessage) {
              return
            }
            switch (payload.type) {
              case 'chunk': {
                assistantMessage.content += payload.text
                break
              }
              case 'meta': {
                assistantMessage.evidence = payload.evidence ?? []
                assistantMessage.suggestions = payload.suggestions ?? []
                this.suggestedQuestions = payload.suggestions ?? this.suggestedQuestions
                break
              }
              case 'done': {
                eventSource.close()
                resolve()
                break
              }
            }
          } catch {
            eventSource.close()
            reject(new Error('Failed to parse streaming explainability response'))
          }
        })

        eventSource.addEventListener('error', () => {
          eventSource.close()
          reject(new Error('Explainability stream interrupted'))
        })
      }).catch((error: any) => {
        appStore.notify(error.message || 'Explainability stream failed', 'warning')
      }).finally(() => {
        this.askingExplainability = false
      })
    },

    connectProgressStream (sessionId: string) {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8002'
      const eventSource = new EventSource(`${apiUrl}/forecast/progress/${sessionId}`)

      console.log('[Progress] SSE connection started for session:', sessionId)

      eventSource.addEventListener('message', event => {
        try {
          const data = JSON.parse(event.data)
          console.log('[Progress] Received update:', data)
          this.progressCurrent = data.current
          this.progressTotal = data.total
          this.progressCurrentModel = data.model_name
          this.progressCompleted = data.completed

          if (data.completed) {
            console.log('[Progress] Completed, closing SSE connection')
            eventSource.close()
          }
        } catch (error) {
          console.error('[Progress] Error parsing progress data:', error)
        }
      })

      eventSource.addEventListener('error', error => {
        console.error('[Progress] SSE connection error:', error)
        eventSource.close()
      })

      // Store reference for cleanup
      ;(this as any)._progressEventSource = eventSource
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
      // Close any active SSE connection
      if ((this as any)._progressEventSource) {
        ;(this as any)._progressEventSource.close()
        ;(this as any)._progressEventSource = null
      }

      this.file = null
      this.intent = ''
      this.ontology = null
      this.cleaningReport = null
      this.forecastResults = []
      this.metrics = []
      this.explanation = ''
      this.dataHealthReport = null
      this.step = 'upload'
      this.modelMetadata = null
      this.tournamentResults = []
      this.backtestData = []
      this.showProgress = false
      this.progressCurrent = 0
      this.progressTotal = 0
      this.progressCurrentModel = ''
      this.progressCompleted = false
      this.explainabilityMessages = []
      this.askingExplainability = false
      this.suggestedQuestions = []
      this.clarificationHistory = []
    },
  },
})
