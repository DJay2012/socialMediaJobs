# Advanced Response Class - Complete Guide

## Overview

The advanced `Response` class is a comprehensive, versatile response handling system that can be used for HTTP responses, service responses, API responses, database responses, and any other type of response in your application.

## Key Features

### ✨ **Core Features**
- **Universal compatibility** - Works with HTTP, service, API, database, and custom responses
- **Rich metadata support** - Store additional information with responses
- **Automatic logging** - Configurable logging based on response status
- **JSON serialization** - Easy conversion to JSON for APIs
- **Response chaining** - Boolean evaluation for conditional logic
- **Performance tracking** - Built-in duration tracking
- **Error accumulation** - Collect multiple errors and warnings
- **Type safety** - Full type hints for better IDE support

### 📊 **Response Types**
- `HTTP` - Web requests and API calls
- `SERVICE` - Internal service responses
- `API` - External API responses
- `DATABASE` - Database operation responses
- `FILE` - File operation responses
- `NETWORK` - Network operation responses
- `VALIDATION` - Data validation responses
- `AUTHENTICATION` - Auth-related responses
- `AUTHORIZATION` - Permission-related responses
- `BUSINESS_LOGIC` - Business rule responses
- `EXTERNAL_SERVICE` - Third-party service responses
- `SYSTEM` - System-level responses

### 🎯 **Response Statuses**
- `SUCCESS` - Operation completed successfully
- `ERROR` - Operation failed
- `WARNING` - Operation completed with warnings
- `INFO` - Informational response
- `PARTIAL_SUCCESS` - Operation partially completed
- `TIMEOUT` - Operation timed out
- `CANCELLED` - Operation was cancelled
- `PENDING` - Operation is pending

## Quick Start

### Basic Usage

```python
from classes.Response import Response, ResponseStatus, ResponseType

# Simple success response
response = Response.success(
    message="Data retrieved successfully",
    data={"users": [{"id": 1, "name": "John"}]}
)

# Simple error response
response = Response.error(
    message="Database connection failed",
    status_code=500
)

# Check response status
if response.is_success:
    print("Success!")
    data = response.data
else:
    print(f"Error: {response.message}")
```

### Advanced Usage

```python
# Create detailed response with metadata
response = Response(
    status_code=200,
    message="User profile updated",
    data={"user_id": 123, "updated_fields": ["name", "email"]},
    status=ResponseStatus.SUCCESS,
    response_type=ResponseType.SERVICE,
    metadata={
        "execution_time": 45.2,
        "cache_updated": True,
        "affected_records": 1
    },
    request_id="req-12345",
    duration_ms=45.2,
    source="UserService"
)
```

## Class Methods (Factory Methods)

### Success Responses
```python
# Basic success
Response.success(message="Operation completed", data={"result": True})

# Success with custom status code
Response.success(message="Created", data={"id": 123}, status_code=201)
```

### Error Responses
```python
# Basic error
Response.error(message="Something went wrong", status_code=500)

# Error with details
Response.error(
    message="Validation failed",
    errors=[
        {"field": "email", "message": "Invalid format", "code": "INVALID_EMAIL"},
        {"field": "age", "message": "Must be positive", "code": "INVALID_AGE"}
    ],
    status_code=400
)
```

### HTTP-Specific Responses
```python
# 404 Not Found
Response.not_found(message="User not found")

# 401 Unauthorized
Response.unauthorized(message="Invalid API key")

# 403 Forbidden
Response.forbidden(message="Access denied")

# 400 Validation Error
Response.validation_error(
    message="Invalid input",
    errors=[{"field": "name", "message": "Required"}]
)

# 408 Timeout
Response.timeout(message="Request timeout")
```

## Instance Methods

### Adding Data
```python
response = Response.success("Initial response")

# Add errors
response.add_error("Something went wrong", "ERROR_CODE")
response.add_error({"message": "Custom error", "details": "More info"})

# Add warnings
response.add_warning("This feature is deprecated")

# Add metadata
response.add_metadata("cache_hit", True)
response.add_metadata("processing_time", 150.5)

# Add headers (for HTTP responses)
response.add_header("X-Request-ID", "12345")
response.add_header("Content-Type", "application/json")
```

### Checking Response State
```python
# Status checks
if response.is_success:
    print("Success!")

if response.is_error:
    print("Error occurred")

if response.is_warning:
    print("Warning present")

# Data checks
if response.has_data:
    print(f"Data: {response.data}")

if response.has_errors:
    for error in response.errors:
        print(f"Error: {error}")

if response.has_warnings:
    for warning in response.warnings:
        print(f"Warning: {warning}")

# Boolean evaluation
if response:  # True if success, False if error
    print("Response is successful")
```

## Serialization

### Convert to Dictionary
```python
response_dict = response.to_dict()
# Returns complete response as dictionary
```

### Convert to JSON
```python
json_string = response.to_json()
# Returns JSON string

# Pretty printed JSON
json_pretty = response.to_json(indent=2)
```

### HTTP-Compatible Format
```python
http_format = response.to_http_dict()
# Returns: {
#   "status_code": 200,
#   "body": {...},
#   "headers": {...}
# }
```

## Working with HTTP Responses

### From requests.Response
```python
import requests

# Make HTTP request
http_resp = requests.get("https://api.example.com/users")

# Convert to Response object
response = Response.from_http_response(
    http_resp,
    message="User data retrieved"
)

# Now you can use all Response features
if response.is_success:
    users = response.data
```

## Use Cases and Examples

### 1. API Endpoint Response
```python
def get_user(user_id: int) -> Response:
    try:
        # Database query
        user = database.get_user(user_id)
        
        if not user:
            return Response.not_found(
                message=f"User {user_id} not found",
                response_type=ResponseType.DATABASE
            )
        
        return Response.success(
            message="User retrieved successfully",
            data=user,
            response_type=ResponseType.DATABASE
        )
        
    except DatabaseError as e:
        return Response.error(
            message="Database error occurred",
            errors=[{"code": "DB_ERROR", "message": str(e)}],
            status_code=500,
            response_type=ResponseType.DATABASE
        )
```

### 2. Service Layer Response
```python
def process_payment(amount: float, card_token: str) -> Response:
    # Validation
    if amount <= 0:
        return Response.validation_error(
            message="Invalid payment amount",
            errors=[{"field": "amount", "message": "Must be positive"}]
        )
    
    try:
        # Process payment
        result = payment_gateway.charge(amount, card_token)
        
        return Response.success(
            message="Payment processed successfully",
            data={
                "transaction_id": result.id,
                "amount": amount,
                "status": "completed"
            },
            response_type=ResponseType.EXTERNAL_SERVICE,
            metadata={
                "gateway": "stripe",
                "processing_fee": result.fee
            }
        )
        
    except PaymentError as e:
        return Response.error(
            message="Payment failed",
            errors=[{"code": e.code, "message": str(e)}],
            response_type=ResponseType.EXTERNAL_SERVICE
        )
```

### 3. File Operation Response
```python
def save_file(file_path: str, content: bytes) -> Response:
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return Response.success(
            message="File saved successfully",
            data={"path": file_path, "size": len(content)},
            response_type=ResponseType.FILE
        )
        
    except PermissionError:
        return Response.forbidden(
            message="Permission denied to write file",
            response_type=ResponseType.FILE
        )
        
    except IOError as e:
        return Response.error(
            message="File operation failed",
            errors=[{"code": "IO_ERROR", "message": str(e)}],
            response_type=ResponseType.FILE
        )
```

### 4. Batch Operation Response
```python
def process_batch(items: list) -> Response:
    results = []
    errors = []
    warnings = []
    
    for item in items:
        try:
            result = process_item(item)
            results.append(result)
        except ValidationError as e:
            errors.append({
                "item_id": item.id,
                "error": str(e),
                "code": "VALIDATION_ERROR"
            })
        except Exception as e:
            warnings.append(f"Item {item.id} processing failed: {str(e)}")
    
    # Determine overall status
    if errors and not results:
        status = ResponseStatus.ERROR
        message = "Batch processing failed completely"
    elif errors and results:
        status = ResponseStatus.PARTIAL_SUCCESS
        message = f"Batch processing partially successful: {len(results)}/{len(items)} items processed"
    elif warnings:
        status = ResponseStatus.WARNING
        message = "Batch processing completed with warnings"
    else:
        status = ResponseStatus.SUCCESS
        message = "Batch processing completed successfully"
    
    return Response(
        status_code=200 if results else 500,
        message=message,
        data={"processed": results, "total_items": len(items)},
        errors=errors,
        warnings=warnings,
        status=status,
        response_type=ResponseType.BUSINESS_LOGIC
    )
```

## Integration Examples

### Flask/FastAPI Integration
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/users/<int:user_id>')
def get_user_endpoint(user_id):
    response = get_user(user_id)  # Returns our Response object
    
    if response.is_success:
        return jsonify(response.to_dict()), response.status_code
    else:
        return jsonify(response.to_dict()), response.status_code

# FastAPI
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get('/users/{user_id}')
def get_user_endpoint(user_id: int):
    response = get_user(user_id)
    
    if response.is_success:
        return response.to_dict()
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.to_dict()
        )
```

### Custom Response Wrapper
```python
class APIResponse:
    """Wrapper for consistent API responses"""
    
    @staticmethod
    def wrap(response: Response):
        """Wrap Response for API consumption"""
        return {
            "success": response.is_success,
            "message": response.message,
            "data": response.data,
            "errors": response.errors,
            "warnings": response.warnings,
            "timestamp": response.timestamp.isoformat(),
            "request_id": response.request_id
        }
```

## Best Practices

### 1. Consistent Status Codes
```python
# Use standard HTTP status codes
SUCCESS = 200        # OK
CREATED = 201        # Created
BAD_REQUEST = 400    # Client error
UNAUTHORIZED = 401   # Authentication required
FORBIDDEN = 403      # Permission denied
NOT_FOUND = 404      # Resource not found
INTERNAL_ERROR = 500 # Server error
```

### 2. Structured Error Messages
```python
# Good: Structured error with code
Response.error(
    message="Validation failed",
    errors=[{
        "field": "email",
        "message": "Invalid email format",
        "code": "INVALID_EMAIL_FORMAT"
    }]
)

# Avoid: Unstructured error
Response.error(message="Error: Invalid email format for field email")
```

### 3. Use Appropriate Response Types
```python
# Database operations
Response.success(data=users, response_type=ResponseType.DATABASE)

# External API calls
Response.success(data=api_data, response_type=ResponseType.EXTERNAL_SERVICE)

# Validation errors
Response.validation_error(errors=validation_errors)
```

### 4. Include Performance Metrics
```python
import time

start_time = time.time()
# ... perform operation ...
duration = (time.time() - start_time) * 1000

Response.success(
    message="Operation completed",
    data=result,
    duration_ms=duration,
    metadata={"cache_hit": False, "db_queries": 3}
)
```

## Testing

Run the test suite:
```bash
python test_response.py
```

Run usage examples:
```bash
python examples/response_usage.py
```

## Migration from Old Response Class

### Old Usage
```python
# Old simple response
response = Response(
    status_code=200,
    detail="Success",
    response_type=ResponseType.SUCCESS
)
```

### New Usage
```python
# New advanced response
response = Response.success(
    message="Success",  # Changed from 'detail' to 'message'
    data=result_data    # Now supports structured data
)
```

The new Response class is backward compatible for basic usage, but offers much more functionality and flexibility for advanced use cases.

## Conclusion

The advanced Response class provides a unified, comprehensive way to handle all types of responses in your application. It offers:

- **Consistency** across different response types
- **Rich metadata** for debugging and monitoring  
- **Type safety** with full type hints
- **Flexibility** for various use cases
- **Performance tracking** built-in
- **Easy serialization** for APIs
- **Automatic logging** for monitoring

Use this Response class throughout your application for consistent, professional response handling!
