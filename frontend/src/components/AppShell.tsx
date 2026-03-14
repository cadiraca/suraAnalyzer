import { useState } from 'react';
import { EligibilityAnalyzer } from './EligibilityAnalyzer';
import { ClinicalSummarizer } from './ClinicalSummarizer';
import { PdfTools } from './PdfTools';
import { cn } from '../lib/utils';

type ActiveModule = 'eligibility' | 'summarizer' | 'pdf-tools';

export function AppShell() {
  const [activeModule, setActiveModule] = useState<ActiveModule>('eligibility');

  const tabs: { key: ActiveModule; label: string; description: string }[] = [
    {
      key: 'eligibility',
      label: 'Elegibilidad',
      description: 'Auditoria contractual automatizada',
    },
    {
      key: 'summarizer',
      label: 'Resumen Clinico',
      description: 'Resumen cronologico de documentos',
    },
    {
      key: 'pdf-tools',
      label: 'Herramientas PDF',
      description: 'Comprimir y dividir archivos PDF',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-primary-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-4">
            <img
              src="/image.png"
              alt="SURA Logo"
              className="h-12 w-auto"
            />
            <div>
              <h1 className="text-3xl font-bold">SURA Analyzer</h1>
              <p className="text-primary-100 mt-1">Plataforma de Analisis Documental con IA</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="container mx-auto px-4">
          <nav className="flex gap-1" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                role="tab"
                aria-selected={activeModule === tab.key}
                onClick={() => setActiveModule(tab.key)}
                className={cn(
                  'px-5 py-3 text-sm font-semibold rounded-t-lg transition-colors',
                  activeModule === tab.key
                    ? 'bg-gray-50 text-primary-700'
                    : 'text-primary-100 hover:text-white hover:bg-primary-500'
                )}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {activeModule === 'eligibility' && <EligibilityAnalyzer />}
        {activeModule === 'summarizer' && <ClinicalSummarizer />}
        {activeModule === 'pdf-tools' && <PdfTools />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-gray-600 text-sm">
          <p>SURA Analyzer</p>
          <p className="mt-1 text-gray-500">Disenado por Mariana Manzano Trujillo</p>
        </div>
      </footer>
    </div>
  );
}
