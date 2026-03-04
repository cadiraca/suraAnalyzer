import { useState } from 'react';
import { ContractSelector } from './ContractSelector';
import { FileUploader } from './FileUploader';
import { AnalysisProgress } from './AnalysisProgress';
import { DecisionBadge } from './DecisionBadge';
import { PatientDataCard } from './PatientDataCard';
import { EligibilityMatrix } from './EligibilityMatrix';
import { ObservationsPanel } from './ObservationsPanel';
import { analyzeEligibility } from '../lib/api';
import type { AnalysisResponse } from '../lib/types';

export function EligibilityAnalyzer() {
  const [contractId, setContractId] = useState<string | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = () => {
    if (files.length === 0) {
      alert('Por favor selecciona al menos un archivo');
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setStatusMessage('Iniciando analisis...');
    setResult(null);
    setError(null);

    analyzeEligibility(files, contractId, {
      onInit: (data) => {
        setStatusMessage(`Analizando con contrato: ${data.contract_name}`);
        setProgress(10);
      },
      onAnalyzing: (data) => {
        setStatusMessage(data.message);
        setProgress(data.progress);
      },
      onResult: (data) => {
        setResult(data);
        setProgress(100);
        setStatusMessage('Analisis completado');
      },
      onComplete: () => {
        setIsAnalyzing(false);
      },
      onError: (data) => {
        setError(data.error);
        setIsAnalyzing(false);
      },
    });
  };

  const handleReset = () => {
    setFiles([]);
    setResult(null);
    setError(null);
    setProgress(0);
    setStatusMessage('');
  };

  return (
    <div className="space-y-6">
      {/* Compact Control Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <ContractSelector
              selectedContractId={contractId}
              onContractChange={setContractId}
              disabled={isAnalyzing}
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing || files.length === 0}
            className="px-6 py-2.5 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap shadow-sm"
          >
            {isAnalyzing ? 'Analizando...' : 'Analizar'}
          </button>
          {result && (
            <button
              onClick={handleReset}
              className="px-6 py-2.5 bg-gray-600 text-white font-semibold rounded-lg hover:bg-gray-700 transition-colors whitespace-nowrap shadow-sm"
            >
              Nuevo Analisis
            </button>
          )}
        </div>
      </div>

      {/* File Uploader */}
      <div className="space-y-2">
        <FileUploader files={files} onFilesChange={setFiles} disabled={isAnalyzing} />
        {files.length > 0 && !isAnalyzing && (
          <p className="text-sm text-gray-600 px-1">
            {files.length} archivo{files.length !== 1 ? 's' : ''} seleccionado{files.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      {/* Progress */}
      {isAnalyzing && (
        <AnalysisProgress
          progress={progress}
          statusMessage={statusMessage}
          contractName={contractId || undefined}
        />
      )}

      {/* Error */}
      {error && (
        <div className="bg-danger-50 border border-danger-200 rounded-lg p-4">
          <p className="text-danger-800 font-semibold">Error: {error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          <DecisionBadge
            decision={result.eligibility_decision}
            confidenceScore={result.confidence_score}
          />
          <PatientDataCard patientData={result.patient_data} />
          <EligibilityMatrix criteriaMatrix={result.criteria_matrix} />
          <ObservationsPanel
            observations={result.observations}
            missingFields={result.missing_fields}
          />
        </div>
      )}
    </div>
  );
}
