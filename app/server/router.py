"""FastAPI router with /solving endpoint."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, field_validator
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from app.utils.config import settings
from app.quiz.solver import solve_quiz
from app.utils.logger import get_logger
from typing import Any

router = APIRouter()
logger = get_logger("router")


class SolveRequest(BaseModel):
    """Request model for solving endpoint."""
    email: str
    secret: str
    url: str  # Accept any string to allow file:// URLs
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email is not empty."""
        if not v or not v.strip():
            raise ValueError("Email cannot be empty")
        return v
    
    @field_validator('secret')
    @classmethod
    def validate_secret(cls, v: str) -> str:
        """Validate secret is not empty."""
        if not v or not v.strip():
            raise ValueError("Secret cannot be empty")
        return v
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v:
            raise ValueError("URL cannot be empty")
        # Allow http, https, and file URLs for testing
        if not (v.startswith('http://') or v.startswith('https://') or v.startswith('file://')):
            raise ValueError("URL must start with http://, https://, or file://")
        return v


@router.post("/solving")
def solving(req: SolveRequest):
    """Endpoint to start solving a quiz at `url`.

    Verifies secret and runs the solver recursively until completion.
    
    Args:
        req: Request containing email, secret, and quiz URL
        
    Returns:
        Final quiz result JSON
        
    Raises:
        HTTPException: 403 if secret is invalid, 400 for bad requests, 500 for server errors
    """
    # Check secret authentication
    if req.secret != settings.SECRET:
        logger.warning("Invalid secret for email=%s", req.email)
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="invalid secret")

    try:
        logger.info(f"Starting quiz solve for {req.url}")
        result = solve_quiz(str(req.url), req.email)
        logger.info(f"Quiz solve completed successfully")
        return result
    except ValueError as e:
        logger.exception("Bad request: %s", e)
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Server error: %s", e)
        # Return more detailed error for debugging
        import traceback
        error_detail = f"internal error: {str(e)}"
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

