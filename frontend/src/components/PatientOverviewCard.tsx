import type { PatientOverview } from '../lib/types';

interface PatientOverviewCardProps {
  overview: PatientOverview;
}

export function PatientOverviewCard({ overview }: PatientOverviewCardProps) {
  const hasInfo = overview.name || overview.age || overview.patient_id;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="text-sm font-bold text-gray-700 mb-3">Datos del Paciente</h3>

      {hasInfo ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          {overview.name && (
            <div>
              <p className="text-xs text-gray-500">Nombre</p>
              <p className="text-sm font-medium text-gray-900">{overview.name}</p>
            </div>
          )}
          {overview.age != null && (
            <div>
              <p className="text-xs text-gray-500">Edad</p>
              <p className="text-sm font-medium text-gray-900">{overview.age} anos</p>
            </div>
          )}
          {overview.patient_id && (
            <div>
              <p className="text-xs text-gray-500">Identificacion</p>
              <p className="text-sm font-medium text-gray-900">{overview.patient_id}</p>
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-gray-400 mb-3">
          No se encontraron datos del paciente en los documentos.
        </p>
      )}

      {overview.primary_conditions.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-1.5">Condiciones principales</p>
          <div className="flex flex-wrap gap-1.5">
            {overview.primary_conditions.map((condition, idx) => (
              <span
                key={idx}
                className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full"
              >
                {condition}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
