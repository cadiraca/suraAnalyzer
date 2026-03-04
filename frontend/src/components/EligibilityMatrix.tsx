import { useState } from 'react';
import type { CriterionEvaluation } from '../lib/types';
import { getStatusColor } from '../lib/utils';

interface EligibilityMatrixProps {
  criteriaMatrix: CriterionEvaluation[];
}

export function EligibilityMatrix({ criteriaMatrix }: EligibilityMatrixProps) {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-4">
        <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
          />
        </svg>
        <h3 className="text-lg font-semibold text-gray-900">Matriz de Criterios de Elegibilidad</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Criterio</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Requisito</th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Valor del Paciente</th>
              <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">Estado</th>
              <th className="w-12"></th>
            </tr>
          </thead>
          <tbody>
            {criteriaMatrix.map((criterion, index) => (
              <>
                <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <p className="font-medium text-gray-900">{criterion.criterion}</p>
                  </td>
                  <td className="py-3 px-4">
                    <p className="text-sm text-gray-700">{criterion.requirement}</p>
                  </td>
                  <td className="py-3 px-4">
                    <p className="text-sm text-gray-900">{criterion.patient_value}</p>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex justify-center">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(criterion.status)}`}>
                        {criterion.status}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => toggleRow(index)}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                      title={expandedRows.has(index) ? 'Ocultar justificación' : 'Ver justificación'}
                    >
                      <svg
                        className={`w-5 h-5 transition-transform ${expandedRows.has(index) ? 'transform rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                  </td>
                </tr>
                {expandedRows.has(index) && (
                  <tr key={`${index}-expanded`} className="border-b border-gray-100 bg-gray-50">
                    <td colSpan={5} className="py-3 px-4">
                      <div className="border-l-4 border-primary-500 pl-4">
                        <p className="text-sm font-medium text-gray-700 mb-1">Justificación:</p>
                        <p className="text-sm text-gray-600">{criterion.justification}</p>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {criteriaMatrix.length === 0 && (
        <div className="text-center py-8 text-gray-500">No hay criterios para mostrar</div>
      )}
    </div>
  );
}
