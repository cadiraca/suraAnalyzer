interface AnalysisProgressProps {
  progress: number;
  statusMessage: string;
  contractName?: string;
}

export function AnalysisProgress({
  progress,
  statusMessage,
  contractName,
}: AnalysisProgressProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="animate-spin">
            <svg
              className="w-6 h-6 text-primary-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">
              Análisis en Progreso
            </h3>
            {contractName && (
              <p className="text-sm text-gray-600">{contractName}</p>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-700 font-medium">{statusMessage}</span>
            <span className="text-primary-600 font-semibold">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-primary-600 h-full rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Info Message */}
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-3">
          <p className="text-sm text-primary-800">
            ⏳ El análisis puede tardar entre 30 segundos y 2 minutos dependiendo del número y tamaño de los archivos.
          </p>
        </div>
      </div>
    </div>
  );
}
