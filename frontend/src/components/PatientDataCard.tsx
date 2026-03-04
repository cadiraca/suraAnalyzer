import type { PatientData } from '../lib/types';

interface PatientDataCardProps {
  patientData: PatientData;
}

export function PatientDataCard({ patientData }: PatientDataCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-4">
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
            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
          />
        </svg>
        <h3 className="text-lg font-semibold text-gray-900">Datos del Paciente</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-500 uppercase mb-1">Nombre Completo</p>
          <p className="text-base font-semibold text-gray-900">{patientData.name}</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-500 uppercase mb-1">Edad</p>
          <p className="text-base font-semibold text-gray-900">{patientData.age} años</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-500 uppercase mb-1">Número de Identificación</p>
          <p className="text-base font-semibold text-gray-900">{patientData.patient_id}</p>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-xs font-medium text-gray-500 uppercase mb-1">Plan de Salud</p>
          <p className="text-base font-semibold text-gray-900">{patientData.insurance_plan}</p>
        </div>

        {patientData.has_poliza !== undefined && (
          <div className="bg-gray-50 rounded-lg p-4 md:col-span-2">
            <p className="text-xs font-medium text-gray-500 uppercase mb-1">Póliza Sura Activa</p>
            <div className="flex items-center gap-2">
              {patientData.has_poliza ? (
                <>
                  <svg className="w-5 h-5 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-base font-semibold text-success-700">Sí</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  <span className="text-base font-semibold text-gray-700">No</span>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
