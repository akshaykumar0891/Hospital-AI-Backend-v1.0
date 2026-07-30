import logging
import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import text
from config import HOSPITAL_NAME, TIMEZONE, DEFAULT_SLOT_DURATION

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize database tables and seed initial data
from database.database import init_db
logger.info("Initializing database and seeding default data...")
init_db()

from routes.doctor_routes import router as doctor_router
from routes.booking_routes import router as booking_router

app = FastAPI(
    title="Hospital AI Appointment Manager",
    description="A production-ready FastAPI backend for hospital appointment booking and queries. Optimized for Retell AI integration.",
    version="1.0.0"
)

# 1. Enable CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Enable Request Timeout Middleware (10 seconds timeout)
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=10.0)
    except asyncio.TimeoutError:
        logger.error(f"Request timeout exceeded for path: {request.url.path}")
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "message": "Request gateway timeout",
                "errors": ["The server took too long to respond to the request."]
            }
        )

# 3. Global Standard Response Format Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    # If the detail payload already matches our custom success/error structure, return it
    if isinstance(detail, dict) and "success" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    
    # Otherwise wrap standard exception details
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(detail),
            "errors": [str(detail)]
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors_list = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        errors_list.append(f"{loc}: {msg}")
    
    logger.warning(f"Request validation failure on path {request.url.path}: {errors_list}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Input validation failed",
            "errors": errors_list
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error on path {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error occurred",
            "errors": [str(exc)]
        }
    )

# Include routers with v1 API version prefix
app.include_router(doctor_router, prefix="/api/v1", tags=["Doctors"])
app.include_router(booking_router, prefix="/api/v1", tags=["Bookings"])

@app.get(
    "/api/v1/ai-capabilities",
    summary="Get AI receptionist capabilities",
    description="Exposes capabilities configuration metadata to help Retell AI receptionist discover hospital details, departments, and search parameters.",
    response_description="AI capabilities configuration model."
)
def get_ai_capabilities():
    """AI Receptionist discovery and configuration settings endpoint."""
    return {
        "success": True,
        "message": "AI capabilities retrieved successfully",
        "data": {
            "hospital_name": HOSPITAL_NAME,
            "timezone": TIMEZONE,
            "appointment_duration": DEFAULT_SLOT_DURATION,
            "supports_doctor_name": True,
            "supports_department_search": True,
            "available_departments": [
                "Cardiology",
                "Pediatrics",
                "General Medicine"
            ]
        },
        "errors": []
    }

@app.get(
    "/api/v1/system-info",
    summary="Get backend system specifications",
    description="Retrieves operational info about the backend engine.",
    response_description="System specifications payload."
)
def system_info():
    """System information endpoint."""
    env = os.getenv("ENVIRONMENT", "development")
    return {
        "success": True,
        "message": "System info retrieved successfully",
        "data": {
            "service": "Hospital AI Backend",
            "version": "1.0.0",
            "status": "running",
            "database": "PostgreSQL",
            "environment": env
        },
        "errors": []
    }

@app.get(
    "/health",
    summary="Health check validation",
    description="Validates that database connection queries succeed and FastAPI runner works.",
    response_description="Core system state."
)
def health_check():
    """Health check endpoint to verify database connectivity and app status."""
    db_connected = "disconnected"
    try:
        from database.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_connected = "connected"
        db.close()
    except Exception as e:
        logger.error(f"Health check database connection failed: {e}")
        
    return {
        "success": True,
        "message": "Hospital AI backend is healthy",
        "data": {
            "status": "healthy",
            "database": db_connected,
            "version": "1.0.0"
        },
        "errors": []
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
