import type { ClinicalSummaryResponse } from '../lib/types';
import { PatientOverviewCard } from './PatientOverviewCard';
import { TimelineView } from './TimelineView';
import { ArtifactToolbar } from './ArtifactToolbar';
import { formatConfidence } from '../lib/utils';

interface SummaryArtifactProps {
  result: ClinicalSummaryResponse;
}

export function SummaryArtifact({ result }: SummaryArtifactProps) {
  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden print:shadow-none print:border-none">
      {/* Artifact Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-4 print:bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Document icon */}
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">Resumen Clinico</h3>
              <p className="text-xs text-gray-500">
                {result.documents_analyzed} documento{result.documents_analyzed !== 1 ? 's' : ''} analizado{result.documents_analyzed !== 1 ? 's' : ''}
                {' · '}
                Confianza: {formatConfidence(result.confidence_score)}
                {' · '}
                Idioma: {result.document_language.toUpperCase()}
              </p>
            </div>
          </div>
          <div className="print:hidden">
            <ArtifactToolbar result={result} />
          </div>
        </div>
      </div>

      {/* Artifact Content */}
      <div className="px-6 py-5 max-h-[70vh] overflow-y-auto print:max-h-none print:overflow-visible">
        {/* Patient Overview */}
        <div className="mb-6">
          <PatientOverviewCard overview={result.patient_overview} />
        </div>

        {/* Focus Summary - highlighted if present */}
        {result.focus_summary && (
          <div className="mb-6 bg-primary-50 border border-primary-200 rounded-lg p-4">
            <h4 className="text-sm font-bold text-primary-800 mb-2">Resumen Enfocado</h4>
            <p className="text-sm text-primary-700 leading-relaxed whitespace-pre-line">
              {result.focus_summary}
            </p>
          </div>
        )}

        {/* Timeline */}
        <div className="mb-6">
          <h4 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Linea de Tiempo Cronologica
          </h4>
          <TimelineView events={result.timeline} />
        </div>

        {/* General Observations */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-bold text-gray-700 mb-2">Observaciones Generales</h4>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
            {result.general_observations}
          </p>
        </div>

        {/* Disclaimer */}
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-400 italic text-center">
            Este resumen fue generado automaticamente mediante inteligencia artificial.
            Debe ser revisado por un profesional de salud antes de tomar decisiones clinicas.
          </p>
        </div>
      </div>
    </div>
  );
}
