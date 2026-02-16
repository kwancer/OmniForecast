// --- ENUMS & LITERALS (Matching Python Enums) ---

export type ColumnRole = 'time_index' | 'target' | 'group_id' | 'covariate' | 'ignore'
export type DataType = 'continuous' | 'discrete' | 'binary' | 'categorical' | 'text' | 'datetime'
export type CovariateType = 'controllable' | 'exogenous' | 'static'
export type TimeUnit = 'second' | 'minute' | 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year'
export type CompletenessStatus = 'complete' | 'partial'
export type RiskPreference = 'balanced' | 'under_penalty' | 'over_penalty'

// --- SUB-OBJECTS ---

export interface MetaContext {
  user_intent_summary: string
  domain_inference: string // e.g., 'Financial', 'Retail'
  completeness_check: CompletenessStatus
}

export interface Granularity {
  unit: TimeUnit
  is_regular: boolean
}

export interface ProblemDefinition {
  task_type: string
  granularity: Granularity
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
}

export interface HorizonRequirement {
  steps: number
  flexibility: 'strict' | 'approximate'
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
  hyndman_score?: number
  forecasting_gain_pct?: number
  trend_strength?: number
  seasonality_strength?: number
  decomposition_type?: string
  winner_name?: string
  winner_complexity?: number
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
}

// --- APP UTILS ---

export type NotificationType = 'success' | 'error' | 'info' | 'warning'

export interface AppNotification {
  id: string
  message: string
  type: NotificationType
  timeout?: number
}
