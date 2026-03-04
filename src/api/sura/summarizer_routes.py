"""
SURA Clinical Document Summarizer API routes.

Provides the endpoint for clinical document summarization
with Server-Sent Events (SSE) streaming.
"""

import os
import json
import time
import logging
import asyncio
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.client_manager import get_gemini_client
from src.api.gemini_client import GeminiClient
from .summarizer_schema import ClinicalSummarySchema
from .summarizer_prompt import build_clinical_summary_prompt
from .summarizer_models import (
    ClinicalSummaryResponse,
    SummarizerSSEInitEvent,
)
from .models import (
    SSEAnalyzingEvent,
    SSECompleteEvent,
    SSEErrorEvent,
)
from .auth import verify_api_key
from src.api.utils import (
    get_mime_type,
    validate_file_for_analysis,
    encode_file_to_base64,
)

logger = logging.getLogger(__name__)

summarizer_router = APIRouter(prefix="/api/v1/sura", tags=["SURA Clinical Summarizer"])


@summarizer_router.post(
    "/summarize-clinical",
    summary="Summarize clinical documents",
    description="Generate a chronological clinical summary from uploaded medical documents with SSE streaming",
    responses={
        200: {"description": "SSE stream with summarization progress and results"},
        401: {"description": "Authentication failed"},
        400: {"description": "Invalid request"},
        500: {"description": "Server error"},
    },
)
async def summarize_clinical_stream(
    files: List[UploadFile] = File(
        ..., description="Clinical documents (PDFs, images)"
    ),
    focus: Optional[str] = Form(
        None, description="Optional focus area for the summary"
    ),
    api_key: str = Depends(verify_api_key),
    client: GeminiClient = Depends(get_gemini_client),
):
    """
    Generate a chronological clinical summary from medical documents with streaming response.

    This endpoint analyzes uploaded clinical documents and produces a unified
    chronological timeline of the patient's medical history.

    Args:
        files: List of clinical documents (PDFs, images)
        focus: Optional focus area for the summary
        api_key: API key for authentication (from header)
        client: Gemini client instance

    Returns:
        StreamingResponse with Server-Sent Events
    """

    async def generate_sse_stream():
        """Generate Server-Sent Events stream for clinical summarization."""
        start_time = time.time()
        temp_files = []

        try:
            # Step 1: Send init event
            init_event = SummarizerSSEInitEvent(
                message="Iniciando resumen de documentos clinicos",
                files_count=len(files),
            )
            yield f"event: init\ndata: {init_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)

            # Step 2: Validate files
            if not files:
                error_event = SSEErrorEvent(
                    error="No se proporcionaron archivos para analizar",
                    error_code="NO_FILES",
                    details=None,
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return

            analyzing_event = SSEAnalyzingEvent(
                message=f"Validando y procesando {len(files)} archivo(s)...",
                progress=20,
            )
            yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)

            # Step 3: Save files temporarily and encode to base64
            file_parts = []
            filenames = []

            for idx, file in enumerate(files):
                if not file.filename:
                    error_event = SSEErrorEvent(
                        error=f"Archivo #{idx + 1} sin nombre",
                        error_code="NO_FILENAME",
                        details=None,
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return

                filenames.append(file.filename)

                # Save file temporarily
                temp_file_path = (
                    f"/tmp/sura_summary_{int(time.time())}_{idx}_{file.filename}"
                )
                temp_files.append(temp_file_path)

                with open(temp_file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)

                # Detect MIME type
                mime_type = get_mime_type(temp_file_path)
                if not mime_type:
                    error_event = SSEErrorEvent(
                        error=f"No se pudo detectar el tipo de archivo: {file.filename}",
                        error_code="UNKNOWN_FILE_TYPE",
                        details=None,
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return

                # Validate file
                validation = validate_file_for_analysis(temp_file_path, mime_type)
                if not validation["valid"]:
                    error_event = SSEErrorEvent(
                        error=f"Validacion fallida para {file.filename}: {', '.join(validation['errors'])}",
                        error_code="VALIDATION_FAILED",
                        details=None,
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return

                # Encode to base64
                base64_data = encode_file_to_base64(temp_file_path, mime_type)

                # Add to parts list
                file_parts.append(
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_data,
                        }
                    }
                )

                logger.info(
                    f"File processed for summarization: {file.filename} ({mime_type})"
                )

            # Step 4: Prepare for Gemini analysis
            analyzing_event = SSEAnalyzingEvent(
                message="Analizando documentos clinicos con Inteligencia Artificial...",
                progress=50,
            )
            yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)

            logger.info(
                f"Calling Gemini API for clinical summarization (focus: {focus or 'none'})..."
            )

            # Step 5: Call Gemini API with streaming
            try:
                # Build prompt
                prompt = build_clinical_summary_prompt(focus=focus, filenames=filenames)

                # Get the clinical summary schema
                summary_schema = ClinicalSummarySchema.get_summary_json_schema()

                # Accumulate the streamed JSON response
                response_text = ""
                chunk_count = 0

                logger.info("[SUMMARIZER] Starting async iteration over Gemini stream")
                async for chunk in client.analyze_multiple_files_structured_stream(
                    file_parts=file_parts,
                    prompt=prompt,
                    response_schema=summary_schema,
                ):
                    chunk_count += 1
                    response_text += chunk
                    logger.info(
                        f"[SUMMARIZER] Received chunk #{chunk_count}, length: {len(chunk)} characters"
                    )

                    # Send progress updates as chunks arrive
                    progress = min(50 + (chunk_count * 5), 90)
                    analyzing_event = SSEAnalyzingEvent(
                        message=f"Generando resumen clinico... ({chunk_count} fragmentos recibidos)",
                        progress=progress,
                    )
                    yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
                    await asyncio.sleep(0)

                logger.info(
                    f"[SUMMARIZER] Stream complete, total chunks: {chunk_count}"
                )

                analyzing_event = SSEAnalyzingEvent(
                    message="Procesando resultados del resumen...",
                    progress=95,
                )
                yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
                await asyncio.sleep(0)

                logger.info(
                    f"Gemini summarization response: {len(response_text)} characters"
                )

                # Parse JSON response
                result_data = json.loads(response_text)

                # Validate with Pydantic model
                summary_result = ClinicalSummaryResponse(**result_data)

                # Sort timeline by date (unknown dates go to end)
                summary_result.timeline.sort(
                    key=lambda e: (
                        e.date_precision == "unknown",
                        e.date if e.date != "Fecha desconocida" else "9999-99-99",
                    )
                )

                # Step 6: Send result event
                result_event = {"result": summary_result.model_dump()}
                yield f"event: result\ndata: {json.dumps(result_event)}\n\n"
                await asyncio.sleep(0)

            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse Gemini summarization response as JSON: {e}"
                )
                error_event = SSEErrorEvent(
                    error="Error al procesar la respuesta del resumen",
                    error_code="PARSE_ERROR",
                    details=str(e),
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            except Exception as e:
                logger.error(f"Error during Gemini summarization: {e}", exc_info=True)
                error_event = SSEErrorEvent(
                    error=f"Error durante el resumen: {str(e)}",
                    error_code="ANALYSIS_ERROR",
                    details=None,
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return

            # Step 7: Send completion event
            processing_time = time.time() - start_time
            complete_event = SSECompleteEvent(
                message="Resumen clinico completado exitosamente",
                processing_time_seconds=round(processing_time, 2),
            )
            yield f"event: complete\ndata: {complete_event.model_dump_json()}\n\n"

            logger.info(f"Clinical summarization completed in {processing_time:.2f}s")

        except Exception as e:
            logger.error(
                f"Unexpected error in summarization stream: {e}", exc_info=True
            )
            error_event = SSEErrorEvent(
                error=f"Error inesperado: {str(e)}",
                error_code="INTERNAL_ERROR",
                details=None,
            )
            yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"

        finally:
            # Cleanup temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")

    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
