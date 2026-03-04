"""
SURA Healthcare eligibility analysis API routes.

Provides endpoints for contract management and eligibility analysis
with Server-Sent Events (SSE) streaming.
"""

import os
import json
import time
import logging
import asyncio
from typing import List, Optional
from pathlib import Path
import tempfile

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.client_manager import get_gemini_client
from src.api.gemini_client import GeminiClient
from .eligibility_schema import EligibilityAnalysisSchema

from .models import (
    ContractListResponse,
    EligibilityResponse,
    ErrorResponse,
    SSEInitEvent,
    SSEAnalyzingEvent,
    SSECompleteEvent,
    SSEErrorEvent
)
from .contract_loader import (
    list_contracts,
    load_contract,
    get_default_contract,
    ContractLoadError
)
from .auth import verify_api_key
from src.api.utils import get_mime_type, validate_file_for_analysis, encode_file_to_base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sura", tags=["SURA Eligibility"])


@router.get(
    "/contracts",
    response_model=ContractListResponse,
    summary="List available contracts",
    description="Get list of all available healthcare contracts for eligibility analysis"
)
async def get_contracts(
    api_key: str = Depends(verify_api_key)
) -> ContractListResponse:
    """
    List all available healthcare contracts.
    
    Returns:
        ContractListResponse with list of available contracts
    """
    try:
        contracts = list_contracts()
        return ContractListResponse(
            contracts=contracts,
            total=len(contracts)
        )
    except Exception as e:
        logger.error(f"Error listing contracts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing contracts: {str(e)}"
        )

async def save_upload_file(upload_file: UploadFile) -> str:
    """
    Save uploaded file to temporary location.
    
    Args:
        upload_file: FastAPI UploadFile object
        
    Returns:
        Path to saved temporary file
    """
    try:
        # Create temporary file
        suffix = os.path.splitext(upload_file.filename or "")[1] if upload_file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            # Read and write file content
            content = await upload_file.read()
            tmp_file.write(content)
            tmp_file.flush()
            return tmp_file.name
    except Exception as e:
        logger.error(f"Error saving upload file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")


@router.post(
    "/analyze-eligibility",
    summary="Analyze eligibility with streaming",
    description="Analyze patient eligibility for a healthcare service using AI with real-time SSE streaming",
    responses={
        200: {"description": "SSE stream with analysis progress and results"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def analyze_eligibility_stream(
    files: List[UploadFile] = File(..., description="Medical documents (PDFs, images)"),
    contract_id: Optional[str] = Form(None, description="Contract ID (optional, uses default if not provided)"),
    api_key: str = Depends(verify_api_key),
    client: GeminiClient = Depends(get_gemini_client)
):
    """
    Analyze patient eligibility for a healthcare service with streaming response.
    
    This endpoint performs a single-pass AI analysis of medical documents,
    extracting patient data and evaluating eligibility criteria in one call.
    
    Args:
        files: List of medical documents (PDFs, images)
        contract_id: Optional contract identifier (defaults to litotripsia_ureteral)
        api_key: API key for authentication (from header)
        
    Returns:
        StreamingResponse with Server-Sent Events
    """
    
    async def generate_sse_stream():
        """Generate Server-Sent Events stream."""
        start_time = time.time()
        temp_files = []
        
        try:
            # Step 1: Load contract
            logger.info(f"Loading contract: {contract_id or 'default'}")
            
            try:
                if contract_id:
                    contract = load_contract(contract_id)
                else:
                    contract = get_default_contract()
            except ContractLoadError as e:
                error_event = SSEErrorEvent(
                    error=f"Contract not found: {str(e)}",
                    error_code="CONTRACT_NOT_FOUND"
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            
            # Step 2: Send init event
            init_event = SSEInitEvent(
                message=f"Iniciando análisis de elegibilidad para {contract.contract_name}",
                contract_id=contract.contract_id,
                contract_name=contract.contract_name,
                files_count=len(files)
            )
            yield f"event: init\ndata: {init_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)
            
            # Step 3: Validate and save files
            if not files:
                error_event = SSEErrorEvent(
                    error="No se proporcionaron archivos para analizar",
                    error_code="NO_FILES"
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            
            analyzing_event = SSEAnalyzingEvent(
                message=f"Validando y procesando {len(files)} archivo(s)...",
                progress=20
            )
            yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)
            
            # Save files temporarily and encode to base64
            file_parts = []
            
            for idx, file in enumerate(files):
                if not file.filename:
                    error_event = SSEErrorEvent(
                        error=f"Archivo #{idx+1} sin nombre",
                        error_code="NO_FILENAME"
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return
                
                # Save file temporarily
                temp_file_path = f"/tmp/sura_{int(time.time())}_{idx}_{file.filename}"
                temp_files.append(temp_file_path)
                
                with open(temp_file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                # Detect MIME type
                mime_type = get_mime_type(temp_file_path)
                if not mime_type:
                    error_event = SSEErrorEvent(
                        error=f"No se pudo detectar el tipo de archivo: {file.filename}",
                        error_code="UNKNOWN_FILE_TYPE"
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return
                
                # Validate file
                validation = validate_file_for_analysis(temp_file_path, mime_type)
                if not validation['valid']:
                    error_event = SSEErrorEvent(
                        error=f"Validación fallida para {file.filename}: {', '.join(validation['errors'])}",
                        error_code="VALIDATION_FAILED"
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return
                
                # Encode to base64
                base64_data = encode_file_to_base64(temp_file_path, mime_type)
                
                # Add to parts list
                file_parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data
                    }
                })
                
                logger.info(f"File processed: {file.filename} ({mime_type})")
            
            # Step 4: Prepare for Gemini analysis
            analyzing_event = SSEAnalyzingEvent(
                message="Analizando documentos con Inteligencia Artificial...",
                progress=50
            )
            yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)
            
            # Get Gemini client
            #client_manager = ClientManager.get_instance()
            #gemini_client = client_manager.get_client()
            
            logger.info(f"Calling Gemini API for eligibility analysis with streaming...")
            
            # Step 5: Call Gemini API using streaming (like analyze_file_stream!)
            try:
                # Get the standardized eligibility schema
                eligibility_schema = EligibilityAnalysisSchema.get_eligibility_json_schema()
                
                # Accumulate the streamed JSON response
                response_text = ""
                chunk_count = 0
                
                # Stream analysis results using async for (same pattern as analyze_file_stream)
                logger.info("[SSE_ROUTE] Starting async iteration over Gemini stream")
                async for chunk in client.analyze_multiple_files_structured_stream(
                    file_parts=file_parts,
                    prompt=contract.eligibility_instructions,
                    response_schema=eligibility_schema
                ):
                    chunk_count += 1
                    response_text += chunk
                    logger.info(f"[SSE_ROUTE] Received chunk #{chunk_count}, length: {len(chunk)} characters")
                    
                    # Send progress updates as chunks arrive
                    progress = min(50 + (chunk_count * 5), 90)  # Progress from 50% to 90%
                    analyzing_event = SSEAnalyzingEvent(
                        message=f"Analizando documentos... ({chunk_count} fragmentos recibidos)",
                        progress=progress
                    )
                    yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
                    await asyncio.sleep(0)
                
                logger.info(f"[SSE_ROUTE] Stream complete, total chunks: {chunk_count}")
                
                analyzing_event = SSEAnalyzingEvent(
                    message="Procesando resultados del análisis...",
                    progress=95
                )
                yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
                await asyncio.sleep(0)
                
                logger.info(f"Gemini response received: {len(response_text)} characters")
                
                # Parse JSON response
                result_data = json.loads(response_text)
                
                # Validate with Pydantic model
                eligibility_result = EligibilityResponse(**result_data)
                
                # Step 6: Send result event
                result_event = {
                    "result": eligibility_result.model_dump()
                }
                yield f"event: result\ndata: {json.dumps(result_event)}\n\n"
                await asyncio.sleep(0)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                error_event = SSEErrorEvent(
                    error="Error al procesar la respuesta del análisis",
                    error_code="PARSE_ERROR",
                    details=str(e)
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            except Exception as e:
                logger.error(f"Error during Gemini analysis: {e}", exc_info=True)
                error_event = SSEErrorEvent(
                    error=f"Error durante el análisis: {str(e)}",
                    error_code="ANALYSIS_ERROR"
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            
            # Step 7: Send completion event
            processing_time = time.time() - start_time
            complete_event = SSECompleteEvent(
                message="✅ Análisis completado exitosamente",
                processing_time_seconds=round(processing_time, 2)
            )
            yield f"event: complete\ndata: {complete_event.model_dump_json()}\n\n"
            
            logger.info(f"Analysis completed in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Unexpected error in analysis stream: {e}", exc_info=True)
            error_event = SSEErrorEvent(
                error=f"Error inesperado: {str(e)}",
                error_code="INTERNAL_ERROR"
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
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )

@router.post("/analyze-file")
async def analyze_file_stream(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    max_tokens: int = Form(4096),
    temperature: float = Form(0.7),
    client: GeminiClient = Depends(get_gemini_client)
):
    """
    Analyze uploaded file with streaming response via Server-Sent Events.
    
    This endpoint accepts any supported file type and returns real-time analysis
    results through SSE (Server-Sent Events).
    
    **Event Types:**
    - `status`: Processing status updates
    - `chunk`: Analysis content chunks from Gemini
    - `error`: Error messages
    - `complete`: Analysis completion signal
    
    **Supported File Types:**
    - Documents: PDF, DOCX, TXT
    - Images: PNG, JPG, JPEG, GIF, WEBP
    - Audio: MP3, WAV, M4A, OGG
    - Video: MP4, MOV, WEBM, AVI
    - Spreadsheets: XLSX, CSV
    - Presentations: PPTX
    """
    
    temp_path = None
    
    async def event_stream():
        nonlocal temp_path
        
        try:
            logger.info(f"[SSE_ROUTE] Starting file analysis stream for: {file.filename}")
            
            # Validate parameters
            if max_tokens < 1 or max_tokens > 8192:
                error_data = json.dumps({
                    "message": "max_tokens must be between 1 and 8192",
                    "error_code": "INVALID_PARAMETERS"
                })
                logger.error(f"[SSE_ROUTE] Parameter validation failed: max_tokens={max_tokens}")
                yield f"event: error\ndata: {error_data}\n\n"
                return
            
            if temperature < 0.0 or temperature > 1.0:
                error_data = json.dumps({
                    "message": "temperature must be between 0.0 and 1.0",
                    "error_code": "INVALID_PARAMETERS"
                })
                logger.error(f"[SSE_ROUTE] Parameter validation failed: temperature={temperature}")
                yield f"event: error\ndata: {error_data}\n\n"
                return
            
            # Step 1: Validate file
            status_data = json.dumps({
                "message": f"Validating file: {file.filename}",
                "step": "validation"
            })
            logger.info(f"[SSE_ROUTE] Sending validation status")
            yield f"event: status\ndata: {status_data}\n\n"
            
            if not file.filename:
                error_data = json.dumps({
                    "message": "No filename provided",
                    "error_code": "NO_FILENAME"
                })
                logger.error("[SSE_ROUTE] No filename provided")
                yield f"event: error\ndata: {error_data}\n\n"
                return
            
            # Step 2: Save file temporarily
            status_data = json.dumps({
                "message": "Processing uploaded file...",
                "step": "file_processing"
            })
            logger.info("[SSE_ROUTE] Processing uploaded file")
            yield f"event: status\ndata: {status_data}\n\n"
            
            temp_path = await save_upload_file(file)
            logger.info(f"[SSE_ROUTE] File saved to: {temp_path}")
            
            # Step 3: Detect MIME type and validate
            detected_mime = get_mime_type(temp_path)
            provided_mime = file.content_type
            mime_type = detected_mime or provided_mime
            
            if not mime_type:
                error_data = json.dumps({
                    "message": "Could not detect file MIME type",
                    "error_code": "UNKNOWN_FILE_TYPE"
                })
                logger.error(f"[SSE_ROUTE] Could not detect MIME type for: {temp_path}")
                yield f"event: error\ndata: {error_data}\n\n"
                return
            
            validation = validate_file_for_analysis(temp_path, mime_type)
            logger.info(f"[SSE_ROUTE] File validation result: {validation}")
            
            if not validation['valid']:
                error_data = json.dumps({
                    "message": f"File validation failed: {', '.join(validation['errors'])}",
                    "error_code": "VALIDATION_FAILED",
                    "details": validation
                })
                logger.error(f"[SSE_ROUTE] File validation failed: {validation['errors']}")
                yield f"event: error\ndata: {error_data}\n\n"
                return
            
            # Step 4: Start analysis
            status_data = json.dumps({
                "message": f"Starting AI analysis of {validation['file_type']} file ({validation['size_mb']}MB)...",
                "step": "analysis_start",
                "file_info": {
                    "type": validation['file_type'],
                    "mime_type": mime_type,
                    "size_mb": validation['size_mb']
                }
            })
            logger.info(f"[SSE_ROUTE] Starting analysis for {validation['file_type']} file")
            yield f"event: status\ndata: {status_data}\n\n"
            
            # Step 5: Stream analysis results using async for
            chunk_count = 0
            logger.info("[SSE_ROUTE] Starting async iteration over Gemini stream")
            async for chunk in client.analyze_file_stream(
                temp_path,
                mime_type=mime_type,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            ):
                chunk_count += 1
                chunk_data = json.dumps({
                    "content": chunk,
                    "chunk_number": chunk_count
                })
                logger.info(f"[SSE_ROUTE] Sending chunk #{chunk_count} to client, length: {len(chunk)}")
                yield f"event: chunk\ndata: {chunk_data}\n\n"
            
            # Step 6: Complete
            complete_data = json.dumps({
                "message": "Analysis completed successfully",
                "total_chunks": chunk_count
            })
            logger.info(f"[SSE_ROUTE] Analysis complete, total chunks sent: {chunk_count}")
            yield f"event: complete\ndata: {complete_data}\n\n"
            
        except HTTPException as e:
            error_data = json.dumps({
                "message": e.detail,
                "error_code": "HTTP_ERROR",
                "status_code": e.status_code
            })
            logger.error(f"[SSE_ROUTE] HTTP error: {e.detail}")
            yield f"event: error\ndata: {error_data}\n\n"
        except Exception as e:
            logger.error(f"[SSE_ROUTE] Streaming analysis error: {e}", exc_info=True)
            error_data = json.dumps({
                "message": str(e),
                "error_code": "ANALYSIS_ERROR"
            })
            yield f"event: error\ndata: {error_data}\n\n"
        finally:
            # Cleanup temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"[SSE_ROUTE] Cleaned up temp file: {temp_path}")
                except Exception as cleanup_error:
                    logger.warning(f"[SSE_ROUTE] Failed to cleanup temp file {temp_path}: {cleanup_error}")
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "X-Content-Type-Options": "nosniff",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        }
    )


@router.post(
    "/analyze-eligibility-stream",
    summary="Analyze eligibility with streaming",
    description="Analyze patient eligibility for a healthcare service using AI with real-time SSE streaming",
    responses={
        200: {"description": "SSE stream with analysis progress and results"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def analyze_eligibility_stream_v2(
    files: List[UploadFile] = File(..., description="Medical documents (PDFs, images)"),
    contract_id: Optional[str] = Form(None, description="Contract ID (optional, uses default if not provided)"),
    api_key: str = Depends(verify_api_key),
    client: GeminiClient = Depends(get_gemini_client)
):
    """
    Analyze patient eligibility for a healthcare service with streaming response.
    
    This endpoint performs a single-pass AI analysis of medical documents,
    extracting patient data and evaluating eligibility criteria in one call.
    
    Args:
        files: List of medical documents (PDFs, images)
        contract_id: Optional contract identifier (defaults to litotripsia_ureteral)
        api_key: API key for authentication (from header)
        
    Returns:
        StreamingResponse with Server-Sent Events
    """
    
    async def generate_sse_stream():
        """Generate Server-Sent Events stream."""
        start_time = time.time()
        temp_files = []
        
        try:
            # Step 1: Load contract
            logger.info(f"Loading contract: {contract_id or 'default'}")
            
            try:
                if contract_id:
                    contract = load_contract(contract_id)
                else:
                    contract = get_default_contract()
            except ContractLoadError as e:
                error_event = SSEErrorEvent(
                    error=f"Contract not found: {str(e)}",
                    error_code="CONTRACT_NOT_FOUND"
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            
            # Step 2: Send init event
            init_event = SSEInitEvent(
                message=f"Iniciando análisis de elegibilidad para {contract.contract_name}",
                contract_id=contract.contract_id,
                contract_name=contract.contract_name,
                files_count=len(files)
            )
            yield f"event: init\ndata: {init_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)
            
            # Step 3: Validate and save files
            if not files:
                error_event = SSEErrorEvent(
                    error="No se proporcionaron archivos para analizar",
                    error_code="NO_FILES"
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            
            analyzing_event = SSEAnalyzingEvent(
                message=f"Validando y procesando {len(files)} archivo(s)...",
                progress=20
            )
            yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)
            
            # Save files temporarily and encode to base64
            file_parts = []
            
            for idx, file in enumerate(files):
                if not file.filename:
                    error_event = SSEErrorEvent(
                        error=f"Archivo #{idx+1} sin nombre",
                        error_code="NO_FILENAME"
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return
                
                # Save file temporarily
                temp_file_path = f"/tmp/sura_{int(time.time())}_{idx}_{file.filename}"
                temp_files.append(temp_file_path)
                
                with open(temp_file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                # Detect MIME type
                mime_type = get_mime_type(temp_file_path)
                if not mime_type:
                    error_event = SSEErrorEvent(
                        error=f"No se pudo detectar el tipo de archivo: {file.filename}",
                        error_code="UNKNOWN_FILE_TYPE"
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return
                
                # Validate file
                validation = validate_file_for_analysis(temp_file_path, mime_type)
                if not validation['valid']:
                    error_event = SSEErrorEvent(
                        error=f"Validación fallida para {file.filename}: {', '.join(validation['errors'])}",
                        error_code="VALIDATION_FAILED"
                    )
                    yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                    return
                
                # Encode to base64
                base64_data = encode_file_to_base64(temp_file_path, mime_type)
                
                # Add to parts list
                file_parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data
                    }
                })
                
                logger.info(f"File processed: {file.filename} ({mime_type})")
            
            # Step 4: Prepare for Gemini analysis
            analyzing_event = SSEAnalyzingEvent(
                message="Analizando documentos con Inteligencia Artificial...",
                progress=50
            )
            yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
            await asyncio.sleep(0)
            
            # Get Gemini client
            #client_manager = ClientManager.get_instance()
            #gemini_client = client_manager.get_client()
            
            logger.info(f"Calling Gemini API for eligibility analysis...")
            
            # Step 5: Call Gemini API using the client's method (single call!)
            try:
                # Get the standardized eligibility schema
                eligibility_schema = EligibilityAnalysisSchema.get_eligibility_json_schema()
                
                # Use the client's analyze_multiple_files_structured method
                response_text = client.analyze_multiple_files_structured(
                    file_parts=file_parts,
                    prompt=contract.eligibility_instructions,
                    response_schema=eligibility_schema
                )
                
                analyzing_event = SSEAnalyzingEvent(
                    message="Procesando resultados del análisis...",
                    progress=90
                )
                yield f"event: analyzing\ndata: {analyzing_event.model_dump_json()}\n\n"
                await asyncio.sleep(0)
                
                logger.info(f"Gemini response received: {len(response_text)} characters")
                
                # Parse JSON response
                result_data = json.loads(response_text)
                
                # Validate with Pydantic model
                eligibility_result = EligibilityResponse(**result_data)
                
                # Step 6: Send result event
                result_event = {
                    "result": eligibility_result.model_dump()
                }
                yield f"event: result\ndata: {json.dumps(result_event)}\n\n"
                await asyncio.sleep(0)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini response as JSON: {e}")
                error_event = SSEErrorEvent(
                    error="Error al procesar la respuesta del análisis",
                    error_code="PARSE_ERROR",
                    details=str(e)
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            except Exception as e:
                logger.error(f"Error during Gemini analysis: {e}", exc_info=True)
                error_event = SSEErrorEvent(
                    error=f"Error durante el análisis: {str(e)}",
                    error_code="ANALYSIS_ERROR"
                )
                yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"
                return
            
            # Step 7: Send completion event
            processing_time = time.time() - start_time
            complete_event = SSECompleteEvent(
                message="✅ Análisis completado exitosamente",
                processing_time_seconds=round(processing_time, 2)
            )
            yield f"event: complete\ndata: {complete_event.model_dump_json()}\n\n"
            
            logger.info(f"Analysis completed in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Unexpected error in analysis stream: {e}", exc_info=True)
            error_event = SSEErrorEvent(
                error=f"Error inesperado: {str(e)}",
                error_code="INTERNAL_ERROR"
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
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )
