export interface ColumnOntology {
  column_name: string;
  role: 'time_index' | 'target' | 'feature' | 'metadata' | 'group_id' | 'covariate' | 'ignore';
  data_type: 'datetime' | 'numeric' | 'categorical' | 'string' | 'continuous' | 'discrete' | 'binary' | 'text';
}

export interface ModelMetadata {
  name: string;
  description: string;
  rationale: string;
  educational_video_url?: string;
}

export interface UserIntentOntology {
  columns: ColumnOntology[];
  meta: any;
  problem: any;
  requirements: any;
  session_id?: string;
}

export interface SystemAnalysis {
  is_daily: boolean;
  seasonality_mode: string;
  regressors: string[];
}

export interface ForecastOntology {
  intent: UserIntentOntology;
  analysis: SystemAnalysis;
  model_metadata?: ModelMetadata;
  session_id?: string;
}

export interface CleaningAction {
  column: string;
  action: string;
  description: string;
}

export interface CleaningReport {
  actions: CleaningAction[];
  initial_shape: number[];
  final_shape: number[];
  summary: string;
}

export interface ForecastResult {
  [key: string]: string | number;
}

export interface ForecastMetric {
  name: string;
  value: number;
}

export interface ForecastResponse {
  forecast: ForecastResult[];
  explanation: string;
  metrics: ForecastMetric[];
  cleaning_report: CleaningReport;
  cleaned_data?: ForecastResult[];
  session_id?: string;
}

export type NotificationType = 'success' | 'error' | 'info' | 'warning';

export interface AppNotification {
  id: string;
  message: string;
  type: NotificationType;
  timeout?: number;
}
