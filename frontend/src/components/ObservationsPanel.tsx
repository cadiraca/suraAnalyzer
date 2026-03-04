interface ObservationsPanelProps {
  observations: string;
  missingFields: string[];
}

export function ObservationsPanel({ observations, missingFields }: ObservationsPanelProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-4">
        <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="text-lg font-semibold text-gray-900">Observaciones del Análisis</h3>
      </div>

      <div className="mb-6">
        <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">{observations}</div>
      </div>

      {missingFields && missingFields.length > 0 && (
        <div className="border-t border-gray-200 pt-4">
          <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-warning-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-warning-900 mb-2">
                  Información Faltante o Documentos Adicionales Necesarios
                </h4>
                <ul className="space-y-1">
                  {missingFields.map((field, index) => (
                    <li key={index} className="text-sm text-warning-800 flex items-start gap-2">
                      <span className="text-warning-600 mt-1">•</span>
                      <span>{field}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="border-t border-gray-200 pt-4 mt-6">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-gray-900 mb-1">⚠️ Importante</h4>
              <p className="text-xs text-gray-700 leading-relaxed">
                Esta es una auditoría contractual automatizada realizada con inteligencia artificial.
                Los resultados deben ser revisados y validados por un profesional de la salud antes
                de tomar cualquier decisión clínica o administrativa. Este análisis es una herramienta
                de apoyo y no reemplaza el juicio profesional.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
