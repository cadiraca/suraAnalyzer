# SURA HC Eligibility Analyzer - Implementation Plan

## Project Overview

**Goal**: Build an automated eligibility auditing system for SURA Healthcare's ureteral laser lithotripsy service using FastAPI + SAP BTP + Vertex AI Gemini.

**Key Features**:
- Multi-file upload support (PDFs and images)
- Real-time SSE streaming for progress updates
- JSON-based configurable eligibility criteria
- "Insufficient information" handling
- Simple API key authentication for internal use
- React frontend matching provided UX design

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                SURA HC Eligibility Analyzer                 │
│                    (Single-Pass AI-Native)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (React/Next.js)                                   │
│  ├─ Contract Selector Dropdown (Type Selector)             │
│  ├─ Multi-file Upload (Drag & Drop)                        │
│  ├─ Real-time SSE Progress Display                         │
│  ├─ Eligibility Matrix Panel (criteria_matrix)             │
│  ├─ Observations Panel (observations)                      │
│  └─ Decision Badge (eligibility_decision)                  │
│                          ↓                                   │
│  FastAPI Backend API                                        │
│  ├─ API Key Authentication                                 │
│  ├─ GET /api/v1/sura/contracts (list contracts)           │
│  ├─ POST /api/v1/sura/analyze-eligibility (SSE)           │
│  │   Input: files[] + contract_id                          │
│  │   ├─ Load contract configuration                        │
│  │   ├─ Encode files to base64                             │
│  │   └─ Single Gemini API call                             │
│  └─ Response: Structured JSON via response_schema          │
│                          ↓                                   │
│  Gemini Client (via SAP BTP)                               │
│  └─ ONE CALL: files + instructions + response_schema       │
│      ├─ Analyzes all documents                             │
│      ├─ Extracts patient data                              │
│      ├─ Evaluates all criteria                             │
│      └─ Returns structured JSON (guaranteed format)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Architecture Principle: **Single-Pass Processing**

Unlike traditional multi-stage approaches, this system sends everything to Gemini in **one API call**:
- All files (as base64 inline data)
- Contract eligibility instructions (natural language)
- Response schema (JSON structure)

Gemini processes everything and returns a **guaranteed structured JSON** response that maps directly to the frontend panels.
# SURA HC Eligibility Analyzer - Implementation Plan

## Project Overview

**Goal**: Build an automated eligibility auditing system for SURA Healthcare's ureteral laser lithotripsy service using FastAPI + SAP BTP + Vertex AI Gemini.

**Key Features**:
- Multi-file upload support (PDFs and images)
- Real-time SSE streaming for progress updates
- JSON-based configurable eligibility criteria
- "Insufficient information" handling
- Simple API key authentication for internal use
- React frontend matching provided UX design

---


---

## Implementation Phases

### Phase 1: Backend Core (2-3 days)

#### 1.1 Configuration & Models
- [ ] Create `config/sura_eligibility_criteria.json`
- [ ] Define Pydantic models in `src/api/sura/models.py`:
  - `EligibilityCriteria`
  - `PatientData`
  - `CriterionEvaluation`
  - `EligibilityDecision`
  - `AnalysisResponse`

#### 1.2 Criteria Evaluation Engine
- [ ] Implement `src/api/sura/criteria_engine.py`:
  - `load_criteria()` - Load JSON config
  - `evaluate_criterion()` - Check single criterion
  - `evaluate_all_criteria()` - Check all criteria
  - `calculate_confidence()` - Confidence scoring
  - `check_missing_fields()` - Identify missing data

#### 1.3 AI Prompts
- [ ] Create `src/api/sura/prompts.py`:
  - Document classification prompt
  - Patient data extraction prompt
  - Service details extraction prompt
  - Insurance information extraction prompt
  - Eligibility evaluation prompt

#### 1.4 Main Endpoint
- [ ] Implement `src/api/sura/routes.py`:
  - `POST /api/v1/sura/analyze-eligibility` with SSE streaming
  - File validation
  - Multi-file processing
  - Real-time progress events
  - "Insufficient information" handling

#### 1.5 Authentication
- [ ] Implement `src/api/sura/auth.py`:
  - Simple API key validation
  - Add to `config/settings.py`

---

### Phase 2: Frontend UX (2-3 days)

#### 2.1 Core Components
- [ ] `components/FileUploader.tsx`:
  - Drag & drop interface
  - Multiple file support
  - File type validation (PDF, PNG, JPG)
  - Preview thumbnails

#### 2.2 Progress Display
- [ ] `components/SSEProgressBar.tsx`:
  - Real-time SSE connection
  - Progress percentage
  - Status messages
  - File processing indicators

#### 2.3 Results Visualization
- [ ] `components/EligibilityMatrix.tsx`:
  - Display all criteria evaluations
  - Color-coded compliance status
  - Requirement vs. Patient Value comparison

- [ ] `components/PatientDataCard.tsx`:
  - Display extracted patient information
  - Confidence scores
  - Missing fields indicators

- [ ] `components/DecisionSummary.tsx`:
  - Final eligibility status (ELIGIBLE/NOT ELIGIBLE/INSUFFICIENT_INFORMATION)
  - Reasoning explanation
  - Recommended actions
  - Disclaimer

#### 2.4 Custom Hook
- [ ] `hooks/useEligibilityAnalysis.ts`:
  - SSE connection management
  - Event parsing
  - State management
  - Error handling

---

### Phase 3: Testing & Polish (1-2 days)

#### 3.1 Testing
- [ ] Unit tests for criteria engine
- [ ] Integration tests for API endpoint
- [ ] Test with sample medical records
- [ ] Edge cases:
  - Missing critical information
  - Unclear/illegible documents
  - Multiple conflicting documents
  - Non-Spanish documents

#### 3.2 Documentation
- [ ] API documentation
- [ ] Frontend component documentation
- [ ] Deployment guide
- [ ] User manual

#### 3.3 Deployment
- [ ] Environment setup
- [ ] Configuration management
- [ ] Deployment to SAP BTP or local server

---

## Technical Specifications

### Backend API

**Endpoint**: `POST /api/v1/sura/analyze-eligibility`

**Headers**:
```
X-SURA-API-Key: sura_internal_key_001
Accept: text/event-stream
```

**Request Body** (multipart/form-data):
```
files[]: File[] (multiple PDFs/images)
```

**Response** (SSE Events):
```
event: init
event: file_upload
event: file_processing
event: extraction
event: extraction_result
event: criteria_check
event: criteria_result
event: decision
event: complete
event: error (if applicable)
```

### SSE Event Data Structures

**Progress Event**:
```json
{
  "phase": "extraction|evaluation|decision",
  "message": "Extrayendo datos del paciente...",
  "progress": 50
}
```

**Extraction Result**:
```json
{
  "field": "age",
  "value": 45,
  "confidence": 0.95,
  "source": "historia_clinica.pdf"
}
```

**Criteria Result**:
```json
{
  "criterion_id": "age",
  "criterion_name": "Edad",
  "status": "COMPLIANT|NON_COMPLIANT|UNKNOWN",
  "patient_value": "45 años",
  "requirement": "≥18 años",
  "complies": true
}
```

**Final Decision**:
```json
{
  "eligibility_status": "ELIGIBLE|NOT_ELIGIBLE|INSUFFICIENT_INFORMATION",
  "confidence_score": 0.92,
  "all_criteria_met": true,
  "reasoning": "El paciente cumple con todos los criterios...",
  "missing_fields": [],
  "recommended_actions": [],
  "disclaimer": "⚠️ IMPORTANTE: Esta es una auditoría contractual automatizada..."
}
```

---

## File Structure

```
pySURAnalyzer/
├── config/
│   ├── sura_eligibility_criteria.json    # Criteria configuration
│   └── settings.py                        # Environment settings
├── src/
│   ├── main_api.py                        # FastAPI app entry point
│   ├── client_manager.py                  # Gemini client singleton
│   ├── gemini_client.py                   # AI client wrapper
│   ├── utils.py                           # File utilities
│   └── api/
│       ├── routes.py                      # General routes
│       ├── models.py                      # General Pydantic models
│       └── sura/
│           ├── __init__.py
│           ├── routes.py                  # SURA eligibility endpoint
│           ├── models.py                  # SURA-specific models
│           ├── prompts.py                 # AI prompts
│           ├── criteria_engine.py         # Criteria evaluation logic
│           └── auth.py                    # API key authentication
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUploader.tsx
│   │   │   ├── SSEProgressBar.tsx
│   │   │   ├── EligibilityMatrix.tsx
│   │   │   ├── PatientDataCard.tsx
│   │   │   └── DecisionSummary.tsx
│   │   ├── hooks/
│   │   │   └── useEligibilityAnalysis.ts
│   │   └── pages/
│   │       └── eligibility-analyzer.tsx
│   └── package.json
├── tests/
│   └── test_sura_eligibility.py
├── IMPLEMENTATION_PLAN.md                  # This file
├── PROGRESS_TRACKER.md                     # Progress tracking
└── README.md
```

---

## Key Design Decisions

### 1. Single-Pass AI-Native Architecture
- **Why**: Leverage Gemini's native multimodal and reasoning capabilities
- **How**: Send all files + instructions in one call, receive structured JSON
- **Benefits**: Simpler code, faster processing, context-aware analysis, no extraction pipeline needed

### 2. Contract-Based Configuration
- **Why**: Support multiple SURA healthcare contracts with different criteria
- **Location**: `config/contracts/` directory (one JSON per contract)
- **Structure**: Each contract contains:
  - `eligibility_instructions`: Natural language criteria (prompt)
  - `response_schema`: JSON schema for structured output
- **Benefits**: Add new contracts by adding JSON files, no code changes

### 3. Natural Language Criteria (No Meta-Language)
- **Strategy**: Write criteria as clear instructions in Spanish
- **Evaluation**: Gemini interprets and evaluates naturally
- **Benefits**: Human-readable, maintainable, flexible, no complex rule engine

### 4. "Insufficient Information" Handling
- **Strategy**: Gemini identifies missing critical data
- **Response**: `INSUFFICIENT_INFORMATION` status with specific missing fields
- **User Action**: System indicates what documents/data are needed

### 5. Single-Pass Processing
```
Stage 1: File Upload & Contract Selection
  ↓
Stage 2: Single Gemini API Call
  Input:
    - All files (base64 inline)
    - Contract instructions (text)
    - Response schema (JSON)
  Output:
    - patient_data
    - eligibility_decision
    - criteria_matrix[]
    - observations
    - confidence_score
  ↓
Stage 3: Stream to Frontend via SSE
```

---

## Implementation Phases

### Phase 1: Backend Core (2-3 days)

#### 1.1 Configuration & Models
- [ ] Create `config/sura_eligibility_criteria.json`
- [ ] Define Pydantic models in `src/api/sura/models.py`:
  - `EligibilityCriteria`
  - `PatientData`
  - `CriterionEvaluation`
  - `EligibilityDecision`
  - `AnalysisResponse`

#### 1.2 Criteria Evaluation Engine
- [ ] Implement `src/api/sura/criteria_engine.py`:
  - `load_criteria()` - Load JSON config
  - `evaluate_criterion()` - Check single criterion
  - `evaluate_all_criteria()` - Check all criteria
  - `calculate_confidence()` - Confidence scoring
  - `check_missing_fields()` - Identify missing data

#### 1.3 AI Prompts
- [ ] Create `src/api/sura/prompts.py`:
  - Document classification prompt
  - Patient data extraction prompt
  - Service details extraction prompt
  - Insurance information extraction prompt
  - Eligibility evaluation prompt

#### 1.4 Main Endpoint
- [ ] Implement `src/api/sura/routes.py`:
  - `POST /api/v1/sura/analyze-eligibility` with SSE streaming
  - File validation
  - Multi-file processing
  - Real-time progress events
  - "Insufficient information" handling

#### 1.5 Authentication
- [ ] Implement `src/api/sura/auth.py`:
  - Simple API key validation
  - Add to `config/settings.py`

---

### Phase 2: Frontend UX (2-3 days)

#### 2.1 Core Components
- [ ] `components/FileUploader.tsx`:
  - Drag & drop interface
  - Multiple file support
  - File type validation (PDF, PNG, JPG)
  - Preview thumbnails

#### 2.2 Progress Display
- [ ] `components/SSEProgressBar.tsx`:
  - Real-time SSE connection
  - Progress percentage
  - Status messages
  - File processing indicators

#### 2.3 Results Visualization
- [ ] `components/EligibilityMatrix.tsx`:
  - Display all criteria evaluations
  - Color-coded compliance status
  - Requirement vs. Patient Value comparison

- [ ] `components/PatientDataCard.tsx`:
  - Display extracted patient information
  - Confidence scores
  - Missing fields indicators

- [ ] `components/DecisionSummary.tsx`:
  - Final eligibility status (ELIGIBLE/NOT ELIGIBLE/INSUFFICIENT_INFORMATION)
  - Reasoning explanation
  - Recommended actions
  - Disclaimer

#### 2.4 Custom Hook
- [ ] `hooks/useEligibilityAnalysis.ts`:
  - SSE connection management
  - Event parsing
  - State management
  - Error handling

---

### Phase 3: Testing & Polish (1-2 days)

#### 3.1 Testing
- [ ] Unit tests for criteria engine
- [ ] Integration tests for API endpoint
- [ ] Test with sample medical records
- [ ] Edge cases:
  - Missing critical information
  - Unclear/illegible documents
  - Multiple conflicting documents
  - Non-Spanish documents

#### 3.2 Documentation
- [ ] API documentation
- [ ] Frontend component documentation
- [ ] Deployment guide
- [ ] User manual

#### 3.3 Deployment
- [ ] Environment setup
- [ ] Configuration management
- [ ] Deployment to SAP BTP or local server

---

## Technical Specifications

### Backend API

**Endpoint**: `POST /api/v1/sura/analyze-eligibility`

**Headers**:
```
X-SURA-API-Key: sura_internal_key_001
Accept: text/event-stream
```

**Request Body** (multipart/form-data):
```
files[]: File[] (multiple PDFs/images)
```

**Response** (SSE Events):
```
event: init
event: file_upload
event: file_processing
event: extraction
event: extraction_result
event: criteria_check
event: criteria_result
event: decision
event: complete
event: error (if applicable)
```

### SSE Event Data Structures

**Progress Event**:
```json
{
  "phase": "extraction|evaluation|decision",
  "message": "Extrayendo datos del paciente...",
  "progress": 50
}
```

**Extraction Result**:
```json
{
  "field": "age",
  "value": 45,
  "confidence": 0.95,
  "source": "historia_clinica.pdf"
}
```

**Criteria Result**:
```json
{
  "criterion_id": "age",
  "criterion_name": "Edad",
  "status": "COMPLIANT|NON_COMPLIANT|UNKNOWN",
  "patient_value": "45 años",
  "requirement": "≥18 años",
  "complies": true
}
```

**Final Decision**:
```json
{
  "eligibility_status": "ELIGIBLE|NOT_ELIGIBLE|INSUFFICIENT_INFORMATION",
  "confidence_score": 0.92,
  "all_criteria_met": true,
  "reasoning": "El paciente cumple con todos los criterios...",
  "missing_fields": [],
  "recommended_actions": [],
  "disclaimer": "⚠️ IMPORTANTE: Esta es una auditoría contractual automatizada..."
}
```

---

## File Structure

```
pySURAnalyzer/
├── config/
│   ├── sura_eligibility_criteria.json    # Criteria configuration
│   └── settings.py                        # Environment settings
├── src/
│   ├── main_api.py                        # FastAPI app entry point
│   ├── client_manager.py                  # Gemini client singleton
│   ├── gemini_client.py                   # AI client wrapper
│   ├── utils.py                           # File utilities
│   └── api/
│       ├── routes.py                      # General routes
│       ├── models.py                      # General Pydantic models
│       └── sura/
│           ├── __init__.py
│           ├── routes.py                  # SURA eligibility endpoint
│           ├── models.py                  # SURA-specific models
│           ├── prompts.py                 # AI prompts
│           ├── criteria_engine.py         # Criteria evaluation logic
│           └── auth.py                    # API key authentication
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUploader.tsx
│   │   │   ├── SSEProgressBar.tsx
│   │   │   ├── EligibilityMatrix.tsx
│   │   │   ├── PatientDataCard.tsx
│   │   │   └── DecisionSummary.tsx
│   │   ├── hooks/
│   │   │   └── useEligibilityAnalysis.ts
│   │   └── pages/
│   │       └── eligibility-analyzer.tsx
│   └── package.json
├── tests/
│   └── test_sura_eligibility.py
├── IMPLEMENTATION_PLAN.md                  # This file
├── PROGRESS_TRACKER.md                     # Progress tracking
└── README.md
```

---

## Key Design Decisions


### 6. SSE Event Types (Simplified)
- `init` - Analysis start with contract info
- `file_upload` - Files received
- `analyzing` - Gemini processing
- `result` - Complete structured response
- `complete` - Analysis complete
- `error` - Error occurred


### 7. Confidence Scoring
Gemini provides confidence based on:
- Document quality and legibility
- Completeness of information
- Clarity of extracted data

```python
confidence_levels = {
    "high": 0.80 - 1.0,    # Clear decision possible
    "medium": 0.50 - 0.79, # Requires human review
    "low": 0.0 - 0.49      # Insufficient information
}
```


---

## Eligibility Criteria Matrix

| Criterio | Condición | Accede al Servicio? | Observaciones |
|----------|-----------|---------------------|---------------|
| Edad | ≥18 años | ✓ Sí | |
| Tipo de Plan | PBS o PGP sin póliza Sura activa | ✓ Sí | Exclusión si póliza activa |
| Autorización | Tiene autorización antes de póliza | ✓ Sí | Solo aplica si hay póliza |
| Nivel de Atención | Nivel I o II | ✓ Sí | Nivel III es exclusión |
| Ubicación | Área de cobertura | ✓ Sí | Jamundí, Cali, Palmira, Buga, Tuluá, Yumbo |
| Servicio | Litotricia intracorpórea | ✓ Sí | |

**Decision Logic**:
- ALL criteria must be met → ELIGIBLE
- ANY criterion fails → NOT ELIGIBLE
- Missing critical data → INSUFFICIENT_INFORMATION

---

## Sample API Requests

### List Available Contracts
```bash
curl -X GET "http://localhost:8000/api/v1/sura/contracts" \
  -H "X-SURA-API-Key: sura_internal_key_001"
```

### Analyze Eligibility (Default Contract)
```bash
curl -X POST "http://localhost:8000/api/v1/sura/analyze-eligibility" \
  -H "X-SURA-API-Key: sura_internal_key_001" \
  -H "Accept: text/event-stream" \
  -F "files=@historia_clinica.pdf" \
  -F "files=@autorizacion.pdf" \
  -F "files=@carnet.jpg" \
  --no-buffer
```

### Analyze Eligibility (Specific Contract)
```bash
curl -X POST "http://localhost:8000/api/v1/sura/analyze-eligibility" \
  -H "X-SURA-API-Key: sura_internal_key_001" \
  -H "Accept: text/event-stream" \
  -F "files=@historia_clinica.pdf" \
  -F "files=@autorizacion.pdf" \
  -F "contract_id=cirugia_cardiaca" \
  --no-buffer
```

---

## Eligibility Criteria Matrix

| Criterio | Condición | Accede al Servicio? | Observaciones |
|----------|-----------|---------------------|---------------|
| Edad | ≥18 años | ✓ Sí | |
| Tipo de Plan | PBS o PGP sin póliza Sura activa | ✓ Sí | Exclusión si póliza activa |
| Autorización | Tiene autorización antes de póliza | ✓ Sí | Solo aplica si hay póliza |
| Nivel de Atención | Nivel I o II | ✓ Sí | Nivel III es exclusión |
| Ubicación | Área de cobertura | ✓ Sí | Jamundí, Cali, Palmira, Buga, Tuluá, Yumbo |
| Servicio | Litotricia intracorpórea | ✓ Sí | |

**Decision Logic**:
- ALL criteria must be met → ELIGIBLE
- ANY criterion fails → NOT ELIGIBLE
- Missing critical data → INSUFFICIENT_INFORMATION

