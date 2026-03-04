# Gemini SAP App: Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Key Features](#key-features)
5. [API Endpoints](#api-endpoints)
6. [Streaming with SSE](#streaming-with-sse)
7. [Setup and Configuration](#setup-and-configuration)
8. [Usage Examples](#usage-examples)

---

## 1. Overview

The **Gemini SAP Application** is a Python-based solution that bridges **SAP Business Technology Platform (BTP)** with **Google's Vertex AI** to enable advanced, multimodal file analysis. The application's core innovation is its ability to analyze various file formats (PDFs, images, audio, video, documents, and spreadsheets) **without requiring local data extraction or preprocessing**.

### Key Benefits

- **Direct File Processing**: Files are encoded and sent directly to Vertex AI via SAP's Generative AI Hub proxy
- **No Local Extraction**: Unlike traditional approaches, there's no need to extract text or data locally before sending to the AI
- **Real-time Streaming**: Server-Sent Events (SSE) provide live, progressive responses for a rich user experience
- **Multi-format Support**: Handles 20+ file formats including PDFs, images, audio, video, and office documents
- **Specialized Processing**: Built-in invoice extraction for Latin American documents with regional identifier support

### How It Works

```
┌─────────────┐    HTTP/File Upload    ┌──────────────┐    SAP AI Hub Proxy    ┌─────────────┐
│   Client    │ ──────────────────────> │  FastAPI     │ ───────────────────────> │  Vertex AI  │
│ Application │                         │  Backend     │                          │   (Gemini)  │
└─────────────┘ <────────────────────── └──────────────┘ <─────────────────────── └─────────────┘
                   SSE Stream Response         │                    Response
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │   Base64     │
                                         │   Encoding   │
                                         └──────────────┘
```

The application takes advantage of Vertex AI's native multimodal capabilities, sending files as base64-encoded inline data directly to the Gemini models through SAP's managed proxy infrastructure.

---

## 2. Architecture

### System Architecture

```
gemini-sap-app/
├── src/                          # Core application logic
│   ├── main_api.py              # FastAPI application entry point
│   ├── client_manager.py        # Thread-safe singleton for client management
│   ├── gemini_client.py         # Gemini API wrapper with streaming support
│   ├── utils.py                 # File handling utilities
│   └── api/                     # API layer
│       ├── routes.py            # REST endpoints
│       ├── models.py            # Pydantic models
│       ├── invoice_prompts.py   # Invoice extraction prompts
│       ├── invoice_utils.py     # Invoice processing utilities
│       └── funny_messages.py    # UX enhancement messages
├── config/                       # Configuration management
│   └── settings.py              # Application settings
├── examples/                     # Usage examples
└── frontend/                     # React frontend (separate)
```

### Technology Stack

- **Framework**: FastAPI (async web framework)
- **AI Integration**: SAP Generative AI Hub SDK
- **AI Model**: Google Gemini via Vertex AI
- **Streaming**: Server-Sent Events (SSE)
- **Concurrency**: Thread-safe singleton pattern
- **File Handling**: Base64 encoding for multimodal input

---

## 3. Core Components

### 3.1 FastAPI Application (`main_api.py`)

The entry point for the API server, responsible for:
- Application lifecycle management
- CORS configuration
- Route registration
- Global exception handling

#### Key Implementation

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Gemini File Analysis API...")
    client_manager = ClientManager.get_instance()
    
    # Pre-initialize client to establish connections
    try:
        client = client_manager.get_client()
        logger.info(f"Successfully initialized client with model: {client.model_name}")
    except Exception as e:
        logger.error(f"Failed to initialize client on startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gemini File Analysis API...")
    client_manager.shutdown()

# Create FastAPI app
app = FastAPI(
    lifespan=lifespan,
    title="Gemini File Analysis API",
    description="Multi-format file analysis with streaming support via SAP BTP GenAI Hub",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why This Matters**:
- The `lifespan` context manager ensures proper initialization and cleanup of resources
- Pre-initialization of the Gemini client during startup avoids cold start delays
- CORS middleware enables cross-origin requests from frontend applications

---

### 3.2 Client Manager (`client_manager.py`)

A **thread-safe singleton** that manages the `GeminiClient` instance across the application. This is crucial for:
- Avoiding multiple client initializations
- Ensuring connection reuse
- Implementing health checks
- Providing error recovery

#### Implementation Details

```python
class ClientManager:
    """Thread-safe singleton manager for GeminiClient instances."""
    
    _instance: Optional['ClientManager'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._client: Optional[GeminiClient] = None
        self._client_lock = threading.Lock()
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
    
    @classmethod
    def get_instance(cls) -> 'ClientManager':
        """Get singleton instance with double-checked locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.info("Created new ClientManager singleton instance")
        return cls._instance
    
    def get_client(self) -> GeminiClient:
        """Get or create GeminiClient with health check."""
        with self._client_lock:
            current_time = time.time()
            
            # Create client if none exists
            if self._client is None:
                logger.info("Initializing new GeminiClient")
                self._client = GeminiClient()
                self._last_health_check = current_time
                return self._client
            
            # Perform periodic health check
            if current_time - self._last_health_check > self._health_check_interval:
                if self._client.is_healthy():
                    self._last_health_check = current_time
                    logger.debug("Client health check passed")
                else:
                    logger.warning("Client health check failed, recreating client")
                    self._client = GeminiClient()
                    self._last_health_check = current_time
            
            return self._client
```

**Key Features**:
- **Double-Checked Locking**: Ensures only one instance is created even in multi-threaded environments
- **Health Checks**: Automatically validates client health every 5 minutes
- **Auto-Recovery**: Recreates the client if health checks fail
- **Thread Safety**: Uses locks to prevent race conditions

---

### 3.3 Gemini Client (`gemini_client.py`)

The heart of the application. This wrapper class provides a clean interface to interact with Google's Gemini models through SAP's AI Core proxy.

#### Initialization and Lazy Loading

```python
class GeminiClient:
    """
    Wrapper class for Gemini model integration with SAP AI Core.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        self.settings = get_settings()
        self.model_name = model_name or self.settings.model_name
        
        # Lazy initialization
        self._proxy_client = None
        self._model = None
        
        logging.basicConfig(level=getattr(logging, self.settings.log_level))
    
    @property
    def proxy_client(self):
        """Lazy initialization of proxy client."""
        if self._proxy_client is None:
            try:
                self._proxy_client = get_proxy_client('gen-ai-hub')
                logger.info("Successfully initialized SAP AI Core proxy client")
            except Exception as e:
                logger.error(f"Failed to initialize proxy client: {e}")
                raise
        return self._proxy_client
    
    @property
    def model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            try:
                self._model = GenerativeModel(
                    proxy_client=self.proxy_client,
                    model_name=self.model_name
                )
                logger.info(f"Successfully initialized Gemini model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize model: {e}")
                raise
        return self._model
```

**Why Lazy Loading?**
- Connections are only established when actually needed
- Reduces startup time
- Allows for error recovery without restarting the application

#### File Analysis: The Core Innovation

The `analyze_file` method demonstrates how files are processed without local extraction:

```python
def analyze_file(self, file_path: str, mime_type: Optional[str] = None, 
                prompt: Optional[str] = None, response_mime_type: Optional[str] = None,
                response_schema: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    """
    Analyze any supported file type using Gemini model with multimodal input.
    """
    try:
        # Validate file
        validation = validate_file_for_analysis(file_path, mime_type)
        if not validation['valid']:
            raise ValueError(f"File validation failed: {', '.join(validation['errors'])}")
        
        mime_type = validation['mime_type']
        file_type = validation['file_type']
        
        logger.info(f"Analyzing {file_type} file: {file_path} ({validation['size_mb']}MB)")
        
        # Use custom prompt or default for file type
        if prompt is None:
            prompt = get_default_prompt_for_file_type(file_type)
        
        # Encode file to base64 - THIS IS THE KEY!
        base64_data = encode_file_to_base64(file_path, mime_type)
        
        # Create multimodal content structure
        content = [{
            "role": "user",
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data  # File sent as base64
                    }
                }
            ]
        }]
        
        # Create generation config with structured output support
        generation_config_params = {
            "max_output_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
            "temperature": kwargs.get("temperature", self.settings.temperature)
        }
        
        # Add structured output parameters if provided
        if response_mime_type:
            generation_config_params["response_mime_type"] = response_mime_type
                
        if response_schema:
            generation_config_params["response_schema"] = response_schema
        
        generation_config = GenerationConfig(**generation_config_params)
        
        # Generate content with multimodal input
        response = self.model.generate_content(
            content,
            generation_config=generation_config
        )
        
        logger.info(f"Successfully analyzed {file_type} file: {file_path}")
        return response.text
        
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {e}")
        raise
```

**What's Happening Here?**

1. **File Validation**: Checks file exists, is readable, and meets size/format requirements
2. **MIME Type Detection**: Automatically detects file type if not provided
3. **Base64 Encoding**: Converts the entire file to base64 string
4. **Multimodal Request**: Sends both text prompt and file data in a single request
5. **Structured Output**: Optionally requests JSON responses with schemas
6. **Direct Processing**: Vertex AI processes the file natively - no local extraction needed!

#### Streaming Analysis: Real-time Responses

The streaming variant enables progressive responses for better UX:

```python
async def analyze_file_stream(self, file_path: str, mime_type: Optional[str] = None,
                             prompt: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
    """
    Analyze any supported file type with streaming response.
    
    Yields:
        Text chunks as they arrive from Gemini
    """
    try:
        # Validate file
        validation = validate_file_for_analysis(file_path, mime_type)
        if not validation['valid']:
            raise ValueError(f"File validation failed: {', '.join(validation['errors'])}")
        
        mime_type = validation['mime_type']
        file_type = validation['file_type']
        
        logger.info(f"[STREAMING] Starting async streaming analysis of {file_type} file")
        
        # Use custom prompt or default for file type
        if prompt is None:
            prompt = get_default_prompt_for_file_type(file_type)
        
        # Encode file to base64
        base64_data = encode_file_to_base64(file_path, mime_type)
        
        # Create multimodal content structure
        content = [{
            "role": "user",
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data
                    }
                }
            ]
        }]
        
        # Create generation config
        generation_config = GenerationConfig(
            max_output_tokens=kwargs.get("max_tokens", self.settings.max_tokens),
            temperature=kwargs.get("temperature", self.settings.temperature)
        )
        
        # Generate content with streaming enabled
        logger.info("[STREAMING] Starting Gemini stream generation...")
        stream = self.model.generate_content(
            content,
            generation_config=generation_config,
            stream=True  # THIS ENABLES STREAMING!
        )
        
        # Yield chunks as they arrive with async iteration
        chunk_count = 0
        for chunk in stream:
            if chunk.text:
                chunk_count += 1
                logger.info(f"[STREAMING] Yielding chunk #{chunk_count}")
                yield chunk.text
                # Yield control back to event loop for real-time streaming
                await asyncio.sleep(0)
        
        logger.info(f"[STREAMING] Successfully completed streaming analysis")
        
    except Exception as e:
        logger.error(f"[STREAMING] Error in streaming analysis: {e}")
        raise
```

**Streaming Benefits**:
- **Progressive Rendering**: Users see results as they're generated
- **Perceived Performance**: Feels faster even if total time is the same
- **Better UX**: Users know the system is working, reducing abandonment
- **Async/Await**: Non-blocking operations for concurrent requests

---

### 3.4 Utilities (`utils.py`)

Provides essential file handling and validation functions.

#### Base64 Encoding

```python
def encode_file_to_base64(file_path: str, mime_type: Optional[str] = None) -> str:
    """
    Encode any supported file type to base64 string.
    
    This is the key function that enables sending files to Vertex AI
    without local extraction.
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Detect MIME type if not provided
    if mime_type is None:
        mime_type = get_mime_type(file_path)
        if mime_type is None:
            raise ValueError(f"Could not detect MIME type for file: {file_path}")
    
    # Check if MIME type is supported
    if not is_supported_mime_type(mime_type):
        raise ValueError(f"Unsupported MIME type: {mime_type}")
    
    # Check file size
    file_size = os.path.getsize(file_path)
    type_info = get_file_type_info(mime_type)
    max_size = type_info['max_size_mb'] * 1024 * 1024
    
    if file_size > max_size:
        raise ValueError(f"File too large: {file_size} bytes. Max: {max_size} bytes")
    
    try:
        with open(file_path, 'rb') as file:
            file_bytes = file.read()
            base64_string = base64.b64encode(file_bytes).decode('utf-8')
            
        logger.info(f"Successfully encoded {mime_type} file to base64")
        return base64_string
        
    except Exception as e:
        logger.error(f"Error encoding file to base64: {e}")
        raise IOError(f"Failed to read and encode file: {e}")
```

#### Supported File Types

```python
SUPPORTED_MIME_TYPES = {
    # Documents
    'application/pdf': {'type': 'document', 'max_size_mb': 20},
    'text/plain': {'type': 'document', 'max_size_mb': 20},
    'application/msword': {'type': 'document', 'max_size_mb': 20},
    
    # Images
    'image/png': {'type': 'image', 'max_size_mb': 20},
    'image/jpeg': {'type': 'image', 'max_size_mb': 20},
    'image/gif': {'type': 'image', 'max_size_mb': 20},
    'image/webp': {'type': 'image', 'max_size_mb': 20},
    
    # Audio
    'audio/mpeg': {'type': 'audio', 'max_size_mb': 20},
    'audio/wav': {'type': 'audio', 'max_size_mb': 20},
    'audio/mp4': {'type': 'audio', 'max_size_mb': 20},
    'audio/ogg': {'type': 'audio', 'max_size_mb': 20},
    
    # Video
    'video/mp4': {'type': 'video', 'max_size_mb': 20},
    'video/quicktime': {'type': 'video', 'max_size_mb': 20},
    'video/webm': {'type': 'video', 'max_size_mb': 20},
    'video/avi': {'type': 'video', 'max_size_mb': 20},
}
```

#### Smart Default Prompts

```python
def get_default_prompt_for_file_type(file_type: str) -> str:
    """
    Get default analysis prompt based on file type.
    
    Each file type gets an optimized prompt for its content.
    """
    prompts = {
        'document': (
            "Please provide a comprehensive analysis of this document. Include:\n"
            "1. Document type and structure\n"
            "2. Key content and main topics\n"
            "3. Important data, numbers, or findings\n"
            "4. Summary of conclusions or recommendations\n"
            "5. Any notable formatting, tables, or visual elements"
        ),
        'image': (
            "Please analyze this image in detail. Describe:\n"
            "1. Overall scene and context\n"
            "2. Objects, people, and their relationships\n"
            "3. Colors, lighting, and composition\n"
            "4. Any text or written content visible\n"
            "5. Notable details or interesting elements"
        ),
        'audio': (
            "Please analyze this audio file. Provide:\n"
            "1. Transcription of spoken content\n"
            "2. Identification of speakers or voices\n"
            "3. Key topics and main points discussed\n"
            "4. Tone, mood, and context\n"
            "5. Any background sounds or music"
        ),
        # ... more file types
    }
    
    return prompts.get(file_type, prompts['document'])
```

---

## 4. Key Features

### 4.1 Multimodal File Analysis

The application's primary feature is analyzing files without local extraction. Here's what makes it powerful:

**Traditional Approach** (What we DON'T do):
```
1. Upload PDF
2. Extract text locally (PyPDF2, pdfplumber, etc.)
3. Send extracted text to AI
4. Lose formatting, images, tables
```

**Our Approach** (What we DO):
```
1. Upload PDF
2. Encode entire file to base64
3. Send file + prompt to Vertex AI via SAP proxy
4. Gemini natively processes PDF with full fidelity
5. Return comprehensive analysis including tables, images, layout
```

**Benefits**:
- **Full Fidelity**: Preserves all document elements (images, tables, formatting)
- **Simpler Code**: No need for complex extraction libraries
- **Better Results**: AI sees the actual document, not just extracted text
- **Multi-format**: Works with PDFs, images, audio, video, etc.

### 4.2 Structured Output Support

The application supports requesting structured JSON responses:

```python
# Example: Extract invoice data as JSON
response_schema = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string"},
        "date": {"type": "string"},
        "total": {"type": "number"},
        "vendor": {"type": "string"}
    }
}

result = client.analyze_file(
    file_path="invoice.pdf",
    prompt="Extract invoice details",
    response_mime_type="application/json",
    response_schema=response_schema
)

# Result is valid JSON matching the schema!
```

### 4.3 Chat Sessions

Support for multi-turn conversations:

```python
# Start a chat
chat = client.start_chat(
    system_instruction="You are a helpful document analyst"
)

# First message
response1 = chat.send_message("What's in this document?")

# Follow-up questions maintain context
response2 = chat.send_message("What are the key findings?")
response3 = chat.send_message("Summarize in bullet points")
```

### 4.4 Health Monitoring

Built-in health checks ensure reliability:

```python
def is_healthy(self) -> bool:
    """Check if the client connection is healthy."""
    try:
        test_content = [{
            "role": "user",
            "parts": [{"text": "ping"}]
        }]
        
        generation_config = GenerationConfig(
            max_output_tokens=10,
            temperature=0.1
        )
        
        response = self.model.generate_content(
            test_content,
            generation_config=generation_config
        )
        
        return bool(response and response.text)
        
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return False
```

---

## 5. API Endpoints

### 5.1 General File Analysis (Streaming)

**Endpoint**: `POST /api/v1/analyze-file`

**Description**: Analyze any supported file with real-time streaming response.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-file" \
  -H "accept: text/event-stream" \
  -F "file=@document.pdf" \
  -F "prompt=Summarize the key points" \
  -F "temperature=0.7" \
  -F "max_tokens=2048"
```

**Parameters**:
- `file` (required): The file to analyze
- `prompt` (optional): Custom analysis prompt (uses default if not provided)
- `temperature` (optional): Controls randomness (0.0-1.0)
- `max_tokens` (optional): Maximum response length

**Response** (Server-Sent Events):
```
event: status
data: {"status": "Validating file...", "progress": 10}

event: status
data: {"status": "Processing file...", "progress": 30}

event: status
data: {"status": "Starting analysis...", "progress": 50}

event: chunk
data: {"content": "This document appears to be..."}

event: chunk
data: {"content": " a comprehensive report on..."}

event: complete
data: {"message": "Analysis complete", "chunks_sent": 47}
```

### 5.2 Invoice Extraction (Streaming)

**Endpoint**: `POST /api/v1/extract-invoice`

**Description**: Extract structured invoice data with Latin American regional support.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/extract-invoice" \
  -H "accept: text/event-stream" \
  -F "file=@factura.pdf" \
  -F "extract_line_items=true" \
  -F "include_raw_response=false"
```

**Parameters**:
- `file` (required): Invoice file (PDF or image)
- `extract_line_items` (optional): Extract individual line items (default: true)
- `include_raw_response` (optional): Include raw AI response (default: false)

**Response** (Server-Sent Events):
```
event: progress
data: {"phase": "starting", "message": "🚀 Buckle up! We're about to decode this invoice..."}

event: progress
data: {"phase": "analyzing", "message": "🔍 Playing detective with your invoice..."}

event: progress
data: {"phase": "extracting", "message": "💎 Mining those precious invoice details..."}

event: result
data: {
  "invoice_number": "FC-001234",
  "invoice_date": "2023-11-07",
  "due_date": "2023-12-07",
  "vendor": {
    "name": "Acme Corporation",
    "tax_id": "123456789-0",
    "address": "Calle 123 #45-67, Bogotá"
  },
  "customer": {
    "name": "Customer Inc",
    "tax_id": "987654321-0"
  },
  "financial_summary": {
    "subtotal": 1000000,
    "tax_amount": 190000,
    "total_amount": 1190000,
    "currency": "COP"
  },
  "line_items": [
    {
      "description": "Product A",
      "quantity": 10,
      "unit_price": 100000,
      "total": 1000000
    }
  ],
  "regional_identifiers": {
    "country": "Colombia",
    "cufe": "abc123...",
    "electronic_invoice": true
  },
  "metadata": {
    "completeness_score": 0.95,
    "confidence_level": "high",
    "language": "Spanish"
  }
}

event: complete
data: {"message": "✅ Invoice extraction complete!", "processing_time_seconds": 4.2}
```

**Supported Regional Identifiers**:
- 🇨🇴 **Colombia**: CUFE, CUDE codes
- 🇲🇽 **Mexico**: UUID SAT, CFDI versions
- 🇧🇷 **Brazil**: NFe Access Keys
- 🇨🇱 **Chile**: Folio, TED stamps
- 🇦🇷 **Argentina**: CAE codes
- 🇵🇪 **Peru**: CDR receipts

### 5.3 Text Generation (Streaming)

**Endpoint**: `POST /api/v1/analyze-text-stream`

**Description**: Generate text responses with streaming.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-text-stream" \
  -H "accept: text/event-stream" \
  -F "prompt=Explain quantum computing in simple terms"
```

### 5.4 File Validation

**Endpoint**: `POST /api/v1/validate-file`

**Description**: Validate a file before analysis.

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/validate-file" \
  -F "file=@document.pdf"
```

**Response**:
```json
{
  "valid": true,
  "mime_type": "application/pdf",
  "file_type": "document",
  "size_mb": 2.5,
  "errors": []
}
```

### 5.5 Health Check

**Endpoint**: `GET /api/v1/health`

**Description**: Check API health status.

**Response**:
```json
{
  "status": "healthy",
  "model": "gemini-1.5-flash",
  "timestamp": "2023-11-21T20:44:09Z",
  "client_healthy": true
}
```

### 5.6 Supported Formats

**Endpoint**: `GET /api/v1/supported-formats`

**Description**: Get list of supported file formats.

**Response**:
```json
{
  "documents": {
    "formats": ["PDF", "TXT", "DOC", "XLS", "CSV"],
    "mime_types": ["application/pdf", "text/plain", "..."],
    "max_size_mb": 20
  },
  "images": {
    "formats": ["PNG", "JPG", "JPEG", "GIF", "WEBP"],
    "mime_types": ["image/png", "image/jpeg", "..."],
    "max_size_mb": 20
  },
  "audio": {
    "formats": ["MP3", "WAV", "M4A", "OGG"],
    "mime_types": ["audio/mpeg", "audio/wav", "..."],
    "max_size_mb": 20
  },
  "video": {
    "formats": ["MP4", "MOV", "WEBM", "AVI"],
    "mime_types": ["video/mp4", "video/quicktime", "..."],
    "max_size_mb": 20
  }
}
```

---

## 6. Streaming with SSE

### 6.1 What are Server-Sent Events?

Server-Sent Events (SSE) is a standard that allows a server to push updates to clients over HTTP. Unlike WebSockets, SSE is:
- **Unidirectional**: Server → Client only
- **HTTP-based**: Works with existing infrastructure
- **Automatic Reconnection**: Built-in retry logic
- **Simple**: Easy to implement and debug

### 6.2 Why SSE for File Analysis?

File analysis can take several seconds. SSE provides:

1. **Progress Updates**: Show users what's happening
2. **Progressive Results**: Display content as it arrives
3. **Better UX**: Users stay engaged, reducing abandonment
4. **Error Handling**: Gracefully handle and communicate errors

### 6.3 SSE Implementation in Routes

Here's how SSE is implemented in the API routes:

```python
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter()

@router.post("/analyze-file")
async def analyze_file_stream(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    temperature: Optional[float] = Form(0.7),
    max_tokens: Optional[int] = Form(2048)
):
    """
    Analyze uploaded file with streaming response via SSE.
    """
    async def generate_sse_stream():
        try:
            # Step 1: Send status update
            yield f"event: status\ndata: {json.dumps({'status': 'Validating file...', 'progress': 10})}\n\n"
            await asyncio.sleep(0)  # Yield control to event loop
            
            # Validate file
            if not file.filename:
                error_data = {
                    "error": "No filename provided",
                    "error_code": "NO_FILENAME"
                }
                yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
                return
            
            # Save uploaded file temporarily
            temp_file_path = f"/tmp/{file.filename}"
            with open(temp_file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Step 2: Processing status
            yield f"event: status\ndata: {json.dumps({'status': 'Processing file...', 'progress': 30})}\n\n"
            await asyncio.sleep(0)
            
            # Detect MIME type
            mime_type = get_mime_type(temp_file_path)
            if not mime_type:
                error_data = {
                    "error": "Could not detect file type",
                    "error_code": "UNKNOWN_FILE_TYPE"
                }
                yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
                return
            
            # Validate for analysis
            validation = validate_file_for_analysis(temp_file_path, mime_type)
            if not validation['valid']:
                error_data = {
                    "error": f"File validation failed: {', '.join(validation['errors'])}",
                    "error_code": "VALIDATION_FAILED"
                }
                yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
                return
            
            # Step 3: Analysis starting
            yield f"event: status\ndata: {json.dumps({'status': 'Starting analysis...', 'progress': 50})}\n\n"
            await asyncio.sleep(0)
            
            # Get Gemini client
            client = get_gemini_client()
            
            # Step 4: Stream analysis results
            chunk_count = 0
            async for chunk in client.analyze_file_stream(
                file_path=temp_file_path,
                mime_type=mime_type,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                chunk_count += 1
                chunk_data = {"content": chunk}
                yield f"event: chunk\ndata: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0)  # Yield control for real-time streaming
            
            # Step 5: Completion
            complete_data = {
                "message": "Analysis complete",
                "chunks_sent": chunk_count
            }
            yield f"event: complete\ndata: {json.dumps(complete_data)}\n\n"
            
            # Cleanup
            os.remove(temp_file_path)
            
        except Exception as e:
            logger.error(f"Error in streaming analysis: {e}", exc_info=True)
            error_data = {
                "error": str(e),
                "error_code": "ANALYSIS_ERROR"
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )
```

### 6.4 SSE Event Types

The application uses several event types:

1. **`status`**: Progress updates during processing
   ```
   event: status
   data: {"status": "Validating file...", "progress": 10}
   ```

2. **`chunk`**: Analysis content as it arrives
   ```
   event: chunk
   data: {"content": "This document describes..."}
   ```

3. **`error`**: Error information with codes
   ```
   event: error
   data: {"error": "File too large", "error_code": "FILE_TOO_LARGE"}
   ```

4. **`complete`**: Analysis completion
   ```
   event: complete
   data: {"message": "Analysis complete", "chunks_sent": 47}
   ```

5. **`progress`**: Phased progress (invoice extraction)
   ```
   event: progress
   data: {"phase": "analyzing", "message": "🔍 Playing detective..."}
   ```

6. **`result`**: Structured data (invoice extraction)
   ```
   event: result
   data: {"invoice_number": "FC-001234", ...}
   ```

### 6.5 Client-Side SSE Consumption

**JavaScript Example**:

```javascript
// Create EventSource for SSE endpoint
const eventSource = new EventSource('/api/v1/analyze-file');

// Handle different event types
eventSource.addEventListener('status', (event) => {
  const data = JSON.parse(event.data);
  console.log('Status:', data.status);
  updateProgressBar(data.progress);
});

eventSource.addEventListener('chunk', (event) => {
  const data = JSON.parse(event.data);
  appendToResults(data.content);
});

eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  console.error('Error:', data.error);
  showErrorMessage(data.error);
  eventSource.close();
});

eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data);
  console.log('Complete:', data.message);
  eventSource.close();
});

// Handle connection errors
eventSource.onerror = (error) => {
  console.error('Connection error:', error);
  eventSource.close();
};
```

**React Hook Example** (from your frontend):

```typescript
import { useState, useEffect } from 'react';

export const useSSEStream = (url: string, formData: FormData) => {
  const [content, setContent] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    const fetchStream = async () => {
      try {
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
        });

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader!.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('event:')) {
              const eventType = line.slice(6).trim();
              const dataLine = lines[lines.indexOf(line) + 1];
              
              if (dataLine && dataLine.startsWith('data:')) {
                const data = JSON.parse(dataLine.slice(5).trim());

                switch (eventType) {
                  case 'status':
                    setStatus(data.status);
                    break;
                  case 'chunk':
                    setContent(prev => prev + data.content);
                    break;
                  case 'error':
                    setError(data.error);
                    break;
                  case 'complete':
                    setIsComplete(true);
                    break;
                }
              }
            }
          }
        }
      } catch (err) {
        setError(err.message);
      }
    };

    fetchStream();
  }, [url, formData]);

  return { content, status, error, isComplete };
};
```

### 6.6 SSE Benefits for UX

The streaming approach provides several UX benefits:

1. **Immediate Feedback**: Users see progress within milliseconds
2. **Progressive Disclosure**: Content appears as it's generated
3. **Reduced Perceived Latency**: Feels faster than waiting for complete response
4. **Better Error Handling**: Errors communicated immediately, not after timeout
5. **User Engagement**: Users stay on the page, reducing abandonment
6. **Transparency**: Users understand what's happening at each step

**Example User Experience**:

```
[10%] ⏳ Validating file...
[30%] 📄 Processing file...
[50%] 🤖 Starting analysis...
[60%] 📝 This document appears to be a financial report...
[70%] 📝 The key findings include a 15% increase in revenue...
[80%] 📝 Notable risks identified: market volatility and...
[90%] 📝 Recommendations: diversify portfolio, increase...
[100%] ✅ Analysis complete!
```

---

## 7. Setup and Configuration

### 7.1 Prerequisites

- Python 3.9+
- SAP BTP account with AI Core enabled
- Access to SAP Generative AI Hub
- Service key for AI Core

### 7.2 Installation

```bash
# Clone repository
git clone <repository-url>
cd gemini-sap-app

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 7.3 Configuration

Create a `.env` file based on `.env.example`:

```env
# SAP AI Core Configuration
AICORE_AUTH_URL=https://your-auth-url.authentication.sap.hana.ondemand.com
AICORE_CLIENT_ID=your-client-id
AICORE_CLIENT_SECRET=your-client-secret
AICORE_BASE_URL=https://api.ai.prod.us-east-1.aws.ml.hana.ondemand.com
AICORE_RESOURCE_GROUP=default

# Gemini Model Configuration
MODEL_NAME=gemini-1.5-flash
MAX_TOKENS=2048
TEMPERATURE=0.7

# Application Configuration
LOG_LEVEL=INFO
```

### 7.4 Running the Application

```bash
# Development mode with auto-reload
uvicorn src.main_api:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main_api:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7.5 Deployment to SAP BTP

The application includes Cloud Foundry configuration:

```yaml
# manifest.yml
applications:
  - name: gemini-file-analysis
    memory: 512M
    instances: 1
    buildpacks:
      - python_buildpack
    command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main_api:app
    env:
      AICORE_AUTH_URL: ((aicore-auth-url))
      AICORE_CLIENT_ID: ((aicore-client-id))
      AICORE_CLIENT_SECRET: ((aicore-client-secret))
      AICORE_BASE_URL: ((aicore-base-url))
```

Deploy with:

```bash
cf push
```

---

## 8. Usage Examples

### 8.1 Python Client

```python
from src.gemini_client import GeminiClient

# Initialize client
client = GeminiClient()

# Analyze a PDF
result = client.analyze_pdf(
    pdf_path="data/invoice.pdf",
    prompt="Extract key information from this invoice"
)
print(result)

# Analyze an image
result = client.analyze_file(
    file_path="data/chart.png",
    prompt="Describe this chart and its key insights"
)
print(result)

# Stream analysis
import asyncio

async def stream_analysis():
    async for chunk in client.analyze_file_stream(
        file_path="data/report.pdf",
        prompt="Summarize this report"
    ):
        print(chunk, end='', flush=True)

asyncio.run(stream_analysis())
```

### 8.2 cURL Examples

**Analyze PDF with streaming**:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-file" \
  -H "accept: text/event-stream" \
  -F "file=@invoice.pdf" \
  -F "prompt=Extract invoice details" \
  --no-buffer
```

**Extract invoice data**:
```bash
curl -X POST "http://localhost:8000/api/v1/extract-invoice" \
  -H "accept: text/event-stream" \
  -F "file=@factura.pdf" \
  -F "extract_line_items=true" \
  --no-buffer
```

**Analyze image**:
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-file" \
  -H "accept: text/event-stream" \
  -F "file=@chart.png" \
  -F "prompt=Describe this chart" \
  --no-buffer
```

### 8.3 JavaScript/React Example

```typescript
const analyzeFile = async (file: File, prompt: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('prompt', prompt);

  const response = await fetch('/api/v1/analyze-file', {
    method: 'POST',
    body: formData,
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    // Process SSE events
    parseSSEChunk(chunk);
  }
};
```

---

## 9. Advanced Topics

### 9.1 Error Handling

The application implements comprehensive error handling:

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code="HTTP_ERROR"
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.log_level == "DEBUG" else None,
            error_code="INTERNAL_ERROR"
        ).model_dump()
    )
```

### 9.2 Performance Considerations

**Concurrency**:
- FastAPI's async support enables concurrent request handling
- Thread-safe ClientManager prevents connection issues
- Streaming reduces memory usage for large files

**Optimization Tips**:
1. Use connection pooling (handled by SAP SDK)
2. Implement request queuing for high load
3. Cache common prompts/responses
4. Set appropriate max_tokens to reduce costs
5. Use CDN for frontend assets

### 9.3 Security Best Practices

1. **Authentication**: Add API key or OAuth validation
2. **File Validation**: Strict MIME type and size checks
3. **Rate Limiting**: Prevent abuse with rate limiters
4. **Input Sanitization**: Validate all user inputs
5. **CORS Configuration**: Restrict origins in production
6. **Secrets Management**: Use environment variables or SAP BTP services

### 9.4 Monitoring and Logging

```python
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log important events
logger.info(f"Analyzing {file_type} file: {file_path}")
logger.error(f"Error during analysis: {e}", exc_info=True)
logger.warning(f"Health check failed, recreating client")
```

**Key Metrics to Monitor**:
- Request latency
- Error rates by type
- File size distribution
- Model response times
- Client health check failures

---

## 10. Conclusion

The Gemini SAP Application demonstrates a powerful approach to file analysis by:

1. **Direct Integration**: Seamless connection between SAP BTP and Vertex AI
2. **No Local Extraction**: Files processed in their native format with full fidelity
3. **Streaming UX**: Real-time feedback via Server-Sent Events
4. **Multi-format Support**: Handles 20+ file types uniformly
5. **Production-Ready**: Thread-safe, error-resilient, and scalable

This architecture is particularly valuable for:
- **Enterprise Applications**: Leverage existing SAP infrastructure
- **Document Processing**: Maintain formatting and visual elements
- **User Experience**: Progressive rendering and transparency
- **Scalability**: Cloud-native design with managed AI services

The combination of SAP BTP's enterprise capabilities with Google's advanced AI models creates a robust solution for modern document analysis needs.

---

## Resources

- [SAP Generative AI Hub Documentation](https://help.sap.com/docs/sap-ai-core)
- [Google Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Server-Sent Events Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)

---

**Version**: 1.0.0  
**Last Updated**: November 2023  
**Author**: SAP AI Development Team
