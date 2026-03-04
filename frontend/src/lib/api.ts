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
