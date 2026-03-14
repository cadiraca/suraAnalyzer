import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import type { FileRejection } from 'react-dropzone';

interface FileUploaderProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  disabled?: boolean;
}

export function FileUploader({ files, onFilesChange, disabled }: FileUploaderProps) {
  const [oversizedFiles, setOversizedFiles] = useState<string[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFilesChange([...files, ...acceptedFiles]);
    },
    [files, onFilesChange]
  );

  const onDropRejected = useCallback((rejections: FileRejection[]) => {
    const names = rejections
      .filter((r) => r.errors.some((e) => e.code === 'file-too-large'))
      .map((r) => r.file.name);
    if (names.length > 0) {
      setOversizedFiles((prev) => [...prev, ...names.filter((n) => !prev.includes(n))]);
    }
  }, []);

  const dismissOversized = (name: string) => {
    setOversizedFiles((prev) => prev.filter((n) => n !== name));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled,
  });

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    onFilesChange(newFiles);
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2">
          <svg
            className="w-12 h-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <div className="text-sm text-gray-600">
            {isDragActive ? (
              <p className="font-semibold text-primary-600">Suelta los archivos aquí...</p>
            ) : (
              <>
                <p className="font-semibold">Arrastra archivos aquí o haz clic para seleccionar</p>
                <p className="text-xs mt-1">PDF, PNG, JPG (máx. 10MB cada uno)</p>
              </>
            )}
          </div>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-700">
            Archivos seleccionados ({files.length})
          </h3>
          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-gray-50 p-3 rounded-lg border border-gray-200"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <svg
                    className="w-5 h-5 text-gray-500 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  disabled={disabled}
                  className="ml-2 text-danger-600 hover:text-danger-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Eliminar archivo"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {oversizedFiles.length > 0 && (
        <div className="space-y-2">
          {oversizedFiles.map((name) => (
            <div
              key={name}
              className="flex items-start justify-between gap-2 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800"
            >
              <span>
                ⚠️ El archivo <strong className="font-semibold">{name}</strong> supera el límite de
                10&nbsp;MB. Usa la pestaña{' '}
                <strong className="font-semibold">Herramientas PDF</strong> para reducir su tamaño
                antes de cargarlo.
              </span>
              <button
                type="button"
                onClick={() => dismissOversized(name)}
                className="flex-shrink-0 text-amber-600 hover:text-amber-800 font-bold leading-none"
                title="Cerrar"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
