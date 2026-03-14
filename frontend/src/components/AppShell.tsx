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
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-primary-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4 md:py-6">
          <div className="flex items-center gap-4 flex-wrap">
            <img
              src="/image.png"
              alt="SURA Logo"
              className="h-12 w-auto object-contain"
            />
            <div>
              <h1 className="text-3xl font-bold">SURA Analyzer</h1>
              <p className="text-primary-100 mt-1">Plataforma de Analisis Documental con IA</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="container mx-auto px-4">
          <nav className="flex gap-1 overflow-x-auto pb-0" role="tablist">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                role="tab"
                aria-selected={activeModule === tab.key}
                onClick={() => setActiveModule(tab.key)}
                className={cn(
                  'px-5 py-3 text-sm font-semibold transition-colors whitespace-nowrap border-b-2',
                  activeModule === tab.key
                    ? 'text-white border-white'
                    : 'text-primary-200 border-transparent hover:text-white hover:border-primary-400'
                )}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-6xl flex-1">
        {activeModule === 'eligibility' && <EligibilityAnalyzer />}
        {activeModule === 'summarizer' && <ClinicalSummarizer />}
        {activeModule === 'pdf-tools' && <PdfTools />}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="container mx-auto px-4 py-4 text-center text-gray-600 text-sm">
          <p>SURA Analyzer</p>
          <p className="mt-1 text-gray-500">Disenado por Mariana Manzano Trujillo</p>
        </div>
      </footer>
    </div>
  );
}
