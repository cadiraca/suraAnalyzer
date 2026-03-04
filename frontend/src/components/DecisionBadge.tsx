import type { EligibilityDecision } from '../lib/types';
import { getDecisionColor, getDecisionLabel, formatConfidence } from '../lib/utils';

interface DecisionBadgeProps {
  decision: EligibilityDecision;
  confidenceScore: number;
}

export function DecisionBadge({ decision, confidenceScore }: DecisionBadgeProps) {
  const colors = getDecisionColor(decision);
  const label = getDecisionLabel(decision);

  const getIcon = () => {
    switch (decision) {
      case 'ELIGIBLE':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
      case 'NOT_ELIGIBLE':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
      case 'INSUFFICIENT_INFORMATION':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        );
    }
  };

  return (
    <div className={`${colors.bg} ${colors.border} border-2 rounded-lg p-6 shadow-sm`}>
      <div className="flex items-center gap-4">
        <div className={colors.text}>{getIcon()}</div>
        <div className="flex-1">
          <h2 className={`text-2xl font-bold ${colors.text} mb-1`}>{label}</h2>
          <p className="text-sm text-gray-600">
            Nivel de confianza: <span className="font-semibold">{formatConfidence(confidenceScore)}</span>
          </p>
        </div>
      </div>

      {decision === 'INSUFFICIENT_INFORMATION' && (
        <div className="mt-4 pt-4 border-t border-warning-200">
          <p className="text-sm text-warning-800">
            Se requiere información adicional para completar el análisis de elegibilidad.
            Revisa la sección de campos faltantes más abajo.
          </p>
        </div>
      )}

      {decision === 'ELIGIBLE' && (
        <div className="mt-4 pt-4 border-t border-success-200">
          <p className="text-sm text-success-800">
            ✓ El paciente cumple con todos los criterios de elegibilidad para el servicio.
          </p>
        </div>
      )}

      {decision === 'NOT_ELIGIBLE' && (
        <div className="mt-4 pt-4 border-t border-danger-200">
          <p className="text-sm text-danger-800">
            ✗ El paciente no cumple con uno o más criterios de elegibilidad. Revisa la matriz de criterios para más detalles.
          </p>
        </div>
      )}
    </div>
  );
}
