"""
Clinical summarization schema for SURA healthcare.

This module contains the JSON schema definitions for structured
clinical summary responses from Gemini.
"""


class ClinicalSummarySchema:
    """Schema definitions for SURA clinical document summarization."""

    @staticmethod
    def get_summary_json_schema() -> dict:
        """
        Get the JSON schema for structured clinical summary output.

        This schema ensures that Gemini returns properly formatted JSON
        that matches the expected clinical summary response structure.

        Returns:
            Dictionary representing the JSON schema for clinical summary data
        """
        return {
            "type": "object",
            "properties": {
                "patient_overview": {
                    "type": "object",
                    "description": "Informacion general del paciente extraida de los documentos",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre completo del paciente",
                        },
                        "age": {
                            "type": "number",
                            "description": "Edad del paciente en anos",
                        },
                        "patient_id": {
                            "type": "string",
                            "description": "Numero de identificacion del paciente",
                        },
                        "primary_conditions": {
                            "type": "array",
                            "description": "Condiciones o diagnosticos principales identificados",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["primary_conditions"],
                },
                "timeline": {
                    "type": "array",
                    "description": "Linea de tiempo cronologica de eventos clinicos",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Fecha en formato ISO (YYYY-MM-DD) o 'Fecha desconocida'",
                            },
                            "date_precision": {
                                "type": "string",
                                "enum": ["exact", "approximate", "unknown"],
                                "description": "Precision de la fecha",
                            },
                            "title": {
                                "type": "string",
                                "description": "Titulo corto del evento clinico",
                            },
                            "category": {
                                "type": "string",
                                "enum": [
                                    "diagnosis",
                                    "procedure",
                                    "medication",
                                    "examination",
                                    "lab_result",
                                    "hospitalization",
                                    "other",
                                ],
                                "description": "Categoria del evento",
                            },
                            "description": {
                                "type": "string",
                                "description": "Descripcion detallada narrativa del evento",
                            },
                            "source_document": {
                                "type": "string",
                                "description": "Nombre del documento fuente de este evento",
                            },
                            "relevant_details": {
                                "type": "array",
                                "description": "Detalles clinicos clave (dosis, resultados, valores)",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "date",
                            "date_precision",
                            "title",
                            "category",
                            "description",
                            "source_document",
                        ],
                    },
                },
                "focus_summary": {
                    "type": "string",
                    "description": "Resumen narrativo enfocado en el area solicitada por el usuario (si aplica)",
                },
                "general_observations": {
                    "type": "string",
                    "description": "Observaciones clinicas generales y contexto del caso",
                },
                "document_language": {
                    "type": "string",
                    "description": "Idioma detectado de los documentos fuente (ej: 'es', 'en')",
                },
                "documents_analyzed": {
                    "type": "number",
                    "description": "Numero de documentos analizados",
                },
                "confidence_score": {
                    "type": "number",
                    "description": "Nivel de confianza en el resumen (0.0 a 1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
            },
            "required": [
                "patient_overview",
                "timeline",
                "general_observations",
                "document_language",
                "documents_analyzed",
                "confidence_score",
            ],
        }
