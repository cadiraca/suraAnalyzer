import type {
  Contract,
  SSEInitEvent,
  SSEAnalyzingEvent,
  SSEResultEvent,
  SSEErrorEvent,
  SummarizerSSEInitEvent,
  ClinicalSummaryResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || 'sura_internal_key_001';

// Fetch contracts
export async function fetchContracts(): Promise<Contract[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sura/contracts`, {
    headers: {
      'X-SURA-API-Key': API_KEY,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch contracts');
  }

  const data = await response.json();
  return data.contracts || [];
}

// SSE Event Handlers
export interface SSEHandlers {
  onInit?: (data: SSEInitEvent) => void;
  onAnalyzing?: (data: SSEAnalyzingEvent) => void;
  onResult?: (data: SSEResultEvent) => void;
  onComplete?: () => void;
  onError?: (data: SSEErrorEvent) => void;
}

// Analyze eligibility with SSE streaming
export function analyzeEligibility(
  files: File[],
  contractId: string | null,
  handlers: SSEHandlers
): () => void {
  const formData = new FormData();

  // Add files
  files.forEach((file) => {
    formData.append('files', file);
  });

  // Add contract_id if specified
  if (contractId) {
    formData.append('contract_id', contractId);
  }

  // Create AbortController for cancellation
  const abortController = new AbortController();

  // Start SSE request
  fetch(`${API_BASE_URL}/api/v1/sura/analyze-eligibility`, {
    method: 'POST',
    headers: {
      'X-SURA-API-Key': API_KEY,
      'Accept': 'text/event-stream',
    },
    body: formData,
    signal: abortController.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            continue;
          }

          if (line.startsWith('data:')) {
            const data = line.substring(5).trim();

            if (!data) continue;

            try {
              const parsed = JSON.parse(data);

              // Handle different event types
              if (parsed.contract_id) {
                handlers.onInit?.(parsed as SSEInitEvent);
              } else if (parsed.message && parsed.progress !== undefined) {
                handlers.onAnalyzing?.(parsed as SSEAnalyzingEvent);
              } else if (parsed.result) {
                // Result event has nested structure: {"result": {...}}
                handlers.onResult?.(parsed.result as SSEResultEvent);
              } else if (parsed.error) {
                handlers.onError?.(parsed as SSEErrorEvent);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }

          if (line.trim() === '') {
            // Empty line indicates end of event
            continue;
          }
        }
      }

      handlers.onComplete?.();
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        handlers.onError?.({ error: error.message });
      }
    });

  // Return cleanup function
  return () => {
    abortController.abort();
  };
}

// SSE Event Handlers for Clinical Summarizer
export interface SummarizerSSEHandlers {
  onInit?: (data: SummarizerSSEInitEvent) => void;
  onAnalyzing?: (data: SSEAnalyzingEvent) => void;
  onResult?: (data: ClinicalSummaryResponse) => void;
  onComplete?: () => void;
  onError?: (data: SSEErrorEvent) => void;
}

// Summarize clinical documents with SSE streaming
export function summarizeClinical(
  files: File[],
  focus: string | undefined,
  handlers: SummarizerSSEHandlers
): () => void {
  const formData = new FormData();

  // Add files
  files.forEach((file) => {
    formData.append('files', file);
  });

  // Add focus if specified
  if (focus && focus.trim()) {
    formData.append('focus', focus.trim());
  }

  // Create AbortController for cancellation
  const abortController = new AbortController();

  // Start SSE request
  fetch(`${API_BASE_URL}/api/v1/sura/summarize-clinical`, {
    method: 'POST',
    headers: {
      'X-SURA-API-Key': API_KEY,
      'Accept': 'text/event-stream',
    },
    body: formData,
    signal: abortController.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            continue;
          }

          if (line.startsWith('data:')) {
            const data = line.substring(5).trim();

            if (!data) continue;

            try {
              const parsed = JSON.parse(data);

              // Handle different event types
              if (parsed.files_count !== undefined && parsed.message && !parsed.progress) {
                handlers.onInit?.(parsed as SummarizerSSEInitEvent);
              } else if (parsed.message && parsed.progress !== undefined) {
                handlers.onAnalyzing?.(parsed as SSEAnalyzingEvent);
              } else if (parsed.result) {
                handlers.onResult?.(parsed.result as ClinicalSummaryResponse);
              } else if (parsed.error) {
                handlers.onError?.(parsed as SSEErrorEvent);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }

          if (line.trim() === '') {
            continue;
          }
        }
      }

      handlers.onComplete?.();
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        handlers.onError?.({ error: error.message });
      }
    });

  // Return cleanup function
  return () => {
    abortController.abort();
  };
}

// ---------------------------------------------------------------------------
// PDF Tools API
// ---------------------------------------------------------------------------

export interface CompressPdfResult {
  blob: Blob;
  filename: string;
  originalSize: number;
  compressedSize: number;
}

/** Compress a PDF by re-encoding its embedded images at a lower JPEG quality. */
export async function compressPdf(file: File, quality: number): Promise<CompressPdfResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('quality', String(quality));

  const response = await fetch(`${API_BASE_URL}/api/v1/pdf-tools/compress`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse error
    }
    throw new Error(`Error al comprimir el PDF: ${detail}`);
  }

  const blob = await response.blob();

  // Extract sizes from response headers (set by backend)
  const originalSize = Number(response.headers.get('X-Original-Size') ?? file.size);
  const compressedSize = Number(response.headers.get('X-Compressed-Size') ?? blob.size);

  // Derive filename from Content-Disposition or construct from original
  const disposition = response.headers.get('Content-Disposition') ?? '';
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : `compressed_${file.name}`;

  return { blob, filename, originalSize, compressedSize };
}

export interface SplitPdfResult {
  blob: Blob;
  filename: string;
}

/** Split a PDF into chunks of pagesPerChunk pages, returned as a ZIP archive. */
export async function splitPdf(file: File, pagesPerChunk: number): Promise<SplitPdfResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('pages_per_chunk', String(pagesPerChunk));

  const response = await fetch(`${API_BASE_URL}/api/v1/pdf-tools/split`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse error
    }
    throw new Error(`Error al dividir el PDF: ${detail}`);
  }

  const blob = await response.blob();

  const disposition = response.headers.get('Content-Disposition') ?? '';
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : `split_${file.name.replace('.pdf', '')}.zip`;

  return { blob, filename };
}
