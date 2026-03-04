"""
Eligibility analysis schema for SURA healthcare contracts.

This module contains the JSON schema definitions for structured
eligibility analysis responses.
"""

from typing import Dict, Any


class EligibilityAnalysisSchema:
    """Schema definitions for SURA eligibility analysis."""
    
    @staticmethod
    def get_eligibility_json_schema() -> dict:
        """
        Get the JSON schema for structured eligibility analysis.
        
        This schema ensures that Gemini returns properly formatted JSON
        that matches the expected eligibility response structure.
        
        Returns:
            Dictionary representing the JSON schema for eligibility data
        """
        return {
            "type": "object",
            "properties": {
                "patient_data": {
                    "type": "object",
                    "description": "Datos del paciente extraídos de los documentos",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre completo del paciente"
                        },
                        "age": {
                            "type": "number",
                            "description": "Edad del paciente en años"
                        },
                        "patient_id": {
                            "type": "string",
                            "description": "Número de identificación del paciente"
                        },
                        "insurance_plan": {
                            "type": "string",
                            "description": "Tipo de plan de salud (PBS, PGP, etc.)"
                        },
                        "has_poliza": {
                            "type": "boolean",
                            "description": "Indica si el paciente tiene póliza Sura activa"
                        }
                    },
                    "required": ["name", "age", "patient_id", "insurance_plan"]
                },
                "eligibility_decision": {
                    "type": "string",
                    "enum": ["ELIGIBLE", "NOT_ELIGIBLE", "INSUFFICIENT_INFORMATION"],
                    "description": "Decisión final de elegibilidad"
                },
                "criteria_matrix": {
                    "type": "array",
                    "description": "Evaluación detallada de cada criterio",
                    "items": {
                        "type": "object",
                        "properties": {
                            "criterion": {
                                "type": "string",
                                "description": "Nombre del criterio evaluado"
                            },
                            "requirement": {
                                "type": "string",
                                "description": "Requisito específico del criterio"
                            },
                            "patient_value": {
                                "type": "string",
                                "description": "Valor encontrado en los documentos del paciente"
                            },
                            "status": {
                                "type": "string",
                                "description": "Estado del criterio: ✓ CUMPLE, ✗ NO CUMPLE, o ? DESCONOCIDO"
                            },
                            "justification": {
                                "type": "string",
                                "description": "Explicación detallada de la evaluación"
                            }
                        },
                        "required": ["criterion", "requirement", "patient_value", "status", "justification"]
                    }
                },
                "observations": {
                    "type": "string",
                    "description": "Análisis detallado del caso con observaciones y recomendaciones"
                },
                "confidence_score": {
                    "type": "number",
                    "description": "Nivel de confianza en la decisión (0.0 a 1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "missing_fields": {
                    "type": "array",
                    "description": "Lista de información faltante o documentos adicionales necesarios",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "patient_data",
                "eligibility_decision",
                "criteria_matrix",
                "observations",
                "confidence_score",
                "missing_fields"
            ]
        }
