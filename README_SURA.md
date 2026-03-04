# SURA Healthcare Eligibility Analyzer - Backend

## Overview

The SURA Healthcare Eligibility Analyzer is an AI-powered system that automates the auditing of patient eligibility for healthcare services. It uses **FastAPI** + **SAP BTP** + **Vertex AI Gemini** to analyze medical records (PDFs and images) and determine eligibility based on contract-specific criteria.

### Key Features

✅ **Single-Pass AI Analysis** - One API call processes everything  
✅ **Multi-Contract Support** - Different criteria for different services  
✅ **Real-time SSE Streaming** - Live progress updates  
✅ **Natural Language Criteria** - No complex rule engines  
✅ **Structured JSON Output** - Guaranteed response format  
✅ **Multi-File Support** - Analyze PDFs and images together  

---

## Architecture

```
User uploads files + selects contract
         ↓
Backend loads contract JSON (instructions + schema)
         ↓
ONE Gemini API call with:
  - All files (base64)
  - Eligibility instructions (natural language)
  - Response schema (JSON structure)
         ↓
Gemini returns structured JSON:
  - patient_data
  - eligibility_decision
  - criteria_matrix[]
  - observations
  - confidence_score
         ↓
Stream to frontend via SSE
```

---

## Setup

### Prerequisites

- Python 3.9+
- SAP BTP account with AI Core enabled
- Access to SAP Generative AI Hub
- Service key for AI Core

### Installation

1. **Clone the repository**
```bash
cd pySURAnalyzer
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your SAP BTP credentials
```

### Required Environment Variables

```env
# SAP AI Core Configuration
AICORE_AUTH_URL=https://your-auth-url.authentication.sap.hana.ondemand.com
AICORE_CLIENT_ID=your-client-id
AICORE_CLIENT_SECRET=your-client-secret
AICORE_BASE_URL=https://api.ai.prod.us-east-1.aws.ml.hana.ondemand.com
AICORE_RESOURCE_GROUP=default

# Gemini Model
MODEL_NAME=gemini-1.5-flash
MAX_TOKENS=4096
TEMPERATURE=0.3

# SURA API Keys
SURA_INTERNAL_KEYS=sura_internal_key_001,sura_internal_key_002

# Application
LOG_LEVEL=INFO
```

---

## Running the Application

### Development Mode

```bash
uvicorn src.main_api:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn src.main_api:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## API Endpoints

### 1. List Available Contracts

**GET** `/api/v1/sura/contracts`

**Headers:**
```
X-SURA-API-Key: sura_internal_key_001
```

**Response:**
```json
{
  "contracts": [
    {
      "contract_id": "litotripsia_ureteral",
      "contract_name": "Litotricia Intracorpórea con Láser",
      "description": "Análisis de elegibilidad para servicio de litotricia ureteral con láser",
      "version": "1.0",
      "active": true,
      "default": true
    }
  ],
  "total": 1
}
```

### 2. Analyze Eligibility (SSE Streaming)

**POST** `/api/v1/sura/analyze-eligibility`

**Headers:**
```
X-SURA-API-Key: sura_internal_key_001
Accept: text/event-stream
```

**Form Data:**
```
files: File[] (multiple PDFs/images)
contract_id: string (optional, defaults to litotripsia_ureteral)
```

**Response (Server-Sent Events):**

```
event: init
data: {"message":"Iniciando análisis...","contract_id":"litotripsia_ureteral",...}

event: analyzing
data: {"message":"Validando archivos...","progress":20}

event: analyzing
data: {"message":"Analizando documentos con IA...","progress":50}

event: result
data: {"result":{"patient_data":{...},"eligibility_decision":"ELIGIBLE",...}}

event: complete
data: {"message":"✅ Análisis completado","processing_time_seconds":4.2}
```

---

## Example Usage

### Using cURL

```bash
# List contracts
curl -X GET "http://localhost:8000/api/v1/sura/contracts" \
  -H "X-SURA-API-Key: sura_internal_key_001"

# Analyze eligibility (default contract)
curl -X POST "http://localhost:8000/api/v1/sura/analyze-eligibility" \
  -H "X-SURA-API-Key: sura_internal_key_001" \
  -H "Accept: text/event-stream" \
  -F "files=@historia_clinica.pdf" \
  -F "files=@autorizacion.pdf" \
  -F "files=@carnet.jpg" \
  --no-buffer

# Analyze with specific contract
curl -X POST "http://localhost:8000/api/v1/sura/analyze-eligibility" \
  -H "X-SURA-API-Key: sura_internal_key_001" \
  -H "Accept: text/event-stream" \
  -F "files=@documento.pdf" \
  -F "contract_id=cirugia_cardiaca" \
  --no-buffer
```

### Using Python

```python
import requests

# List contracts
response = requests.get(
    "http://localhost:8000/api/v1/sura/contracts",
    headers={"X-SURA-API-Key": "sura_internal_key_001"}
)
contracts = response.json()
print(contracts)

# Analyze eligibility with SSE
files = {
    'files': [
        open('historia_clinica.pdf', 'rb'),
        open('autorizacion.pdf', 'rb')
    ]
}

response = requests.post(
    "http://localhost:8000/api/v1/sura/analyze-eligibility",
    headers={
        "X-SURA-API-Key": "sura_internal_key_001",
        "Accept": "text/event-stream"
    },
    files=files,
    stream=True
)

# Process SSE events
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

---

## Contract Configuration

Contracts are defined in `config/contracts/` as JSON files.

### Contract Structure

```json
{
  "contract_id": "litotripsia_ureteral",
  "contract_name": "Litotricia Intracorpórea con Láser",
  "description": "Análisis de elegibilidad...",
  "version": "1.0",
  "active": true,
  "default": true,
  "eligibility_instructions": "Natural language criteria...",
  "response_schema": {
    "type": "object",
    "properties": {...}
  }
}
```

### Adding a New Contract

1. Create a new JSON file in `config/contracts/`
2. Follow the structure above
3. Define eligibility criteria in natural language
4. Specify the JSON response schema
5. Restart the application

---

## Response Format

### Eligibility Response

```json
{
  "patient_data": {
    "name": "Juan Pérez",
    "age": 45,
    "patient_id": "12345678",
    "insurance_plan": "PBS",
    "has_poliza": false
  },
  "eligibility_decision": "ELIGIBLE",
  "criteria_matrix": [
    {
      "criterion": "Edad",
      "requirement": "≥18 años",
      "patient_value": "45 años",
      "status": "✓ CUMPLE",
      "justification": "El paciente tiene 45 años..."
    },
    {
      "criterion": "Tipo de Plan",
      "requirement": "PBS o PGP sin póliza Sura activa",
      "patient_value": "PBS sin póliza",
      "status": "✓ CUMPLE",
      "justification": "El paciente tiene plan PBS..."
    }
  ],
  "observations": "Análisis completo: El paciente cumple con todos los criterios...",
  "confidence_score": 0.95,
  "missing_fields": []
}
```

### Eligibility Decisions

- **ELIGIBLE**: Patient meets all criteria
- **NOT_ELIGIBLE**: Patient fails one or more criteria
- **INSUFFICIENT_INFORMATION**: Missing critical data

---

## Project Structure

```
pySURAnalyzer/
├── config/
│   ├── contracts/
│   │   └── litotripsia_ureteral.json
│   └── settings.py
├── src/
│   ├── main_api.py
│   ├── client_manager.py
│   ├── gemini_client.py
│   ├── utils.py
│   └── api/
│       └── sura/
│           ├── __init__.py
│           ├── models.py
│           ├── contract_loader.py
│           ├── auth.py
│           └── routes.py
├── .env.example
├── README_SURA.md
└── requirements.txt
```

---

## Security

### API Key Authentication

- API keys are validated via `X-SURA-API-Key` header
- Multiple keys supported (comma-separated in env)
- Keys stored in environment variables, not code

### Best Practices

1. **Never commit .env file** to version control
2. **Rotate API keys regularly**
3. **Use HTTPS in production**
4. **Configure CORS appropriately**
5. **Implement rate limiting** for production

---

## Troubleshooting

### Common Issues

**1. "Contract file not found"**
- Ensure contract JSON exists in `config/contracts/`
- Check contract_id matches filename

**2. "API key is required"**
- Add `X-SURA-API-Key` header to request
- Verify key is in `SURA_INTERNAL_KEYS` env variable

**3. "Failed to initialize client"**
- Check SAP BTP credentials in .env
- Verify network connectivity to SAP services

**4. "File validation failed"**
- Ensure files are PDFs or images (PNG, JPG)
- Check file size < 20MB

---

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "model": "gemini-1.5-flash",
  "client_healthy": true
}
```

### Logs

Application logs include:
- Contract loading
- File processing
- Gemini API calls
- Analysis results
- Errors and warnings

---

## Contributing

When adding new contracts:

1. Define clear, natural language criteria
2. Specify complete response schema
3. Test with sample documents
4. Update documentation

---

## License

Internal SURA Healthcare use only.

---

## Support

For issues or questions, contact the development team.
