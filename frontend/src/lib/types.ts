// Contract Types
export interface Contract {
  contract_id: string;
  contract_name: string;
  description: string;
  version: string;
  active: boolean;
  default?: boolean;
}

export interface ContractsResponse {
  contracts: Contract[];
  total: number;
}

// Patient Data
export interface PatientData {
  name: string;
  age: number;
  patient_id: string;
  insurance_plan: string;
  has_poliza?: boolean;
}

// Criterion Evaluation
export type CriterionStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'UNKNOWN';

export interface CriterionEvaluation {
  criterion: string;
  requirement: string;
  patient_value: string;
  status: CriterionStatus;
  justification: string;
}

// Eligibility Decision
export type EligibilityDecision = 'ELIGIBLE' | 'NOT_ELIGIBLE' | 'INSUFFICIENT_INFORMATION';

// Analysis Response
export interface AnalysisResponse {
  patient_data: PatientData;
  eligibility_decision: EligibilityDecision;
  criteria_matrix: CriterionEvaluation[];
  observations: string;
  confidence_score: number;
  missing_fields: string[];
}

// SSE Event Types
export interface SSEInitEvent {
  contract_id: string;
  contract_name: string;
}

export interface SSEAnalyzingEvent {
  message: string;
  progress: number;
}

export interface SSEResultEvent extends AnalysisResponse {}

export interface SSEErrorEvent {
  error: string;
  details?: string;
}

// ============================================
// Clinical Summarizer Types
// ============================================

export type TimelineCategory =
  | 'diagnosis'
  | 'procedure'
  | 'medication'
  | 'examination'
  | 'lab_result'
  | 'hospitalization'
  | 'other';

export type DatePrecision = 'exact' | 'approximate' | 'unknown';

export interface TimelineEvent {
  date: string;
  date_precision: DatePrecision;
  title: string;
  category: TimelineCategory;
  description: string;
  source_document: string;
  relevant_details?: string[];
}

export interface PatientOverview {
  name?: string;
  age?: number;
  patient_id?: string;
  primary_conditions: string[];
}

export interface ClinicalSummaryResponse {
  patient_overview: PatientOverview;
  timeline: TimelineEvent[];
  focus_summary?: string;
  general_observations: string;
  document_language: string;
  documents_analyzed: number;
  confidence_score: number;
}

export interface SummarizerSSEInitEvent {
  message: string;
  files_count: number;
}
