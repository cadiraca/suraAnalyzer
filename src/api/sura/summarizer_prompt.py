"""
Prompt template for SURA clinical document summarization.

This module provides the prompt template used to instruct Gemini
for clinical document analysis and chronological summarization.
"""


def build_clinical_summary_prompt(
    focus: str | None = None, filenames: list[str] | None = None
) -> str:
    """
    Build the clinical summarization prompt for Gemini.

    Args:
        focus: Optional user-specified focus area for the summary
        filenames: Optional list of uploaded filenames for source tracking

    Returns:
        Complete prompt string for Gemini
    """

    files_context = ""
    if filenames:
        files_list = "\n".join(
            f'  - Documento {i + 1}: "{name}"' for i, name in enumerate(filenames)
        )
        files_context = f"""
DOCUMENTOS PROPORCIONADOS:
{files_list}
Usa estos nombres exactos en el campo "source_document" de cada evento.
"""

    focus_instruction = ""
    if focus:
        focus_instruction = f"""
ENFOQUE ESPECIAL SOLICITADO POR EL USUARIO:
El usuario ha solicitado que el resumen se enfoque especialmente en: "{focus}"

Debes:
1. Completar la linea de tiempo cronologica completa (NO omitir eventos por el enfoque)
2. Adicionalmente, generar un campo "focus_summary" con un resumen narrativo detallado
   que aborde especificamente el enfoque solicitado
3. En la linea de tiempo, dar mayor detalle a los eventos relacionados con el enfoque
"""

    prompt = f"""ROLE: Eres un analista experto en documentos clinicos especializando en resumir historias clinicas y registros medicos.

TAREA PRINCIPAL:
Analiza TODOS los documentos clinicos proporcionados y genera un resumen cronologico completo de la historia clinica del paciente. Tu objetivo es contar la historia clinica del paciente de forma precisa y ordenada en el tiempo.

{files_context}
{focus_instruction}

INSTRUCCIONES DETALLADAS:

1. EXTRACCION DE EVENTOS:
   - Identifica TODOS los eventos clinicamente relevantes de TODOS los documentos
   - Cada evento debe incluir: fecha, titulo, categoria, descripcion detallada, documento fuente
   - Categorias validas: "diagnosis", "procedure", "medication", "examination", "lab_result", "hospitalization", "other"

2. MANEJO DE FECHAS:
   - Usa formato ISO (YYYY-MM-DD) cuando la fecha exacta este disponible → date_precision: "exact"
   - Si solo hay mes y ano, usa el primer dia del mes (ej: 2024-03-01) → date_precision: "approximate"
   - Si la fecha se infiere del contexto pero no es explicita → date_precision: "approximate"
   - Si no hay fecha disponible → date: "Fecha desconocida", date_precision: "unknown"
   - ORDENA todos los eventos cronologicamente (los de fecha desconocida al final)

3. PRECISION Y EXACTITUD:
   - Reporta nombres de medicamentos y dosis EXACTAMENTE como aparecen en los documentos
   - Reporta nombres de procedimientos EXACTAMENTE como aparecen
   - Reporta resultados de examenes con sus valores numericos cuando esten disponibles
   - NUNCA inventes, inferir o fabricar informacion clinica que no este en los documentos
   - Si hay informacion ambigua, indicalo en la descripcion

4. DETALLES RELEVANTES:
   - Para medicamentos: incluir dosis, frecuencia, via de administracion
   - Para examenes: incluir valores, rangos de referencia si estan disponibles
   - Para procedimientos: incluir hallazgos, resultados, complicaciones
   - Para diagnosticos: incluir criterios utilizados, gravedad, estadio

5. INFORMACION DEL PACIENTE:
   - Extrae nombre, edad, numero de identificacion si estan disponibles
   - Identifica las condiciones/diagnosticos principales del paciente

6. IDIOMA:
   - Detecta el idioma principal de los documentos
   - Genera TODO el resumen en el MISMO idioma de los documentos
   - Reporta el codigo de idioma en "document_language" (ej: "es" para espanol, "en" para ingles)

7. OBSERVACIONES GENERALES:
   - Incluye un parrafo de observaciones generales sobre el caso
   - Menciona patrones relevantes, progresion de la enfermedad, respuesta a tratamientos
   - NO hagas recomendaciones medicas, solo describe lo observado en los documentos

8. CONFIANZA:
   - Asigna un confidence_score basado en:
     * Legibilidad de los documentos
     * Completitud de la informacion
     * Claridad de las fechas y eventos
   - 0.9-1.0: Documentos claros, completos, fechas exactas
   - 0.7-0.8: Documentos mayormente legibles, algunas fechas aproximadas
   - 0.5-0.6: Documentos parcialmente legibles, varias fechas faltantes
   - <0.5: Documentos dificiles de leer, informacion muy incompleta

Responde UNICAMENTE con el JSON estructurado segun el esquema proporcionado."""

    return prompt
