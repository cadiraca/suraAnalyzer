import { useState } from 'react';
import { FileUploader } from './FileUploader';
import { FocusPrompt } from './FocusPrompt';
import { AnalysisProgress } from './AnalysisProgress';
import { SummaryArtifact } from './SummaryArtifact';
import { summarizeClinical } from '../lib/api';
import type { ClinicalSummaryResponse } from '../lib/types';

export function ClinicalSummarizer() {
  const [files, setFiles] = useState<File[]>([]);
  const [focus, setFocus] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [result, setResult] = useState<ClinicalSummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSummarize = () => {
    if (files.length === 0) {
      alert('Por favor selecciona al menos un archivo');
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setStatusMessage('Iniciando resumen...');
    setResult(null);
    setError(null);

    summarizeClinical(files, focus || undefined, {
      onInit: (data) => {
        setStatusMessage(data.message);
        setProgress(10);
      },
      onAnalyzing: (data) => {
        setStatusMessage(data.message);
        setProgress(data.progress);
      },
      onResult: (data) => {
        setResult(data);
        setProgress(100);
        setStatusMessage('Resumen completado');
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
    setFocus('');
    setResult(null);
    setError(null);
    setProgress(0);
    setStatusMessage('');
  };

  return (
    <div className="space-y-6">
      {/* Control Bar */}
      {!result && (
        <>
          {/* File Uploader */}
          <div className="space-y-2">
            <FileUploader files={files} onFilesChange={setFiles} disabled={isAnalyzing} />
            {files.length > 0 && !isAnalyzing && (
              <p className="text-sm text-gray-600 px-1">
                {files.length} archivo{files.length !== 1 ? 's' : ''} seleccionado{files.length !== 1 ? 's' : ''}
              </p>
            )}
          </div>

          {/* Focus Prompt */}
          {files.length > 0 && !isAnalyzing && (
            <FocusPrompt value={focus} onChange={setFocus} disabled={isAnalyzing} />
          )}

          {/* Action Buttons */}
          {files.length > 0 && !isAnalyzing && (
            <div className="flex gap-3">
              <button
                onClick={handleSummarize}
                disabled={isAnalyzing || files.length === 0}
                className="px-6 py-2.5 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
              >
                Generar Resumen
              </button>
            </div>
          )}
        </>
      )}

      {/* Progress */}
      {isAnalyzing && (
        <AnalysisProgress
          progress={progress}
          statusMessage={statusMessage}
        />
      )}

      {/* Error */}
      {error && (
        <div className="bg-danger-50 border border-danger-200 rounded-lg p-4">
          <p className="text-danger-800 font-semibold">Error: {error}</p>
        </div>
      )}

      {/* Results - Artifact Style */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Resumen Clinico</h2>
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-gray-600 text-white text-sm font-semibold rounded-lg hover:bg-gray-700 transition-colors shadow-sm"
            >
              Nuevo Resumen
            </button>
          </div>
          <SummaryArtifact result={result} />
        </div>
      )}
    </div>
  );
}
