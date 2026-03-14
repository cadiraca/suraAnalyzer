import { useCallback, useRef, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { compressPdf, splitPdf } from '../lib/api';
import { cn } from '../lib/utils';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type QualityOption = { label: string; value: number };

const QUALITY_OPTIONS: QualityOption[] = [
  { label: 'Baja (máxima compresión)', value: 40 },
  { label: 'Media (recomendada)', value: 72 },
  { label: 'Alta (mejor calidad)', value: 85 },
];

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

// ---------------------------------------------------------------------------
// Shared dropzone section
// ---------------------------------------------------------------------------

interface PdfDropzoneProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
  id: string;
}

function PdfDropzone({ file, onFileChange, disabled, id }: PdfDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFileChange(accepted[0]);
    },
    [onFileChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    disabled,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        id={id}
        className={cn(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400',
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-2">
          {/* PDF icon */}
          <svg
            className="w-10 h-10 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
            />
          </svg>
          {isDragActive ? (
            <p className="text-sm font-semibold text-primary-600">Suelta el PDF aquí…</p>
          ) : file ? (
            <div className="text-sm text-gray-700">
              <p className="font-semibold truncate max-w-xs">{file.name}</p>
              <p className="text-gray-500">{formatBytes(file.size)}</p>
            </div>
          ) : (
            <div className="text-sm text-gray-600">
              <p className="font-semibold">Arrastra un PDF aquí o haz clic para seleccionar</p>
              <p className="text-xs mt-1 text-gray-500">Solo archivos PDF · Sin límite de tamaño</p>
            </div>
          )}
        </div>
      </div>

      {file && (
        <button
          type="button"
          onClick={() => onFileChange(null)}
          disabled={disabled}
          className="mt-2 text-xs text-danger-600 hover:text-danger-700 disabled:opacity-50"
        >
          × Quitar archivo
        </button>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Spinner
// ---------------------------------------------------------------------------

function Spinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-white"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// CompressSection
// ---------------------------------------------------------------------------

function CompressSection() {
  const [file, setFile] = useState<File | null>(null);
  const [quality, setQuality] = useState<number>(72);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<{
    originalSize: number;
    compressedSize: number;
    filename: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCompress = async () => {
    if (!file) return;
    setIsProcessing(true);
    setResult(null);
    setError(null);

    try {
      const { blob, filename, originalSize, compressedSize } = await compressPdf(file, quality);

      // Trigger download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setResult({ originalSize, compressedSize, filename });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al comprimir el archivo.');
    } finally {
      setIsProcessing(false);
    }
  };

  const savingsPercent =
    result && result.originalSize > 0
      ? Math.round((1 - result.compressedSize / result.originalSize) * 100)
      : null;

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      {/* Section header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Comprimir PDF</h2>
          <p className="text-sm text-gray-500">
            Reduce el peso recodificando las imágenes del documento
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Dropzone */}
        <PdfDropzone
          file={file}
          onFileChange={(f) => { setFile(f); setResult(null); setError(null); }}
          disabled={isProcessing}
          id="compress-dropzone"
        />

        {/* Quality selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Calidad de imagen
          </label>
          <div className="grid grid-cols-3 gap-2">
            {QUALITY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setQuality(opt.value)}
                disabled={isProcessing}
                className={cn(
                  'px-3 py-2 text-sm rounded-lg border transition-colors text-left',
                  quality === opt.value
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-primary-400'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Submit button */}
        <button
          type="button"
          onClick={handleCompress}
          disabled={!file || isProcessing}
          className={cn(
            'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors',
            file && !isProcessing
              ? 'bg-primary-600 hover:bg-primary-700 text-white'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          )}
        >
          {isProcessing ? (
            <>
              <Spinner />
              Comprimiendo…
            </>
          ) : (
            'Comprimir y descargar'
          )}
        </button>

        {/* Result */}
        {result && savingsPercent !== null && (
          <div className="rounded-lg bg-success-50 border border-success-200 p-4 text-sm">
            <p className="font-semibold text-success-700 mb-1">
              ✅ Compresión completada
            </p>
            <div className="text-success-600 space-y-0.5">
              <p>Tamaño original: <span className="font-medium">{formatBytes(result.originalSize)}</span></p>
              <p>Tamaño comprimido: <span className="font-medium">{formatBytes(result.compressedSize)}</span></p>
              <p>
                Ahorro:{' '}
                <span className="font-bold">
                  {savingsPercent > 0
                    ? `${savingsPercent}% (${formatBytes(result.originalSize - result.compressedSize)})`
                    : 'Sin reducción significativa'}
                </span>
              </p>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-danger-50 border border-danger-200 p-4 text-sm text-danger-700">
            ⚠️ {error}
          </div>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// SplitSection
// ---------------------------------------------------------------------------

function SplitSection() {
  const [file, setFile] = useState<File | null>(null);
  const [pagesPerChunk, setPagesPerChunk] = useState<number>(1000);
  const [isProcessing, setIsProcessing] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSplit = async () => {
    if (!file) return;
    setIsProcessing(true);
    setSuccess(false);
    setError(null);

    try {
      const { blob, filename } = await splitPdf(file, pagesPerChunk);

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al dividir el archivo.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      {/* Section header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex-shrink-0 w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
          <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Dividir PDF</h2>
          <p className="text-sm text-gray-500">
            Divide el documento en partes de N páginas y descárgalas en un ZIP
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Dropzone */}
        <PdfDropzone
          file={file}
          onFileChange={(f) => { setFile(f); setSuccess(false); setError(null); }}
          disabled={isProcessing}
          id="split-dropzone"
        />

        {/* Pages per chunk */}
        <div>
          <label
            htmlFor="pages-per-chunk"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Páginas por parte
          </label>
          <input
            id="pages-per-chunk"
            type="number"
            min={1}
            max={1000}
            value={pagesPerChunk}
            onChange={(e) => {
              const v = Math.max(1, Math.min(1000, Number(e.target.value) || 1));
              setPagesPerChunk(v);
            }}
            disabled={isProcessing}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
          />
          <p className="text-xs text-gray-500 mt-1">Mínimo 1 · Máximo 1000 (límite de Vertex AI)</p>
        </div>

        {/* Submit button */}
        <button
          type="button"
          onClick={handleSplit}
          disabled={!file || isProcessing}
          className={cn(
            'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors',
            file && !isProcessing
              ? 'bg-orange-600 hover:bg-orange-700 text-white'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          )}
        >
          {isProcessing ? (
            <>
              <Spinner />
              Dividiendo…
            </>
          ) : (
            'Dividir y descargar ZIP'
          )}
        </button>

        {/* Success */}
        {success && (
          <div className="rounded-lg bg-success-50 border border-success-200 p-4 text-sm text-success-700 font-medium">
            ✅ PDF dividido exitosamente. Revisa tu carpeta de descargas.
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-danger-50 border border-danger-200 p-4 text-sm text-danger-700">
            ⚠️ {error}
          </div>
        )}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Main PdfTools page
// ---------------------------------------------------------------------------

export function PdfTools() {
  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Herramientas PDF</h1>
        <p className="mt-1 text-gray-500">
          Prepara tus archivos para el análisis con IA: reduce el tamaño o divide documentos
          extensos antes de cargarlos.
        </p>
      </div>

      {/* Info banner */}
      <div className="rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 text-sm text-blue-700 flex gap-2">
        <span className="flex-shrink-0 mt-0.5">ℹ️</span>
        <span>
          <strong>Límites de Vertex AI:</strong> Los archivos deben pesar menos de 10&nbsp;MB y
          tener menos de 1&nbsp;000 páginas. Usa las herramientas a continuación si tu documento
          supera alguno de estos límites.
        </span>
      </div>

      {/* Tool sections */}
      <div className="grid gap-6 md:grid-cols-2">
        <CompressSection />
        <SplitSection />
      </div>
    </div>
  );
}
