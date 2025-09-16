"""
Advanced Response Class for handling various types of responses
Supports HTTP responses, service responses, API responses, and more
"""

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from log.logging import logger


class ResponseStatus(Enum):
    """Response status types"""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    PARTIAL_SUCCESS = "partial_success"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PENDING = "pending"


class ResponseType(Enum):
    """Response type categories"""

    HTTP = "http"
    SERVICE = "service"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    NETWORK = "network"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"


class ResponseLevel(Enum):
    """Log levels for response messages"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Response:
    """
    Advanced Response class for handling various types of responses

    Features:
    - HTTP response compatibility
    - Service response handling
    - Rich metadata support
    - Automatic logging
    - JSON serialization
    - Response chaining
    - Performance tracking
    - Error details and stack traces
    """

    def __init__(
        self,
        status_code: int = 200,
        message: str = "Success",
        data: Any = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        warnings: Optional[List[str]] = None,
        status: ResponseStatus = ResponseStatus.SUCCESS,
        response_type: ResponseType = ResponseType.SERVICE,
        metadata: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        duration_ms: Optional[float] = None,
        source: Optional[str] = None,
        log_level: ResponseLevel = ResponseLevel.INFO,
        auto_log: bool = True,
        **kwargs,
    ):
        """
        Initialize an advanced response object

        Args:
            status_code: HTTP-style status code (200, 404, 500, etc.)
            message: Human-readable message
            data: Response payload/data
            errors: List of error details
            warnings: List of warning messages
            status: Response status enum
            response_type: Type of response (HTTP, Service, etc.)
            metadata: Additional metadata
            headers: Response headers (for HTTP responses)
            request_id: Unique request identifier
            timestamp: Response timestamp
            duration_ms: Request duration in milliseconds
            source: Source of the response
            log_level: Logging level
            auto_log: Whether to automatically log the response
            **kwargs: Additional custom fields
        """
        self.status_code = status_code
        self.message = message
        self.data = data
        self.errors = errors or []
        self.warnings = warnings or []
        self.status = status
        self.response_type = response_type
        self.metadata = metadata or {}
        self.headers = headers or {}
        self.request_id = request_id
        self.timestamp = timestamp or datetime.utcnow()
        self.duration_ms = duration_ms
        self.source = source
        self.log_level = log_level

        # Add any additional custom fields
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Auto-logging
        if auto_log:
            self._log_response()

    def _log_response(self):
        """Log the response based on its status and level"""
        log_message = (
            f"[{self.response_type.value.upper()}] {self.status_code} - {self.message}"
        )

        if self.request_id:
            log_message = f"[{self.request_id}] {log_message}"

        if self.duration_ms:
            log_message += f" ({self.duration_ms:.2f}ms)"

        if self.source:
            log_message += f" from {self.source}"

        # Log based on status and level
        if self.status == ResponseStatus.SUCCESS:
            logger.success(log_message)

        elif self.status == ResponseStatus.ERROR:
            logger.error(log_message)
            if self.errors:
                for error in self.errors:
                    logger.error(f"  Error: {error}")

        elif self.status == ResponseStatus.WARNING:
            logger.warning(log_message)

        else:
            getattr(logger, self.log_level.value, logger.info)(log_message)

    @property
    def is_success(self) -> bool:
        """Check if response indicates success"""
        return self.status in [ResponseStatus.SUCCESS, ResponseStatus.PARTIAL_SUCCESS]

    @property
    def is_error(self) -> bool:
        """Check if response indicates error"""
        return self.status == ResponseStatus.ERROR

    @property
    def is_warning(self) -> bool:
        """Check if response indicates warning"""
        return self.status == ResponseStatus.WARNING

    @property
    def has_data(self) -> bool:
        """Check if response has data"""
        return self.data is not None

    @property
    def has_errors(self) -> bool:
        """Check if response has errors"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if response has warnings"""
        return len(self.warnings) > 0

    def add_error(self, error: Union[str, Dict[str, Any]], code: Optional[str] = None):
        """Add an error to the response"""
        if isinstance(error, str):
            error_dict = {"message": error, "code": code or "UNKNOWN_ERROR"}
        else:
            error_dict = error

        self.errors.append(error_dict)
        if self.status == ResponseStatus.SUCCESS:
            self.status = ResponseStatus.ERROR

    def add_warning(self, warning: str):
        """Add a warning to the response"""
        self.warnings.append(warning)
        if self.status == ResponseStatus.SUCCESS:
            self.status = ResponseStatus.WARNING

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the response"""
        self.metadata[key] = value

    def add_header(self, key: str, value: str):
        """Add header to the response"""
        self.headers[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        result = {
            "status_code": self.status_code,
            "message": self.message,
            "status": self.status.value,
            "response_type": self.response_type.value,
            "timestamp": self.timestamp.isoformat(),
            "success": self.is_success,
        }

        if self.data is not None:
            result["data"] = self.data

        if self.errors:
            result["errors"] = self.errors

        if self.warnings:
            result["warnings"] = self.warnings

        if self.metadata:
            result["metadata"] = self.metadata

        if self.headers:
            result["headers"] = self.headers

        if self.request_id:
            result["request_id"] = self.request_id

        if self.duration_ms:
            result["duration_ms"] = self.duration_ms

        if self.source:
            result["source"] = self.source

        return result

    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert response to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_http_dict(self) -> Dict[str, Any]:
        """Convert to HTTP-compatible dictionary"""
        return {
            "status_code": self.status_code,
            "body": {
                "message": self.message,
                "data": self.data,
                "errors": self.errors,
                "warnings": self.warnings,
                "success": self.is_success,
                "timestamp": self.timestamp.isoformat(),
            },
            "headers": self.headers,
        }

    def __str__(self) -> str:
        """String representation of the response"""
        return f"Response({self.status_code}, {self.status.value}, {self.message})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return (
            f"Response(status_code={self.status_code}, status={self.status.value}, "
            f"message='{self.message}', type={self.response_type.value})"
        )

    def __bool__(self) -> bool:
        """Boolean evaluation - True if success, False if error"""
        return self.is_success

    @classmethod
    def success(
        cls,
        message: str = "Success",
        data: Any = None,
        status_code: int = 200,
        **kwargs,
    ) -> "Response":
        """Create a success response"""
        return cls(
            status_code=status_code,
            message=message,
            data=data,
            status=ResponseStatus.SUCCESS,
            **kwargs,
        )

    @classmethod
    def error(
        cls,
        message: str = "Error",
        errors: Optional[List[Dict[str, Any]]] = None,
        status_code: int = 500,
        **kwargs,
    ) -> "Response":
        """Create an error response"""
        return cls(
            status_code=status_code,
            message=message,
            errors=errors or [],
            status=ResponseStatus.ERROR,
            log_level=ResponseLevel.ERROR,
            **kwargs,
        )

    @classmethod
    def warning(
        cls,
        message: str = "Warning",
        warnings: Optional[List[str]] = None,
        status_code: int = 200,
        **kwargs,
    ) -> "Response":
        """Create a warning response"""
        return cls(
            status_code=status_code,
            message=message,
            warnings=warnings or [],
            status=ResponseStatus.WARNING,
            log_level=ResponseLevel.WARNING,
            **kwargs,
        )

    @classmethod
    def not_found(cls, message: str = "Resource not found", **kwargs) -> "Response":
        """Create a not found response"""
        return cls.error(message=message, status_code=404, **kwargs)

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized access", **kwargs) -> "Response":
        """Create an unauthorized response"""
        return cls.error(
            message=message,
            status_code=401,
            response_type=ResponseType.AUTHENTICATION,
            **kwargs,
        )

    @classmethod
    def forbidden(cls, message: str = "Access forbidden", **kwargs) -> "Response":
        """Create a forbidden response"""
        return cls.error(
            message=message,
            status_code=403,
            response_type=ResponseType.AUTHORIZATION,
            **kwargs,
        )

    @classmethod
    def validation_error(
        cls,
        message: str = "Validation failed",
        errors: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> "Response":
        """Create a validation error response"""
        return cls.error(
            message=message,
            errors=errors,
            status_code=400,
            response_type=ResponseType.VALIDATION,
            **kwargs,
        )

    @classmethod
    def timeout(cls, message: str = "Request timeout", **kwargs) -> "Response":
        """Create a timeout response"""
        return cls(
            status_code=408,
            message=message,
            status=ResponseStatus.TIMEOUT,
            log_level=ResponseLevel.WARNING,
            **kwargs,
        )

    @classmethod
    def from_http_response(
        cls, http_response: Any, message: Optional[str] = None
    ) -> "Response":
        """Create Response from HTTP response object (requests.Response, etc.)"""
        try:
            status_code = getattr(http_response, "status_code", 200)

            # Try to extract JSON data
            data = None
            try:
                if hasattr(http_response, "json"):
                    data = http_response.json()
                elif hasattr(http_response, "text"):
                    import json

                    data = json.loads(http_response.text)
            except:
                if hasattr(http_response, "text"):
                    data = http_response.text
                elif hasattr(http_response, "content"):
                    data = http_response.content

            # Extract headers
            headers = {}
            if hasattr(http_response, "headers"):
                headers = dict(http_response.headers)

            # Determine status
            if 200 <= status_code < 300:
                status = ResponseStatus.SUCCESS
            elif 400 <= status_code < 500:
                status = ResponseStatus.ERROR
            elif status_code >= 500:
                status = ResponseStatus.ERROR
            else:
                status = ResponseStatus.INFO

            return cls(
                status_code=status_code,
                message=message or f"HTTP {status_code}",
                data=data,
                status=status,
                response_type=ResponseType.HTTP,
                headers=headers,
                auto_log=False,
            )
        except Exception as e:
            return cls.error(
                message=f"Failed to parse HTTP response: {str(e)}", status_code=500
            )
