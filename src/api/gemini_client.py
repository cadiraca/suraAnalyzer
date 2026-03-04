"""Gemini client wrapper for SAP AI Core integration."""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from gen_ai_hub.proxy.native.google_vertexai.clients import GenerativeModel
from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
from vertexai.generative_models import GenerationConfig
from config.settings import get_settings
from src.api.utils import (
    encode_pdf_to_base64, 
    get_file_info, 
    encode_file_to_base64,
    validate_file_for_analysis,
    get_default_prompt_for_file_type
)


logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Wrapper class for Gemini model integration with SAP AI Core.
    
    This class provides a simplified interface for interacting with Gemini models
    through the SAP Generative AI Hub SDK.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the Gemini client.
        
        Args:
            model_name: Name of the Gemini model to use. If None, uses default from settings.
        """
        self.settings = get_settings()
        self.model_name = model_name or self.settings.model_name
        
        # Initialize proxy client
        self._proxy_client = None
        self._model = None
        
        # Setup logging
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
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content using Gemini model.
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Additional parameters for generation
            
        Returns:
            Generated text content
        """
        try:
            content = [{
                "role": "user",
                "parts": [{"text": prompt}]
            }]
            
            # Merge settings with kwargs
            generation_config = {
                "max_output_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature),
            }
            
            response = self.model.generate_content(
                content,
                generation_config=generation_config
            )
            
            logger.info(f"Successfully generated content for prompt: {prompt[:50]}...")
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    def start_chat(self, system_instruction: Optional[str] = None, 
                   enable_function_calling: bool = False) -> Any:
        """
        Start a chat session with the Gemini model.
        
        Args:
            system_instruction: Optional system instruction for the chat
            enable_function_calling: Whether to enable automatic function calling
            
        Returns:
            Chat session object
        """
        try:
            kwargs = {}
            if enable_function_calling:
                kwargs['enable_automatic_function_calling'] = True
            
            chat = self.model.start_chat(**kwargs)
            logger.info("Started new chat session")
            return chat
            
        except Exception as e:
            logger.error(f"Error starting chat: {e}")
            raise
    
    def chat_with_functions(self, message: str, tools: List[Callable], 
                          chat_session: Optional[Any] = None) -> str:
        """
        Send a message to chat with function calling enabled.
        
        Args:
            message: Message to send
            tools: List of functions available as tools
            chat_session: Existing chat session, or None to create new one
            
        Returns:
            Response from the model
        """
        try:
            if chat_session is None:
                chat_session = self.start_chat(enable_function_calling=True)
            
            response = chat_session.send_message(message, tools=tools)
            logger.info(f"Sent message with function calling: {message[:50]}...")
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in chat with functions: {e}")
            raise
    
    def get_chat_history(self, chat_session: Any) -> List[Dict[str, Any]]:
        """
        Get the history of a chat session.
        
        Args:
            chat_session: Chat session object
            
        Returns:
            List of chat history entries
        """
        try:
            history = []
            for content in chat_session.history:
                part = content.parts[0]
                history.append({
                    "role": content.role,
                    "content": type(part).to_dict(part)
                })
            return history
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            raise
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate if a URL is properly formatted and accessible.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL appears valid, False otherwise
        """
        # Basic URL validation regex
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    def analyze_pdf(self, pdf_path: str, prompt: str = None, **kwargs) -> str:
        """
        Analyze a PDF document using Gemini model with multimodal input.
        
        Args:
            pdf_path: Path to the PDF file
            prompt: Custom prompt for analysis. If None, uses default descriptive prompt
            **kwargs: Additional parameters for generation
            
        Returns:
            Analysis/description of the PDF content
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF file is too large
            IOError: If there's an error reading the file
        """
        # Default prompt if none provided
        if prompt is None:
            prompt = (
                "Please provide a comprehensive analysis of this PDF document. "
                "Include details about:\n"
                "1. Document type and purpose\n"
                "2. Key content and information\n"
                "3. Structure and layout\n"
                "4. Any tables, charts, or visual elements\n"
                "5. Important data or findings\n"
                "6. Overall summary"
            )
        
        try:
            # Get file info for logging
            file_info = get_file_info(pdf_path)
            logger.info(f"Analyzing PDF: {file_info}")
            
            # Encode PDF to base64
            base64_pdf = encode_pdf_to_base64(pdf_path)
            
            # Create multimodal content structure
            content = [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "application/pdf",
                            "data": base64_pdf
                        }
                    }
                ]
            }]
            
            # Merge settings with kwargs
            generation_config = {
                "max_output_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature),
            }
            
            # Generate content with multimodal input
            response = self.model.generate_content(
                content,
                generation_config=generation_config
            )
            
            logger.info(f"Successfully analyzed PDF: {pdf_path}")
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing PDF {pdf_path}: {e}")
            raise
    
    def analyze_pdf_from_url(self, pdf_url: str, prompt: str = None, **kwargs) -> str:
        """
        Analyze a PDF document from a URL using Gemini model with fileData.
        
        This method uses fileData instead of inlineData, which is more efficient for 
        PDFs accessible via HTTP/HTTPS URLs or Google Cloud Storage URIs.
        
        Args:
            pdf_url: HTTP/HTTPS URL or Cloud Storage URI (gs://) of the PDF file
                    Must be publicly accessible for HTTP URLs
            prompt: Custom prompt for analysis. If None, uses default descriptive prompt
            **kwargs: Additional parameters for generation
            
        Returns:
            Analysis/description of the PDF content
            
        Raises:
            ValueError: If URL format is invalid
            Exception: If there's an error during analysis
        """
        # Default prompt if none provided
        if prompt is None:
            prompt = (
                "Please provide a comprehensive analysis of this PDF document. "
                "Include details about:\n"
                "1. Document type and purpose\n"
                "2. Key content and information\n"
                "3. Structure and layout\n"
                "4. Any tables, charts, or visual elements\n"
                "5. Important data or findings\n"
                "6. Overall summary"
            )
        
        try:
            # Validate URL format
            if not (pdf_url.startswith(('http://', 'https://')) or pdf_url.startswith('gs://')):
                raise ValueError(f"Invalid URL format. Must start with http://, https://, or gs://")
            
            # Additional validation for HTTP/HTTPS URLs
            if pdf_url.startswith(('http://', 'https://')) and not self._validate_url(pdf_url):
                raise ValueError(f"Invalid HTTP URL format: {pdf_url}")
            
            logger.info(f"Analyzing PDF from URL: {pdf_url}")
            
            # Create multimodal content structure using fileData
            content = [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "fileData": {
                            "mimeType": "application/pdf",
                            "fileUri": pdf_url
                        }
                    }
                ]
            }]
            
            # Merge settings with kwargs
            generation_config = {
                "max_output_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature),
            }
            
            # Generate content with multimodal input
            response = self.model.generate_content(
                content,
                generation_config=generation_config
            )
            
            logger.info(f"Successfully analyzed PDF from URL: {pdf_url}")
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing PDF from URL {pdf_url}: {e}")
            raise

    def analyze_pdf_with_custom_prompt(self, pdf_path: str, custom_prompt: str, **kwargs) -> str:
        """
        Analyze a PDF with a completely custom prompt.
        
        Args:
            pdf_path: Path to the PDF file
            custom_prompt: Custom analysis prompt
            **kwargs: Additional parameters for generation
            
        Returns:
            Response based on the custom prompt
        """
        return self.analyze_pdf(pdf_path, prompt=custom_prompt, **kwargs)
    
    def analyze_pdf_from_url_with_custom_prompt(self, pdf_url: str, custom_prompt: str, **kwargs) -> str:
        """
        Analyze a PDF from URL with a completely custom prompt.
        
        Args:
            pdf_url: HTTP/HTTPS URL or Cloud Storage URI of the PDF file
            custom_prompt: Custom analysis prompt
            **kwargs: Additional parameters for generation
            
        Returns:
            Response based on the custom prompt
        """
        return self.analyze_pdf_from_url(pdf_url, prompt=custom_prompt, **kwargs)
    
    def analyze_file(self, file_path: str, mime_type: Optional[str] = None, 
                    prompt: Optional[str] = None, response_mime_type: Optional[str] = None,
                    response_schema: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        Analyze any supported file type using Gemini model with multimodal input.
        
        Args:
            file_path: Path to the file
            mime_type: MIME type (optional, will be detected if not provided)
            prompt: Custom prompt for analysis. If None, uses default for file type
            response_mime_type: Output format (e.g., "application/json" for structured output)
            response_schema: Schema for structured output (requires response_mime_type)
            **kwargs: Additional parameters for generation
            
        Returns:
            Analysis of the file content
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported or file is too large
            IOError: If there's an error reading the file
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
            
            # Create generation config with structured output support
            generation_config_params = {
                "max_output_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature)
            }
            
            # Add structured output parameters if provided
            if response_mime_type:
                generation_config_params["response_mime_type"] = response_mime_type
                logger.info(f"Using structured output with MIME type: {response_mime_type}")
                
            if response_schema:
                generation_config_params["response_schema"] = response_schema
                logger.info("Using response schema for structured output")
            
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
    
    async def analyze_file_stream(self, file_path: str, mime_type: Optional[str] = None,
                                 prompt: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        """
        Analyze any supported file type with streaming response.
        
        Args:
            file_path: Path to the file
            mime_type: MIME type (optional, will be detected if not provided)
            prompt: Custom prompt for analysis. If None, uses default for file type
            **kwargs: Additional parameters for generation
            
        Yields:
            Text chunks as they arrive from Gemini
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported or file is too large
            IOError: If there's an error reading the file
        """
        try:
            # Validate file
            validation = validate_file_for_analysis(file_path, mime_type)
            if not validation['valid']:
                raise ValueError(f"File validation failed: {', '.join(validation['errors'])}")
            
            mime_type = validation['mime_type']
            file_type = validation['file_type']
            
            logger.info(f"[STREAMING] Starting async streaming analysis of {file_type} file: {file_path} ({validation['size_mb']}MB)")
            
            # Use custom prompt or default for file type
            if prompt is None:
                prompt = get_default_prompt_for_file_type(file_type)
            
            logger.info(f"[STREAMING] Using prompt: {prompt[:100]}...")
            
            # Encode file to base64
            base64_data = encode_file_to_base64(file_path, mime_type)
            logger.info(f"[STREAMING] File encoded to base64, size: {len(base64_data)} characters")
            
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
            
            # Get generation parameters
            max_tokens = kwargs.get("max_tokens", self.settings.max_tokens)
            temperature = kwargs.get("temperature", self.settings.temperature)
            
            logger.info(f"[STREAMING] Generation config - max_tokens: {max_tokens}, temperature: {temperature}")
            
            # Create generation config
            generation_config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            # Generate content with streaming enabled
            logger.info("[STREAMING] Starting Gemini stream generation...")
            stream = self.model.generate_content(
                content,
                generation_config=generation_config,
                stream=True  # Enable streaming
            )
            
            # Yield chunks as they arrive with async iteration
            chunk_count = 0
            for chunk in stream:
                if chunk.text:
                    chunk_count += 1
                    logger.info(f"[STREAMING] Yielding chunk #{chunk_count}, length: {len(chunk.text)} characters")
                    yield chunk.text
                    # Yield control back to event loop for real-time streaming
                    await asyncio.sleep(0)
            
            logger.info(f"[STREAMING] Successfully completed streaming analysis of {file_type} file: {file_path} (total chunks: {chunk_count})")
            
        except Exception as e:
            logger.error(f"[STREAMING] Error in streaming analysis of file {file_path}: {e}")
            raise
    
    async def generate_content_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Generate content with streaming response.
        
        Args:
            prompt: Text prompt for generation
            **kwargs: Additional parameters for generation
            
        Yields:
            Text chunks as they arrive from Gemini
        """
        try:
            content = [{
                "role": "user",
                "parts": [{"text": prompt}]
            }]
            
            # Get generation parameters
            max_tokens = kwargs.get("max_tokens", self.settings.max_tokens)
            temperature = kwargs.get("temperature", self.settings.temperature)
            
            logger.info(f"[TEXT_STREAMING] Starting text generation stream for prompt: {prompt[:50]}...")
            logger.info(f"[TEXT_STREAMING] Generation config - max_tokens: {max_tokens}, temperature: {temperature}")
            
            # Create generation config
            generation_config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            # Generate content with streaming enabled
            stream = self.model.generate_content(
                content,
                generation_config=generation_config,
                stream=True  # Enable streaming
            )
            
            # Yield chunks as they arrive with async iteration
            chunk_count = 0
            for chunk in stream:
                if chunk.text:
                    chunk_count += 1
                    logger.info(f"[TEXT_STREAMING] Yielding text chunk #{chunk_count}, length: {len(chunk.text)} characters")
                    yield chunk.text
                    # Yield control back to event loop for real-time streaming
                    await asyncio.sleep(0)
            
            logger.info(f"[TEXT_STREAMING] Successfully completed streaming generation for prompt: {prompt[:50]}... (total chunks: {chunk_count})")
            
        except Exception as e:
            logger.error(f"[TEXT_STREAMING] Error in streaming generation: {e}")
            raise
    
    def is_healthy(self) -> bool:
        """
        Check if the client connection is healthy.
        
        Returns:
            True if client is healthy, False otherwise
        """
        try:
            # Simple health check with minimal content generation
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
    
    def analyze_multiple_files_structured(
        self,
        file_parts: List[Dict[str, Any]],
        prompt: str,
        response_schema: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Analyze multiple files with structured JSON output.
        
        This method is designed for analyzing multiple files at once with
        a guaranteed JSON response structure, perfect for complex analysis
        tasks like eligibility assessment.
        
        Args:
            file_parts: List of file parts with inline_data format:
                       [{"inline_data": {"mime_type": "...", "data": "base64..."}}]
            prompt: Analysis prompt/instructions
            response_schema: JSON schema for structured output
            **kwargs: Additional generation parameters (max_tokens, temperature)
            
        Returns:
            Structured JSON response as string
            
        Raises:
            ValueError: If file_parts is empty or invalid
            Exception: If analysis fails
        """
        try:
            if not file_parts:
                raise ValueError("file_parts cannot be empty")
            
            # Build content with prompt + all file parts
            content = [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    *file_parts
                ]
            }]
            
            # Create generation config with structured output support
            # Using the same pattern as analyze_file method
            generation_config_params = {
                "max_output_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature)
            }
            
            # Add structured output parameters
            generation_config_params["response_mime_type"] = "application/json"
            generation_config_params["response_schema"] = response_schema
            logger.info(f"Using structured output with MIME type: application/json")
            logger.info("Using response schema for structured output")
            
            # Instantiate GenerationConfig object (same as analyze_file)
            generation_config = GenerationConfig(**generation_config_params)
            
            logger.info(f"Analyzing {len(file_parts)} file(s) with structured JSON output")
            
            # Generate content with structured output
            response = self.model.generate_content(
                content,
                generation_config=generation_config
            )
            
            logger.info(f"Successfully completed multi-file structured analysis ({len(response.text)} chars)")
            return response.text
            
        except Exception as e:
            logger.error(f"Error in multi-file structured analysis: {e}")
            raise
    
    async def analyze_multiple_files_structured_stream(
        self,
        file_parts: List[Dict[str, Any]],
        prompt: str,
        response_schema: Dict[str, Any],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Analyze multiple files with structured JSON output using streaming.
        
        This method streams the analysis response in real-time while ensuring
        the final output conforms to the provided JSON schema.
        
        Args:
            file_parts: List of file parts with inline_data format:
                       [{"inline_data": {"mime_type": "...", "data": "base64..."}}]
            prompt: Analysis prompt/instructions
            response_schema: JSON schema for structured output
            **kwargs: Additional generation parameters (max_tokens, temperature)
            
        Yields:
            Text chunks as they arrive from Gemini
            
        Raises:
            ValueError: If file_parts is empty or invalid
            Exception: If analysis fails
        """
        try:
            if not file_parts:
                raise ValueError("file_parts cannot be empty")
            
            logger.info(f"[STREAMING] Starting multi-file structured streaming analysis for {len(file_parts)} file(s)")
            
            # Build content with prompt + all file parts
            content = [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    *file_parts
                ]
            }]
            
            # Create generation config with structured output support
            generation_config_params = {
                "max_output_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "temperature": kwargs.get("temperature", self.settings.temperature)
            }
            
            # Add structured output parameters
            generation_config_params["response_mime_type"] = "application/json"
            generation_config_params["response_schema"] = response_schema
            logger.info(f"[STREAMING] Using structured output with MIME type: application/json")
            logger.info("[STREAMING] Using response schema for structured output")
            
            # Instantiate GenerationConfig object
            generation_config = GenerationConfig(**generation_config_params)
            
            # Generate content with streaming enabled
            logger.info("[STREAMING] Starting Gemini stream generation for multi-file structured analysis...")
            stream = self.model.generate_content(
                content,
                generation_config=generation_config,
                stream=True  # Enable streaming
            )
            
            # Yield chunks as they arrive with async iteration
            chunk_count = 0
            for chunk in stream:
                if chunk.text:
                    chunk_count += 1
                    logger.info(f"[STREAMING] Yielding structured chunk #{chunk_count}, length: {len(chunk.text)} characters")
                    yield chunk.text
                    # Yield control back to event loop for real-time streaming
                    await asyncio.sleep(0)
            
            logger.info(f"[STREAMING] Successfully completed multi-file structured streaming analysis (total chunks: {chunk_count})")
            
        except Exception as e:
            logger.error(f"[STREAMING] Error in multi-file structured streaming analysis: {e}")
            raise
    
    def reset_connection(self):
        """Reset client connections for error recovery."""
        logger.info("Resetting client connections")
        self._proxy_client = None
        self._model = None
