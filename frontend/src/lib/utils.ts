import type { EligibilityDecision, CriterionStatus, TimelineCategory, DatePrecision } from './types';

// Decision color mapping
export function getDecisionColor(decision: EligibilityDecision) {
  switch (decision) {
    case 'ELIGIBLE':
      return {
        bg: 'bg-success-50',
        border: 'border-success-600',
        text: 'text-success-700',
      };
    case 'NOT_ELIGIBLE':
      return {
        bg: 'bg-danger-50',
        border: 'border-danger-600',
        text: 'text-danger-700',
      };
    case 'INSUFFICIENT_INFORMATION':
      return {
        bg: 'bg-warning-50',
        border: 'border-warning-600',
        text: 'text-warning-700',
      };
  }
}

// Decision label mapping
export function getDecisionLabel(decision: EligibilityDecision): string {
  switch (decision) {
    case 'ELIGIBLE':
      return 'ELEGIBLE';
    case 'NOT_ELIGIBLE':
      return 'NO ELEGIBLE';
    case 'INSUFFICIENT_INFORMATION':
      return 'INFORMACIÓN INSUFICIENTE';
  }
}

// Status color mapping
export function getStatusColor(status: CriterionStatus): string {
  switch (status) {
    case 'COMPLIANT':
      return 'bg-success-100 text-success-800';
    case 'NON_COMPLIANT':
      return 'bg-danger-100 text-danger-800';
    case 'UNKNOWN':
      return 'bg-warning-100 text-warning-800';
  }
}

// Format confidence score
export function formatConfidence(score: number): string {
  return `${Math.round(score * 100)}%`;
}

// Class name utility (similar to clsx)
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

// ============================================
// Clinical Summarizer Utilities
// ============================================

// Category color mapping for timeline events
export function getCategoryColor(category: TimelineCategory): {
  bg: string;
  border: string;
  text: string;
  dot: string;
} {
  switch (category) {
    case 'diagnosis':
      return { bg: 'bg-blue-50', border: 'border-blue-400', text: 'text-blue-700', dot: 'bg-blue-500' };
    case 'procedure':
      return { bg: 'bg-green-50', border: 'border-green-400', text: 'text-green-700', dot: 'bg-green-500' };
    case 'medication':
      return { bg: 'bg-orange-50', border: 'border-orange-400', text: 'text-orange-700', dot: 'bg-orange-500' };
    case 'examination':
      return { bg: 'bg-purple-50', border: 'border-purple-400', text: 'text-purple-700', dot: 'bg-purple-500' };
    case 'lab_result':
      return { bg: 'bg-teal-50', border: 'border-teal-400', text: 'text-teal-700', dot: 'bg-teal-500' };
    case 'hospitalization':
      return { bg: 'bg-red-50', border: 'border-red-400', text: 'text-red-700', dot: 'bg-red-500' };
    case 'other':
      return { bg: 'bg-gray-50', border: 'border-gray-400', text: 'text-gray-700', dot: 'bg-gray-500' };
  }
}

// Category label mapping
export function getCategoryLabel(category: TimelineCategory): string {
  switch (category) {
    case 'diagnosis': return 'Diagnostico';
    case 'procedure': return 'Procedimiento';
    case 'medication': return 'Medicamento';
    case 'examination': return 'Examen';
    case 'lab_result': return 'Resultado Lab';
    case 'hospitalization': return 'Hospitalizacion';
    case 'other': return 'Otro';
  }
}

// Date precision styling
export function getDatePrecisionStyle(precision: DatePrecision): string {
  switch (precision) {
    case 'exact': return 'border-solid font-semibold';
    case 'approximate': return 'border-dashed';
    case 'unknown': return 'border-dotted text-gray-400';
  }
}
