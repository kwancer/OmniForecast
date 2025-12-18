export interface ColumnOntology {
  column_name: string;
  role: 'time_index' | 'target' | 'feature' | 'metadata';
  data_type: 'datetime' | 'numeric' | 'categorical' | 'string';
}

export interface ForecastOntology {
  columns: ColumnOntology[];
  frequency: string;
}

export interface ForecastResult {
  [key: string]: string | number;
}

export interface ForecastResponse {
  forecast: ForecastResult[];
  explanation: string;
}

export type NotificationType = 'success' | 'error' | 'info' | 'warning';

export interface AppNotification {
  id: string;
  message: string;
  type: NotificationType;
  timeout?: number;
}
