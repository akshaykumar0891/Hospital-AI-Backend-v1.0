import logging
from fastapi import FastAPI
from routes.doctor_routes import router as doctor_router
from routes.booking_routes import router as booking_router

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hospital AI Appointment Manager",
    description="A production-ready FastAPI backend for hospital appointment booking and queries.",
    version="1.0.0"
)

# Include routers with v1 API version prefix
app.include_router(doctor_router, prefix="/api/v1", tags=["Doctors"])
app.include_router(booking_router, prefix="/api/v1", tags=["Bookings"])

@app.get("/api/v1/system-info")
def system_info():
    """System information endpoint."""
    import os
    env = os.getenv("ENVIRONMENT", "development")
    return {
        "success": True,
        "message": "System info retrieved successfully",
        "data": {
            "service": "Hospital AI Backend",
            "version": "1.0.0",
            "status": "running",
            "database": "Excel",
            "environment": env
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint to verify database connectivity and app status."""
    import os
    from config import EXCEL_DB_PATH
    db_connected = "disconnected"
    if os.path.exists(EXCEL_DB_PATH):
        db_connected = "connected"
        
    return {
        "success": True,
        "message": "Hospital AI backend is healthy",
        "data": {
            "status": "healthy",
            "database": db_connected,
            "version": "1.0.0"
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
