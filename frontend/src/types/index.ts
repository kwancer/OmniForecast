// --- ENUMS & LITERALS (Matching Python Enums) ---

export type ColumnRole = 'time_index' | 'target' | 'group_id' | 'covariate' | 'ignore'
export type DataType = 'continuous' | 'discrete' | 'binary' | 'categorical' | 'text' | 'datetime'
export type CovariateType = 'known_future' | 'unknown_past' | 'static' | 'controllable' | 'exogenous'
export type TimeUnit = 'second' | 'minute' | 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year'
export type CompletenessStatus = 'complete' | 'partial'
export type RiskPreference = 'balanced' | 'under_penalty' | 'over_penalty'

// --- SUB-OBJECTS ---

export interface MetaContext {
  user_intent_summary: string
  domain_inference: string // e.g., 'Financial', 'Retail'
  completeness_check: CompletenessStatus
  confidence_score?: number
  clarification_questions?: string[]
}

export interface Granularity {
  unit: TimeUnit
  is_regular: boolean
}

export interface ProblemDefinition {
  task_type: string
  granularity: Granularity
  confidence_score?: number
  confidence_rationale?: string
}

export interface FutureAvailability {
  status: 'known' | 'unknown' | 'static'
  action_required: 'prompt_user' | 'internal_forecast' | 'none'
}

export interface Constraints {
  min_value?: number | null
  max_value?: number | null
  allowed_classes?: string[]
  sparsity_ratio?: number | null // Critical for the DataXRay component
}

export interface ColumnOntology {
  column_name: string
  display_name: string
  role: ColumnRole
  data_type: DataType
  covariate_type?: CovariateType
  future_availability?: FutureAvailability
  constraints?: Constraints
  resampling_method?: 'mean' | 'sum' | 'last' | 'max' | 'none'
  date_format?: string | null // Python strftime format for parsing dates
  confidence_score?: number
  confidence_rationale?: string
}

export interface HorizonRequirement {
  steps: number
  flexibility: 'strict' | 'approximate'
  confidence_score?: number
  confidence_rationale?: string
}

export interface UserRequirements {
  primary_objective: string
  cost_function_preference: string
  horizon_requirement: HorizonRequirement
  output_format: string
}

export interface ModelMetadata {
  name: string
  description: string
  rationale: string
  educational_video_url?: string
}

// --- MAIN ONTOLOGY ---

export interface ForecastOntology {
  meta: MetaContext
  problem: ProblemDefinition
  columns: ColumnOntology[]
  requirements: UserRequirements
  model_metadata?: ModelMetadata
  session_id?: string
  sample_data?: Record<string, any>[]
  scenario_overrides?: Record<string, number | number[] | null>
  ignored_columns?: string[]
  // Risk Preference & Confidence Intervals
  risk_preference?: RiskPreference
  interval_width?: number
}

// --- RESULTS & REPORTING ---

export interface CleaningAction {
  column: string
  action: string
  description: string
}

export interface CleaningReport {
  actions: CleaningAction[]
  initial_shape: number[]
  final_shape: number[]
  summary: string
  cleaned_sample?: Record<string, any>[]
}

export interface ForecastResult {
  [key: string]: string | number | undefined
  date?: string
  mean?: number
  lower?: number
  upper?: number
}

export interface ForecastMetric {
  name: string
  value: number
}

export interface DataHealthReport {
  score: number
  rating: string
  explanation: string
  mse_naive?: number
  mse_winner?: number
  rmse_naive?: number
  rmse_winner?: number
  winner_name?: string
  winner_complexity?: number
}

export interface TournamentResult {
  model_name: string
  mae: number
  mse?: number
  rmse?: number
  complexity: number
  status: 'winner' | 'runner_up' | 'rejected'
  metrics: ForecastMetric[]
}

export interface BacktestPoint {
  date: string
  prediction: number
  actual: number
}

export interface ForecastResponse {
  forecast: ForecastResult[]
  explanation: string
  history: ForecastResult[]
  metrics: ForecastMetric[]
  cleaning_report: CleaningReport
  session_id?: string
  model_metadata?: ModelMetadata
  data_health_report?: DataHealthReport
  tournament_results?: TournamentResult[]
  backtest_data?: BacktestPoint[]
}

export interface ExplainabilityEvidence {
  source: string
  detail: string
}

export interface ExplainabilityMessage {
  role: 'assistant' | 'user'
  content: string
  evidence?: ExplainabilityEvidence[]
  suggestions?: string[]
}

export interface ExplainabilityResponse {
  answer: string
  evidence: ExplainabilityEvidence[]
  suggestions: string[]
  tool_trace?: Array<Record<string, any>>
}

// --- APP UTILS ---

export type NotificationType = 'success' | 'error' | 'info' | 'warning'

export interface AppNotification {
  id: string
  message: string
  type: NotificationType
  timeout?: number
}
