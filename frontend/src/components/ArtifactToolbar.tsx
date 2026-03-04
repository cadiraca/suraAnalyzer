import { useState } from 'react';
import type { ClinicalSummaryResponse } from '../lib/types';
import { getCategoryLabel } from '../lib/utils';

interface ArtifactToolbarProps {
  result: ClinicalSummaryResponse;
}

function generateMarkdown(result: ClinicalSummaryResponse): string {
  const lines: string[] = [];

  // Title
  const patientName = result.patient_overview.name || 'Paciente';
  lines.push(`# Resumen Clinico - ${patientName}`);
  lines.push('');

  // Patient info
  if (result.patient_overview.name || result.patient_overview.age || result.patient_overview.patient_id) {
    lines.push('## Datos del Paciente');
    lines.push('');
    if (result.patient_overview.name) lines.push(`- **Nombre:** ${result.patient_overview.name}`);
    if (result.patient_overview.age) lines.push(`- **Edad:** ${result.patient_overview.age} anos`);
    if (result.patient_overview.patient_id) lines.push(`- **ID:** ${result.patient_overview.patient_id}`);
    if (result.patient_overview.primary_conditions.length > 0) {
      lines.push(`- **Condiciones principales:** ${result.patient_overview.primary_conditions.join(', ')}`);
    }
    lines.push('');
  }

  // Focus summary
  if (result.focus_summary) {
    lines.push('## Resumen Enfocado');
    lines.push('');
    lines.push(result.focus_summary);
    lines.push('');
  }

  // Timeline
  lines.push('## Linea de Tiempo');
  lines.push('');

  for (const event of result.timeline) {
    const dateLabel = event.date_precision === 'unknown' ? 'Fecha desconocida' : event.date;
    const precisionNote = event.date_precision === 'approximate' ? ' (aprox.)' : '';
    lines.push(`### ${dateLabel}${precisionNote} - ${event.title}`);
    lines.push('');
    lines.push(`**Categoria:** ${getCategoryLabel(event.category)}`);
    lines.push('');
    lines.push(event.description);
    lines.push('');
    if (event.relevant_details && event.relevant_details.length > 0) {
      lines.push('**Detalles:**');
      for (const detail of event.relevant_details) {
        lines.push(`- ${detail}`);
      }
      lines.push('');
    }
    lines.push(`*Fuente: ${event.source_document}*`);
    lines.push('');
    lines.push('---');
    lines.push('');
  }

  // General observations
  lines.push('## Observaciones Generales');
  lines.push('');
  lines.push(result.general_observations);
  lines.push('');

  // Metadata
  lines.push('---');
  lines.push('');
  lines.push(`*Documentos analizados: ${result.documents_analyzed} | Confianza: ${Math.round(result.confidence_score * 100)}% | Idioma: ${result.document_language}*`);

  return lines.join('\n');
}

export function ArtifactToolbar({ result }: ArtifactToolbarProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyMarkdown = async () => {
    const markdown = generateMarkdown(result);
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy markdown:', err);
    }
  };

  const handleExportPDF = () => {
    // Use the browser's print dialog as a simple PDF export
    // This captures the artifact panel content
    window.print();
  };

  return (
    <div className="flex items-center gap-2">
      {/* Copy Markdown */}
      <button
        onClick={handleCopyMarkdown}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
        title="Copiar como Markdown"
      >
        {copied ? (
          <>
            <svg className="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-green-600">Copiado</span>
          </>
        ) : (
          <>
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
            </svg>
            <span>Copiar MD</span>
          </>
        )}
      </button>

      {/* Export PDF */}
      <button
        onClick={handleExportPDF}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
        title="Exportar como PDF"
      >
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span>PDF</span>
      </button>
    </div>
  );
}
