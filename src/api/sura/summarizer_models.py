"""
Pydantic models for SURA Clinical Document Summarizer API.

These models define the structure of requests and responses for the
clinical summarization endpoints.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """A single clinical event in the patient's timeline."""

    date: str = Field(
        ...,
        description="Fecha del evento en formato ISO (YYYY-MM-DD) o 'Fecha desconocida'",
    )
    date_precision: Literal["exact", "approximate", "unknown"] = Field(
        ..., description="Precision de la fecha: exact, approximate, o unknown"
    )
    title: str = Field(
        ..., description="Titulo corto del evento (ej: 'Consulta Urologica')"
    )
    category: Literal[
        "diagnosis",
        "procedure",
        "medication",
        "examination",
        "lab_result",
        "hospitalization",
        "other",
    ] = Field(..., description="Categoria del evento clinico")
    description: str = Field(
        ..., description="Descripcion detallada narrativa del evento"
    )
    source_document: str = Field(
        ..., description="Nombre/identificador del documento fuente"
    )
    relevant_details: Optional[List[str]] = Field(
        default=None, description="Detalles clinicos clave (dosis, resultados, etc.)"
    )


class PatientOverview(BaseModel):
    """Overview of patient information extracted from clinical documents."""

    name: Optional[str] = Field(
        default=None, description="Nombre completo del paciente"
    )
    age: Optional[int] = Field(default=None, description="Edad del paciente en anos")
    patient_id: Optional[str] = Field(
        default=None, description="Numero de identificacion del paciente"
    )
    primary_conditions: List[str] = Field(
        default_factory=list,
        description="Condiciones/diagnosticos principales identificados",
    )


class ClinicalSummaryResponse(BaseModel):
    """Complete clinical summary response with chronological timeline."""

    patient_overview: PatientOverview = Field(
        ..., description="Informacion general del paciente"
    )
    timeline: List[TimelineEvent] = Field(
        ..., description="Linea de tiempo cronologica de eventos clinicos"
    )
    focus_summary: Optional[str] = Field(
        default=None,
        description="Resumen narrativo enfocado en el area solicitada por el usuario",
    )
    general_observations: str = Field(
        ..., description="Observaciones clinicas generales"
    )
    document_language: str = Field(
        ..., description="Idioma detectado de los documentos fuente"
    )
    documents_analyzed: int = Field(..., description="Numero de documentos analizados")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Nivel de confianza en el resumen (0.0 a 1.0)"
    )


# SSE Event models specific to the summarizer
class SummarizerSSEInitEvent(BaseModel):
    """SSE event sent at summarization start."""

    message: str = Field(..., description="Mensaje de inicio")
    files_count: int = Field(..., description="Numero de archivos a analizar")


class SummarizerSSEResultEvent(BaseModel):
    """SSE event containing the summarization result."""

    result: ClinicalSummaryResponse = Field(
        ..., description="Resultado completo del resumen"
    )
