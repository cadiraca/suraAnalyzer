"""
Pydantic models for SURA Healthcare eligibility analysis API.

These models define the structure of requests and responses for the
eligibility analysis endpoints.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class PatientData(BaseModel):
    """Patient information extracted from documents."""
    
    name: str = Field(..., description="Nombre completo del paciente")
    age: int = Field(..., description="Edad del paciente en años")
    patient_id: str = Field(..., description="Número de identificación del paciente")
    insurance_plan: str = Field(..., description="Tipo de plan de salud (PBS, PGP, etc.)")
    has_poliza: Optional[bool] = Field(None, description="Indica si el paciente tiene póliza Sura activa")


class CriterionEvaluation(BaseModel):
    """Evaluation of a single eligibility criterion."""
    
    criterion: str = Field(..., description="Nombre del criterio evaluado")
    requirement: str = Field(..., description="Requisito específico del criterio")
    patient_value: str = Field(..., description="Valor encontrado en los documentos del paciente")
    status: str = Field(..., description="Estado: ✓ CUMPLE, ✗ NO CUMPLE, o ? DESCONOCIDO")
    justification: str = Field(..., description="Explicación detallada de la evaluación")


class EligibilityResponse(BaseModel):
    """Complete eligibility analysis response."""
    
    patient_data: PatientData = Field(..., description="Datos del paciente extraídos")
    eligibility_decision: Literal["ELIGIBLE", "NOT_ELIGIBLE", "INSUFFICIENT_INFORMATION"] = Field(
        ..., 
        description="Decisión final de elegibilidad"
    )
    criteria_matrix: List[CriterionEvaluation] = Field(
        ..., 
        description="Evaluación detallada de cada criterio"
    )
    observations: str = Field(..., description="Análisis detallado del caso")
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Nivel de confianza en la decisión (0.0 a 1.0)"
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Lista de información faltante o documentos adicionales necesarios"
    )


class ContractInfo(BaseModel):
    """Information about a healthcare contract."""
    
    contract_id: str = Field(..., description="Identificador único del contrato")
    contract_name: str = Field(..., description="Nombre descriptivo del contrato")
    description: str = Field(..., description="Descripción del servicio cubierto")
    version: str = Field(..., description="Versión del contrato")
    active: bool = Field(..., description="Indica si el contrato está activo")
    default: bool = Field(default=False, description="Indica si es el contrato por defecto")


class ContractListResponse(BaseModel):
    """Response containing list of available contracts."""
    
    contracts: List[ContractInfo] = Field(..., description="Lista de contratos disponibles")
    total: int = Field(..., description="Número total de contratos")


class SSEInitEvent(BaseModel):
    """SSE event sent at analysis start."""
    
    message: str = Field(..., description="Mensaje de inicio")
    contract_id: str = Field(..., description="ID del contrato seleccionado")
    contract_name: str = Field(..., description="Nombre del contrato")
    files_count: int = Field(..., description="Número de archivos a analizar")


class SSEAnalyzingEvent(BaseModel):
    """SSE event sent during analysis."""
    
    message: str = Field(..., description="Mensaje de progreso")
    progress: int = Field(..., ge=0, le=100, description="Porcentaje de progreso")


class SSEResultEvent(BaseModel):
    """SSE event containing the analysis result."""
    
    result: EligibilityResponse = Field(..., description="Resultado completo del análisis")


class SSECompleteEvent(BaseModel):
    """SSE event sent when analysis is complete."""
    
    message: str = Field(..., description="Mensaje de finalización")
    processing_time_seconds: float = Field(..., description="Tiempo de procesamiento en segundos")


class SSEErrorEvent(BaseModel):
    """SSE event sent when an error occurs."""
    
    error: str = Field(..., description="Mensaje de error")
    error_code: str = Field(..., description="Código de error")
    details: Optional[str] = Field(None, description="Detalles adicionales del error")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(..., description="Mensaje de error")
    error_code: str = Field(..., description="Código de error")
    details: Optional[str] = Field(None, description="Detalles adicionales")
