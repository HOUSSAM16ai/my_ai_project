from fastapi import FastAPI, HTTPException
from microservices.auditor_service.src.schemas import ReviewRequest, ReviewResponse, ConsultRequest, ConsultResponse
from microservices.auditor_service.src.core import AuditorService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuditorService")

app = FastAPI(title="Auditor Microservice", version="1.0.0")

# Singleton Service
auditor_service = AuditorService()

@app.post("/review", response_model=ReviewResponse)
async def review_work(request: ReviewRequest):
    """
    Review the work result or plan.
    """
    try:
        return await auditor_service.review_work(request)
    except Exception as e:
        logger.error(f"Error in review_work: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post("/consult", response_model=ConsultResponse)
async def consult(request: ConsultRequest):
    """
    Provide consultation.
    """
    try:
        return await auditor_service.consult(request)
    except Exception as e:
        logger.error(f"Error in consult: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "auditor"}
