interface FocusPromptProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function FocusPrompt({ value, onChange, disabled }: FocusPromptProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <label
        htmlFor="focus-prompt"
        className="block text-sm font-semibold text-gray-700 mb-2"
      >
        Enfoque del resumen (opcional)
      </label>
      <p className="text-xs text-gray-500 mb-3">
        Indica si hay algo especifico en lo que el resumen deba enfocarse.
        Si lo dejas vacio, se generara un resumen cronologico general.
      </p>
      <textarea
        id="focus-prompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="Ej: medicamentos recetados, procedimientos quirurgicos, resultados de laboratorio..."
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
          disabled:opacity-50 disabled:cursor-not-allowed
          resize-none"
        rows={3}
      />
    </div>
  );
}
