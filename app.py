import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import text

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
    description="A production-ready FastAPI backend for hospital appointment booking and queries.",
    version="1.0.0"
)

# Include routers with v1 API version prefix
app.include_router(doctor_router, prefix="/api/v1", tags=["Doctors"])
app.include_router(booking_router, prefix="/api/v1", tags=["Bookings"])

@app.get("/api/v1/system-info")
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
        }
    }

@app.get("/health")
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
        }
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

