"""FastAPI application for AI Legal Assistant."""

import logging
import os
import uuid
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form, Request, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from typing import AsyncGenerator

from .core.config import settings
from .agents.contract_analyzer import ContractAnalyzer
from .vector_store.embeddings import PolicyEmbeddings
from .vector_store.retriever import PolicyRetriever
from .services.groq_service import groq_service
from .services.auth_service import AuthService
from .core.prompts import CHATBOT_PROMPT, CHATBOT_POLICY_SEARCH_PROMPT
from langchain_google_genai import ChatGoogleGenerativeAI
from .database import init_db, get_db, User as DBUser, Session as DBSession, AnalysisJob as DBAnalysisJob, Negotiation, NegotiationMessage
from sqlalchemy.orm import Session as DBSessionType
from fastapi import Depends, WebSocket, WebSocketDisconnect
from .services.negotiation_service import NegotiationService
from .services.message_service import MessageService
from .services.websocket_manager import ws_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Legal Assistant API",
    description="Automated contract review and analysis system powered by Gemini",
    version="0.1.0"
)

# Add CORS middleware - must specify exact origins when credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    logger.info("🚀 Starting AI Legal Assistant API...")
    init_db()
    logger.info("✅ Database initialized and ready")


# Helper function to get AuthService with database session
def get_auth_service(db: DBSessionType = Depends(get_db)) -> AuthService:
    """Get AuthService instance with database session."""
    return AuthService(db)


# Helper function to get NegotiationService with database session
def get_negotiation_service(db: DBSessionType = Depends(get_db)) -> NegotiationService:
    """Get NegotiationService instance with database session."""
    return NegotiationService(db)


# Helper function to get MessageService with database session
def get_message_service(db: DBSessionType = Depends(get_db)) -> MessageService:
    """Get MessageService instance with database session."""
    return MessageService(db)


# Helper dependency to get current authenticated user (requires authentication)
def require_auth(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> DBUser:
    """Get current authenticated user or raise 401."""
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = auth_service.get_user_by_session(session_id)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user


# In-memory storage for backwards compatibility (will be fully migrated to database)
analysis_jobs: Dict[str, Dict[str, Any]] = {}


class ClauseAnalysisRequest(BaseModel):
    """Request model for single clause analysis."""
    clause_text: str
    clause_type: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    job_id: str
    status: str
    message: str


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str
    history: Optional[list] = []


class TTSRequest(BaseModel):
    """Request model for text-to-speech."""
    text: str
    voice: Optional[str] = None
    model: Optional[str] = "playai-tts"


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: str
    password: str
    company_name: str
    company_id: Optional[str] = None


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: str
    password: str


class AuthResponse(BaseModel):
    """Response model for authentication."""
    success: bool
    message: str
    user: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CreateNegotiationRequest(BaseModel):
    """Request model for creating a negotiation."""
    receiver_email: str
    contract_name: str
    contract_job_id: Optional[str] = None


class RejectNegotiationRequest(BaseModel):
    """Request model for rejecting a negotiation."""
    reason: Optional[str] = None


class CancelNegotiationRequest(BaseModel):
    """Request model for cancelling a negotiation."""
    reason: Optional[str] = None


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    content: str
    message_type: str = "text"


class MarkMessagesReadRequest(BaseModel):
    """Request model for marking messages as read."""
    message_ids: list[str]


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Legal Assistant API",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "upload": "/api/contracts/upload",
            "analyze": "/api/contracts/{job_id}/analyze",
            "status": "/api/contracts/{job_id}/status",
            "download": "/api/contracts/{job_id}/download",
            "policies": "/api/policies/ingest"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": settings.gemini_model,
        "vector_store": settings.chroma_collection_name
    }


# Authentication Endpoints

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    try:
        result = auth_service.register_user(
            email=request.email,
            password=request.password,
            company_name=request.company_name,
            company_id=request.company_id
        )

        if result["success"]:
            # Set session cookie (HttpOnly for security)
            response.set_cookie(
                key="session_id",
                value=result["session_id"],
                httponly=True,
                samesite="lax",
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            # Set WebSocket token cookie (non-HttpOnly so JS can read it)
            response.set_cookie(
                key="ws_token",
                value=result["session_id"],
                httponly=False,  # Allow JS access for WebSocket
                samesite="lax",
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            return AuthResponse(
                success=True,
                message="Registration successful",
                user=result["user"]
            )
        else:
            return AuthResponse(
                success=False,
                message="Registration failed",
                error=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user."""
    try:
        result = auth_service.login(
            email=request.email,
            password=request.password
        )

        if result["success"]:
            # Set session cookie (HttpOnly for security)
            response.set_cookie(
                key="session_id",
                value=result["session_id"],
                httponly=True,
                samesite="lax",
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            # Set WebSocket token cookie (non-HttpOnly so JS can read it)
            response.set_cookie(
                key="ws_token",
                value=result["session_id"],
                httponly=False,  # Allow JS access for WebSocket
                samesite="lax",
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            return AuthResponse(
                success=True,
                message="Login successful",
                user=result["user"]
            )
        else:
            return AuthResponse(
                success=False,
                message="Login failed",
                error=result.get("error", "Invalid credentials")
            )

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/api/auth/logout")
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user."""
    try:
        session_id = request.cookies.get("session_id")

        if session_id:
            auth_service.logout(session_id)

        # Clear both cookies
        response.delete_cookie(key="session_id")
        response.delete_cookie(key="ws_token")

        return {"success": True, "message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"success": False, "message": "Logout failed"}


@app.get("/api/auth/me")
async def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user info."""
    try:
        session_id = request.cookies.get("session_id")

        if not session_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        user = auth_service.get_user_by_session(session_id)

        if not user:
            raise HTTPException(status_code=401, detail="Session invalid or expired")

        return {
            "success": True,
            "user": user.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user info")


# Policy Management Endpoints

@app.post("/api/policies/upload")
async def upload_policy(
    file: UploadFile = File(...),
    user: DBUser = Depends(require_auth)
):
    """
    Upload a policy document to user's collection.

    Args:
        file: Policy document (PDF, TXT, or MD)

    Returns:
        Upload confirmation with chunk count
    """
    try:

        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.md']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Save uploaded file temporarily
        temp_dir = Path(settings.upload_dir) / "policies" / user.company_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        file_path = temp_dir / file.filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Ingest into user's collection
        from .vector_store.embeddings import PolicyEmbeddings
        embeddings = PolicyEmbeddings()
        chunk_count = embeddings.ingest_single_file(file_path, company_id=user.company_id)

        logger.info(f"Policy uploaded by {user.email}: {file.filename} ({chunk_count} chunks)")

        return {
            "success": True,
            "message": "Policy uploaded successfully",
            "filename": file.filename,
            "chunk_count": chunk_count,
            "company_id": user.company_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload policy: {str(e)}")


@app.get("/api/policies")
async def list_policies(user: DBUser = Depends(require_auth)):
    """
    List user's uploaded policies.

    Returns:
        List of policies with metadata
    """
    try:

        # Get user's collection
        from .vector_store.embeddings import PolicyEmbeddings
        embeddings = PolicyEmbeddings()
        collection = embeddings.get_or_create_user_collection(user.company_id)

        # Get all documents from collection
        count = collection.count()

        # Get unique file names from metadata
        if count > 0:
            results = collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])

            # Group by filename
            files = {}
            for metadata in metadatas:
                filename = metadata.get("filename", "unknown")
                if filename not in files:
                    # Generate a unique ID for this policy file
                    policy_id = hash(f"{user.company_id}_{filename}")

                    # Get file size if file_path exists
                    file_size = None
                    file_path = metadata.get("file_path", "")
                    if file_path and Path(file_path).exists():
                        file_size = Path(file_path).stat().st_size

                    files[filename] = {
                        "id": str(policy_id),
                        "name": filename,
                        "type": metadata.get("policy_type", "unknown"),
                        "version": metadata.get("version", "v1.0"),
                        "file_path": file_path,
                        "uploaded_at": metadata.get("uploaded_at", ""),
                        "file_size": file_size,
                        "chunk_count": 0
                    }
                files[filename]["chunk_count"] += 1

            policy_list = list(files.values())
        else:
            policy_list = []

        return {
            "success": True,
            "policies": policy_list,
            "total_chunks": count,
            "company_id": user.company_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List policies error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list policies")


@app.post("/api/contracts/upload", response_model=AnalysisResponse)
async def upload_contract(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: DBUser = Depends(require_auth)
):
    """
    Upload a contract for analysis.

    Args:
        file: Contract document file (.docx or .pdf)

    Returns:
        Job ID for tracking the analysis
    """
    try:

        # Validate file type
        if not file.filename.endswith(('.docx', '.pdf')):
            raise HTTPException(
                status_code=400,
                detail="Only .docx and .pdf files are supported"
            )

        # Validate file size
        content = await file.read()
        if len(content) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Save uploaded file
        upload_path = Path(settings.upload_dir) / f"{job_id}_{file.filename}"
        with open(upload_path, "wb") as f:
            f.write(content)

        # Initialize job with user_id if logged in
        job_data = {
            "job_id": job_id,
            "status": "uploaded",
            "filename": file.filename,
            "upload_path": str(upload_path),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Add user info (now always required)
        job_data["user_id"] = user.id
        job_data["company_name"] = user.company_name

        analysis_jobs[job_id] = job_data

        logger.info(f"Contract uploaded: {job_id} - {file.filename}")

        return AnalysisResponse(
            job_id=job_id,
            status="uploaded",
            message=f"Contract uploaded successfully. Use job_id to start analysis."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contracts")
async def list_contracts(request: Request):
    """
    List contracts for the current user or all if anonymous.
    """
    try:
        # Get current user from session
        session_id = request.cookies.get("session_id")
        current_user = auth_service.get_user_by_session(session_id) if session_id else None

        # Filter contracts based on user
        contracts = []
        for job_id, job in analysis_jobs.items():
            # If user is logged in, only show their contracts
            if current_user:
                if job.get("user_id") == current_user.id:
                    contracts.append({
                        "job_id": job["job_id"],
                        "filename": job["filename"],
                        "status": job.get("status", "unknown"),
                        "created_at": job.get("created_at"),
                        "company_name": job.get("company_name", current_user.company_name)
                    })
            else:
                # For anonymous users, show all or recent contracts (demo mode)
                contracts.append({
                    "job_id": job["job_id"],
                    "filename": job["filename"],
                    "status": job.get("status", "unknown"),
                    "created_at": job.get("created_at"),
                    "company_name": job.get("company_name", "Anonymous")
                })

        # Sort by created_at descending (newest first)
        contracts.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return {
            "success": True,
            "contracts": contracts,
            "user": current_user.to_dict() if current_user else None
        }

    except Exception as e:
        logger.error(f"Error listing contracts: {e}")
        raise HTTPException(status_code=500, detail="Failed to list contracts")


@app.post("/api/contracts/{job_id}/analyze")
async def analyze_contract(
    job_id: str,
    background_tasks: BackgroundTasks
):
    """
    Start contract analysis for an uploaded document.

    Args:
        job_id: Job ID from upload

    Returns:
        Analysis status
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    if job["status"] != "uploaded":
        raise HTTPException(
            status_code=400,
            detail=f"Job is already {job['status']}"
        )

    # Update status
    job["status"] = "analyzing"
    job["updated_at"] = datetime.now().isoformat()

    # Start analysis in background
    background_tasks.add_task(
        run_contract_analysis,
        job_id=job_id,
        contract_path=job["upload_path"]
    )

    logger.info(f"Started analysis for job: {job_id}")

    return {
        "job_id": job_id,
        "status": "analyzing",
        "message": "Contract analysis started. Check status for progress."
    }


def run_contract_analysis(job_id: str, contract_path: str):
    """
    Background task to run contract analysis.

    Args:
        job_id: Job ID
        contract_path: Path to the contract file
    """
    try:
        logger.info(f"Running analysis for job: {job_id}")

        # Get job data to extract company_id if available
        job = analysis_jobs.get(job_id)
        company_id = None

        if job and job.get("user_id"):
            # Find user by user_id to get company_id
            user_id = job["user_id"]
            for user in auth_service.users.values():
                if user.id == user_id:
                    company_id = user.company_id
                    logger.info(f"Using company-specific policies for company: {company_id}")
                    break

        # Initialize analyzer with company_id for user-specific policy retrieval
        analyzer = ContractAnalyzer(company_id=company_id)

        # Define output path
        output_path = Path(settings.output_dir) / f"{job_id}_reviewed.docx"

        # Run analysis
        results = analyzer.analyze_contract(
            contract_path=contract_path,
            output_path=str(output_path)
        )

        # Log the results structure for debugging
        logger.info(f"Analysis results structure: {list(results.keys()) if isinstance(results, dict) else type(results)}")
        if isinstance(results, dict) and "analysis_results" in results:
            logger.info(f"Number of analysis results: {len(results.get('analysis_results', []))}")
            if results.get('analysis_results'):
                logger.info(f"First result keys: {list(results['analysis_results'][0].keys())}")

        # Update job with results
        analysis_jobs[job_id].update({
            "status": "completed",
            "updated_at": datetime.now().isoformat(),
            "output_path": str(output_path),
            "results": results
        })

        logger.info(f"Analysis completed for job: {job_id}")

    except Exception as e:
        logger.error(f"Error in analysis job {job_id}: {e}")
        analysis_jobs[job_id].update({
            "status": "failed",
            "updated_at": datetime.now().isoformat(),
            "error": str(e)
        })


@app.get("/api/contracts/{job_id}/status")
async def get_analysis_status(request: Request, job_id: str):
    """
    Get the status of a contract analysis job.

    Args:
        job_id: Job ID

    Returns:
        Job status and results (if completed)
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    # Check ownership if user is authenticated
    session_id = request.cookies.get("session_id")
    current_user = auth_service.get_user_by_session(session_id) if session_id else None

    if current_user and job.get("user_id"):
        # If both user and job have user_id, check ownership
        if job["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied - not your contract")

    # Map backend status to frontend status
    status_map = {
        "uploaded": "pending",
        "analyzing": "processing",
        "completed": "completed",
        "failed": "failed"
    }

    # Calculate progress
    progress = 0
    if job["status"] == "uploaded":
        progress = 0
    elif job["status"] == "analyzing":
        progress = 50  # Default to 50% during analysis
    elif job["status"] == "completed":
        progress = 100
    elif job["status"] == "failed":
        progress = 0

    response = {
        "job_id": job_id,
        "status": status_map.get(job["status"], job["status"]),
        "progress": progress,
        "message": job.get("message", ""),
    }

    # Include full result with analysis details if completed
    if job["status"] == "completed" and "results" in job:
        results = job["results"]

        # Get and transform analysis results to match frontend expectations
        analysis_results_raw = results.get("analysis_results", [])
        analysis_results = []

        for idx, result in enumerate(analysis_results_raw):
            # Transform backend format to frontend format
            transformed = {
                "clause_number": idx + 1,
                "clause_text": result.get("text", result.get("clause_text", "")),
                "clause_type": result.get("type", result.get("clause_type", "Unknown")),
                "compliance_status": "Compliant" if result.get("compliant") else "Non-Compliant",
                "issues": result.get("issues", []),
                "recommendations": result.get("recommendations", []),
                "policy_references": result.get("policy_references", result.get("relevant_policies", [])),
                "risk_level": result.get("risk_level", "Medium"),
                "suggested_text": result.get("suggested_alternative", result.get("suggested_text"))
            }
            analysis_results.append(transformed)

        summary = results.get("summary", {})

        # If summary is missing fields, calculate them
        if not summary or "total_clauses" not in summary:
            total_clauses = len(analysis_results)
            compliant = sum(1 for r in analysis_results if r.get("compliance_status") == "Compliant")
            non_compliant = sum(1 for r in analysis_results if r.get("compliance_status") == "Non-Compliant")
            needs_review = sum(1 for r in analysis_results if r.get("compliance_status") == "Needs Review")

            critical = sum(1 for r in analysis_results if r.get("risk_level") == "Critical")
            high = sum(1 for r in analysis_results if r.get("risk_level") == "High")
            medium = sum(1 for r in analysis_results if r.get("risk_level") == "Medium")
            low = sum(1 for r in analysis_results if r.get("risk_level") == "Low")

            compliance_rate = (compliant / total_clauses * 100) if total_clauses > 0 else 0

            # Determine overall risk
            if critical > 0:
                overall_risk = "Critical"
            elif high > 0:
                overall_risk = "High"
            elif medium > 0:
                overall_risk = "Medium"
            else:
                overall_risk = "Low"

            summary = {
                "total_clauses": total_clauses,
                "compliant_clauses": compliant,
                "non_compliant_clauses": non_compliant,
                "needs_review_clauses": needs_review,
                "critical_issues": critical,
                "high_risk_issues": high,
                "medium_risk_issues": medium,
                "low_risk_issues": low,
                "compliance_rate": compliance_rate,
                "overall_risk": overall_risk
            }

        response["result"] = {
            "job_id": job_id,
            "contract_name": job["filename"],
            "status": "completed",
            "created_at": job["created_at"],
            "completed_at": job["updated_at"],
            "analysis_results": analysis_results,
            "summary": summary,
            "output_files": {
                "reviewed_contract": job.get("output_path", ""),
                "detailed_report": job.get("output_path", "").replace(".docx", "_DETAILED_REPORT.docx"),
                "html_summary": job.get("output_path", "").replace(".docx", "_SUMMARY.html")
            }
        }

    # Include error if failed
    if job["status"] == "failed" and "error" in job:
        response["message"] = job["error"]

    return response


@app.get("/api/contracts/{job_id}/download/{report_type}")
async def download_report(job_id: str, report_type: str):
    """
    Download analysis report.

    Args:
        job_id: Job ID
        report_type: Type of report (reviewed, detailed, html)

    Returns:
        Report file
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {job['status']}"
        )

    output_path = job.get("output_path")
    if not output_path:
        raise HTTPException(status_code=404, detail="Output file not found")

    # Determine file path based on report type
    if report_type == "reviewed":
        file_path = output_path
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"reviewed_{job['filename']}"
    elif report_type == "detailed":
        file_path = output_path.replace(".docx", "_DETAILED_REPORT.docx")
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"detailed_report_{job['filename']}"
    elif report_type == "html":
        file_path = output_path.replace(".docx", "_SUMMARY.html")
        media_type = "text/html"
        filename = f"summary_{job['filename'].replace('.docx', '.html')}"
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")

    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"{report_type} report not found")

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )


@app.post("/api/analyze/clause")
async def analyze_single_clause(request: ClauseAnalysisRequest):
    """
    Analyze a single clause (for testing or quick checks).

    Args:
        request: Clause analysis request

    Returns:
        Analysis result
    """
    try:
        analyzer = ContractAnalyzer()

        result = analyzer.analyze_clause_text(
            clause_text=request.clause_text,
            clause_type=request.clause_type
        )

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error analyzing clause: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/policies/ingest")
async def ingest_policies(background_tasks: BackgroundTasks):
    """
    Ingest company policies and laws into the vector store.

    Returns:
        Ingestion status
    """
    try:
        embeddings = PolicyEmbeddings()

        # Run ingestion
        results = embeddings.ingest_policies()

        logger.info(f"Policy ingestion completed: {results}")

        return {
            "status": "success",
            "message": "Policies and laws ingested successfully",
            "results": results,
            "collection_stats": embeddings.get_collection_stats()
        }

    except Exception as e:
        logger.error(f"Error ingesting policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/policies/upload")
async def upload_policy(file: UploadFile = File(...)):
    """
    Upload a policy file to the policies directory.

    Args:
        file: Policy file (.txt, .md, or .pdf)

    Returns:
        Upload status
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.txt', '.md', '.pdf')):
            raise HTTPException(
                status_code=400,
                detail="Only .txt, .md, and .pdf files are supported"
            )

        # Save file to policies directory
        policy_dir = Path(settings.policies_dir)
        policy_dir.mkdir(parents=True, exist_ok=True)

        file_path = policy_dir / file.filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Policy uploaded: {file.filename}")

        return {
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "message": "Policy uploaded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies")
async def list_policies():
    """
    List all policy files in the policies directory.

    Returns:
        List of policy files with metadata
    """
    try:
        policy_dir = Path(settings.policies_dir)
        if not policy_dir.exists():
            return []

        policies = []
        for file_path in policy_dir.glob("*"):
            if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.pdf']:
                stat = file_path.stat()

                # Extract metadata from filename (e.g., Legal_Liability_v1.0.txt)
                name_parts = file_path.stem.split('_')
                policy_type = name_parts[0] if name_parts else "Unknown"
                version = name_parts[-1] if len(name_parts) > 1 and name_parts[-1].startswith('v') else "v1.0"

                policies.append({
                    "id": file_path.name,
                    "name": file_path.stem,
                    "type": policy_type,
                    "version": version,
                    "file_path": str(file_path),
                    "file_size": stat.st_size,
                    "uploaded_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })

        return policies

    except Exception as e:
        logger.error(f"Error listing policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """
    Delete a policy file.

    Args:
        policy_id: Policy filename (ID)

    Returns:
        Deletion status
    """
    try:
        policy_dir = Path(settings.policies_dir)
        file_path = policy_dir / policy_id

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Policy not found")

        file_path.unlink()
        logger.info(f"Policy deleted: {policy_id}")

        return {
            "status": "success",
            "message": f"Policy {policy_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/policies/reingest")
async def reingest_policies():
    """
    Reingest all policies from the policies directory into the vector store.

    Returns:
        Ingestion status
    """
    try:
        embeddings = PolicyEmbeddings()
        results = embeddings.ingest_policies()

        logger.info(f"Policy reingestion completed: {results}")

        return {
            "status": "success",
            "message": "Policies reingested successfully",
            "results": results
        }

    except Exception as e:
        logger.error(f"Error reingesting policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/stats")
async def get_policy_stats():
    """
    Get statistics about the policy vector store.

    Returns:
        Collection statistics
    """
    try:
        embeddings = PolicyEmbeddings()
        stats = embeddings.get_collection_stats()

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/contracts/{job_id}")
async def delete_analysis_job(job_id: str):
    """
    Delete an analysis job and its associated files.

    Args:
        job_id: Job ID

    Returns:
        Deletion status
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    # Delete uploaded file
    if "upload_path" in job and Path(job["upload_path"]).exists():
        Path(job["upload_path"]).unlink()

    # Delete output file
    if "output_path" in job and Path(job["output_path"]).exists():
        Path(job["output_path"]).unlink()

    # Remove from jobs
    del analysis_jobs[job_id]

    logger.info(f"Deleted job: {job_id}")

    return {
        "status": "success",
        "message": f"Job {job_id} deleted successfully"
    }


# ===== Chatbot and Voice Endpoints =====

@app.post("/api/chat/{job_id}")
async def chat_with_assistant(job_id: str, chat_request: ChatRequest, request: Request):
    """
    Chat endpoint with Server-Sent Events streaming.
    Provides COMPLETE analysis data to LLM for accurate responses.

    Args:
        job_id: Job ID for the contract analysis
        chat_request: Chat request with message and history

    Returns:
        SSE stream with assistant response
    """
    # Check if job exists
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    # Check ownership if user is authenticated
    session_id = request.cookies.get("session_id")
    current_user = auth_service.get_user_by_session(session_id) if session_id else None

    if current_user and job.get("user_id"):
        # If both user and job have user_id, check ownership
        if job["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied - not your contract")

    # Check if analysis is complete
    if job.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="Analysis not yet completed. Please wait for analysis to finish."
        )

    # Get the COMPLETE result object - check both "result" and "results" keys
    result = job.get("result") or job.get("results", {})

    # DEBUG: Log what we actually have
    logger.info(f"DEBUG - Job keys: {list(job.keys())}")
    logger.info(f"DEBUG - Job status: {job.get('status')}")
    logger.info(f"DEBUG - Has 'result': {'result' in job}, Has 'results': {'results' in job}")
    logger.info(f"DEBUG - Result is empty: {not result}")

    if result:
        logger.info(f"DEBUG - Result keys: {list(result.keys())}")
        if "analysis_results" in result:
            logger.info(f"DEBUG - analysis_results length: {len(result['analysis_results'])}")
            if result['analysis_results']:
                logger.info(f"DEBUG - First clause keys: {list(result['analysis_results'][0].keys())}")

    # If result is still empty, check if data is directly in job
    if not result or not result.get("analysis_results"):
        logger.warning(f"Result is empty or missing analysis_results. Checking job directly...")
        # Try to use the job data directly
        if "analysis_results" in job:
            result = job
            logger.info(f"Using job data directly - found {len(job.get('analysis_results', []))} results")

    # Initialize LLM with slightly higher temperature for more natural conversation
    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0.5,  # Slightly higher for more conversational responses
        max_output_tokens=1024  # Shorter for brief responses
    )

    # Create comprehensive system prompt with ALL analysis data
    system_prompt = f"""You are a friendly legal assistant helping someone understand their contract review. Speak naturally and conversationally, as if explaining to a colleague.

IMPORTANT: Only use information from the data below. Keep responses brief and suitable for speech.

====================
CONTRACT ANALYSIS DATA
====================

{json.dumps(result, indent=2)}

====================
END OF DATA
====================

CONVERSATION STYLE:

1. Be conversational and human-like:
   - Use natural language, not robotic lists
   - Keep sentences short and clear
   - Speak as if you're having a conversation
   - Avoid long technical explanations

2. For non-compliant clauses:
   - Start with the count: "I found 5 issues..." or "There are 3 problematic clauses..."
   - Briefly mention the main problems
   - Focus on the most important ones first
   - Don't quote entire clauses - just key phrases

3. Keep it brief:
   - Aim for 2-3 sentences for simple questions
   - Maximum 4-5 sentences for complex questions
   - If there's a lot to cover, ask if they want more details

4. Be helpful:
   - If no issues: "Good news! All clauses are compliant."
   - If many issues: "There are several concerns. The main ones are..."
   - Offer to elaborate: "Would you like me to explain any of these?"

5. Natural speech patterns:
   - Use contractions (it's, there's, don't)
   - Add transitions (actually, basically, essentially)
   - Sound encouraging when appropriate

Remember: You're having a conversation, not reading a report. Be helpful, clear, and concise."""

    # Log for debugging
    logger.info(f"Chat for job {job_id}")
    logger.info(f"Result keys: {list(result.keys())}")
    logger.info(f"System prompt size: {len(system_prompt)} characters")

    if "analysis_results" in result:
        analysis_results = result["analysis_results"]
        non_compliant = sum(1 for c in analysis_results
                          if c.get("compliance_status") == "Non-Compliant" or not c.get("compliant", True))
        logger.info(f"Analysis has {len(analysis_results)} clauses, {non_compliant} non-compliant")

    # Build message history
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add chat history (limit to prevent token overflow)
    for msg in chat_request.history[-5:]:  # Keep last 5 messages
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # Add current message
    messages.append({"role": "user", "content": chat_request.message})

    async def generate_response() -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        try:
            # Get streaming response from LLM
            response = llm.stream(messages)

            for chunk in response:
                if chunk.content:
                    # Format as SSE
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"
                    await asyncio.sleep(0.01)  # Small delay to prevent overwhelming client

            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in chat streaming: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering for nginx
        }
    )


@app.post("/api/voice/synthesize")
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using Groq PlayAI TTS.

    Args:
        request: TTS request with text and voice options

    Returns:
        WAV audio stream
    """
    try:
        # Generate speech
        audio_bytes = groq_service.text_to_speech(
            text=request.text,
            voice=request.voice,
            model=request.model
        )

        # Return audio stream
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "inline; filename=speech.wav",
                "Cache-Control": "no-cache"
            }
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/transcribe")
async def speech_to_text(
    file: UploadFile = File(...),
    language: Optional[str] = Form("en"),
    model: Optional[str] = Form("whisper-large-v3-turbo")
):
    """
    Transcribe audio to text using Groq Whisper.

    Args:
        file: Audio file to transcribe
        language: Language code (ISO-639-1)
        model: Whisper model to use

    Returns:
        Transcription result
    """
    # Validate file size
    if file.size > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 25MB limit"
        )

    try:
        # Read file content
        audio_content = await file.read()

        # Transcribe audio
        result = groq_service.speech_to_text(
            audio_file=io.BytesIO(audio_content),
            filename=file.filename,
            model=model,
            language=language,
            response_format="json"
        )

        return {
            "status": "success",
            "transcription": result.get("text", ""),
            "language": result.get("language", language)
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug/{job_id}")
async def debug_job(job_id: str):
    """
    Debug endpoint to see complete job structure.
    """
    if job_id not in analysis_jobs:
        return {
            "error": "Job not found",
            "available_jobs": list(analysis_jobs.keys())
        }

    job = analysis_jobs[job_id]
    # Check both "result" and "results" keys
    result = job.get("result") or job.get("results", {})

    # Create a summary of what's in the job
    debug_info = {
        "job_id": job_id,
        "job_status": job.get("status"),
        "job_keys": list(job.keys()),
        "has_result": bool(job.get("result")),
        "has_results": bool(job.get("results")),
        "using_key": "results" if job.get("results") else "result" if job.get("result") else "none",
        "result_keys": list(result.keys()) if result else [],
        "analysis_results_count": len(result.get("analysis_results", [])) if result else 0
    }

    # If there are analysis results, show sample
    if result and "analysis_results" in result and result["analysis_results"]:
        first_clause = result["analysis_results"][0]
        debug_info["first_clause_keys"] = list(first_clause.keys())
        debug_info["first_clause_compliance"] = {
            "compliance_status": first_clause.get("compliance_status"),
            "compliant": first_clause.get("compliant")
        }

        # Count non-compliant
        non_compliant = 0
        for clause in result["analysis_results"]:
            if clause.get("compliance_status") == "Non-Compliant" or not clause.get("compliant", True):
                non_compliant += 1
        debug_info["non_compliant_count"] = non_compliant

    return debug_info


@app.get("/api/chat/{job_id}/context")
async def get_chat_context(job_id: str):
    """
    Debug endpoint to view the chat context for a job.

    Args:
        job_id: Job ID for the contract analysis

    Returns:
        The context that would be provided to the chatbot
    """
    # Check if job exists
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    # Check if analysis is complete
    if job.get("status") != "completed":
        return {
            "status": "incomplete",
            "message": "Analysis not yet completed"
        }

    # Get analysis results - check both "result" and "results" keys
    result = job.get("result") or job.get("results", {})
    analysis_results = result.get("analysis_results", [])
    summary = result.get("summary", {})

    # Format analysis results for context
    non_compliant_clauses = []

    for i, clause in enumerate(analysis_results):
        # Determine compliance status from available fields
        compliance_status = clause.get("compliance_status", "")
        if not compliance_status:
            compliant_bool = clause.get("compliant", True)
            compliance_status = "Compliant" if compliant_bool else "Non-Compliant"

        if compliance_status == "Non-Compliant":
            non_compliant_clauses.append({
                "clause_number": clause.get("clause_number", i + 1),
                "clause_type": clause.get("clause_type", ""),
                "compliance_status": compliance_status,
                "risk_level": clause.get("risk_level", "Medium")
            })

    return {
        "job_id": job_id,
        "contract_name": result.get("contract_name", "Unknown"),
        "total_clauses": len(analysis_results),
        "compliant_clauses": len(analysis_results) - len(non_compliant_clauses),
        "non_compliant_clauses": len(non_compliant_clauses),
        "compliance_rate": round(((len(analysis_results) - len(non_compliant_clauses)) / max(len(analysis_results), 1)) * 100, 1),
        "non_compliant_list": non_compliant_clauses,
        "summary": summary
    }


@app.get("/api/voice/voices")
async def get_available_voices(language: str = "english"):
    """
    Get list of available TTS voices.

    Args:
        language: Language for voices ("english" or "arabic")

    Returns:
        List of available voices
    """
    if not groq_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Voice features are not available. Please configure GROQ_API_KEY."
        )

    voices = groq_service.get_available_voices(language)

    return {
        "status": "success",
        "language": language,
        "voices": voices,
        "default": voices[0] if voices else None
    }


# ===== Negotiation Endpoints =====

@app.post("/api/negotiations")
async def create_negotiation(
    request: CreateNegotiationRequest,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service)
):
    """
    Create a new negotiation request.

    Args:
        request: Negotiation creation request
        user: Authenticated user (initiator)
        negotiation_service: Negotiation service instance

    Returns:
        Created negotiation data or error
    """
    result = negotiation_service.create_negotiation(
        initiator_id=user.id,
        receiver_email=request.receiver_email,
        contract_name=request.contract_name,
        contract_job_id=request.contract_job_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result["negotiation"]


@app.get("/api/negotiations")
async def list_negotiations(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service)
):
    """
    List user's negotiations with optional filtering.

    Args:
        status: Optional status filter (pending, active, completed, rejected, cancelled)
        limit: Maximum number of results (default: 20)
        offset: Number of results to skip (default: 0)
        user: Authenticated user
        negotiation_service: Negotiation service instance

    Returns:
        List of negotiations with pagination metadata
    """
    result = negotiation_service.list_user_negotiations(
        user_id=user.id,
        status_filter=status,
        limit=limit,
        offset=offset
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    # Add unread counts for each negotiation
    for negotiation in result["negotiations"]:
        unread_count = negotiation_service.get_unread_count(negotiation["id"], user.id)
        negotiation["unread_count"] = unread_count

    return result


@app.get("/api/negotiations/{negotiation_id}")
async def get_negotiation(
    negotiation_id: str,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service)
):
    """
    Get negotiation details.

    Args:
        negotiation_id: ID of the negotiation
        user: Authenticated user
        negotiation_service: Negotiation service instance

    Returns:
        Negotiation data
    """
    # Check access
    if not negotiation_service.can_user_access(negotiation_id, user.id):
        raise HTTPException(status_code=403, detail="You do not have access to this negotiation")

    negotiation = negotiation_service.get_negotiation(negotiation_id)
    if not negotiation:
        raise HTTPException(status_code=404, detail="Negotiation not found")

    # Add unread count
    result = negotiation.to_dict()
    result["unread_count"] = negotiation_service.get_unread_count(negotiation_id, user.id)

    return result


@app.patch("/api/negotiations/{negotiation_id}/accept")
async def accept_negotiation(
    negotiation_id: str,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service)
):
    """
    Accept a pending negotiation request.

    Args:
        negotiation_id: ID of the negotiation
        user: Authenticated user (must be receiver)
        negotiation_service: Negotiation service instance

    Returns:
        Updated negotiation data
    """
    result = negotiation_service.accept_negotiation(negotiation_id, user.id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result["negotiation"]


@app.patch("/api/negotiations/{negotiation_id}/reject")
async def reject_negotiation(
    negotiation_id: str,
    request: RejectNegotiationRequest,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service)
):
    """
    Reject a pending negotiation request.

    Args:
        negotiation_id: ID of the negotiation
        request: Rejection request with optional reason
        user: Authenticated user (must be receiver)
        negotiation_service: Negotiation service instance

    Returns:
        Success status
    """
    result = negotiation_service.reject_negotiation(negotiation_id, user.id, request.reason)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"status": "success", "message": "Negotiation rejected"}


@app.patch("/api/negotiations/{negotiation_id}/complete")
async def complete_negotiation(
    negotiation_id: str,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service)
):
    """
    Mark a negotiation as completed.

    Args:
        negotiation_id: ID of the negotiation
        user: Authenticated user (must be participant)
        negotiation_service: Negotiation service instance

    Returns:
        Success status
    """
    result = negotiation_service.complete_negotiation(negotiation_id, user.id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"status": "success", "message": "Negotiation marked as completed"}


@app.delete("/api/negotiations/{negotiation_id}")
async def cancel_negotiation(
    negotiation_id: str,
    request: CancelNegotiationRequest,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service)
):
    """
    Cancel a negotiation.

    Args:
        negotiation_id: ID of the negotiation
        request: Cancellation request with optional reason
        user: Authenticated user (must be participant)
        negotiation_service: Negotiation service instance

    Returns:
        Success status
    """
    result = negotiation_service.cancel_negotiation(negotiation_id, user.id, request.reason)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"status": "success", "message": "Negotiation cancelled"}


# ===== Message Endpoints =====

@app.post("/api/negotiations/{negotiation_id}/messages")
async def send_message(
    negotiation_id: str,
    request: SendMessageRequest,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service),
    message_service: MessageService = Depends(get_message_service)
):
    """
    Send a message in a negotiation (HTTP fallback for when WebSocket is unavailable).

    Args:
        negotiation_id: ID of the negotiation
        request: Message content
        user: Authenticated user
        negotiation_service: Negotiation service instance
        message_service: Message service instance

    Returns:
        Created message data
    """
    # Check access
    if not negotiation_service.can_user_access(negotiation_id, user.id):
        raise HTTPException(status_code=403, detail="You do not have access to this negotiation")

    # Send message
    result = message_service.send_message(
        negotiation_id=negotiation_id,
        sender_user_id=user.id,
        content=request.content,
        message_type=request.message_type
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    # Broadcast to WebSocket connections
    await ws_manager.send_message_event(
        negotiation_id=negotiation_id,
        message_data=result["message"],
        sender_user_id=user.id
    )

    return result["message"]


@app.get("/api/negotiations/{negotiation_id}/messages")
async def get_messages(
    negotiation_id: str,
    limit: int = 50,
    offset: int = 0,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service),
    message_service: MessageService = Depends(get_message_service)
):
    """
    Get message history for a negotiation.

    Args:
        negotiation_id: ID of the negotiation
        limit: Maximum number of messages (default: 50)
        offset: Number of messages to skip (default: 0)
        user: Authenticated user
        negotiation_service: Negotiation service instance
        message_service: Message service instance

    Returns:
        List of messages with pagination metadata
    """
    # Check access
    if not negotiation_service.can_user_access(negotiation_id, user.id):
        raise HTTPException(status_code=403, detail="You do not have access to this negotiation")

    result = message_service.get_message_history(
        negotiation_id=negotiation_id,
        limit=limit,
        offset=offset
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@app.patch("/api/negotiations/{negotiation_id}/messages/read")
async def mark_messages_read(
    negotiation_id: str,
    request: MarkMessagesReadRequest,
    user: DBUser = Depends(require_auth),
    negotiation_service: NegotiationService = Depends(get_negotiation_service),
    message_service: MessageService = Depends(get_message_service)
):
    """
    Mark messages as read.

    Args:
        negotiation_id: ID of the negotiation
        request: List of message IDs to mark as read
        user: Authenticated user
        negotiation_service: Negotiation service instance
        message_service: Message service instance

    Returns:
        Success status with count of marked messages
    """
    # Check access
    if not negotiation_service.can_user_access(negotiation_id, user.id):
        raise HTTPException(status_code=403, detail="You do not have access to this negotiation")

    result = message_service.mark_as_read(
        message_ids=request.message_ids,
        user_id=user.id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    # Notify via WebSocket
    await ws_manager.send_read_receipt(
        negotiation_id=negotiation_id,
        message_ids=request.message_ids,
        reader_user_id=user.id
    )

    return {"status": "success", "marked_count": result["marked_count"]}


# ===== WebSocket Endpoint =====

@app.websocket("/ws/negotiations/{negotiation_id}")
async def websocket_negotiation(
    websocket: WebSocket,
    negotiation_id: str,
    token: Optional[str] = None,
    db: DBSessionType = Depends(get_db)
):
    """
    WebSocket endpoint for real-time negotiation chat.

    Args:
        websocket: WebSocket connection
        negotiation_id: ID of the negotiation
        token: Session token for authentication
        db: Database session

    Protocol:
        Client → Server:
            - {type: "message", content: "..."}  # Send message
            - {type: "typing", is_typing: true}  # Typing indicator
            - {type: "read", message_ids: [...]} # Mark as read

        Server → Client:
            - {type: "message", ...}             # New message
            - {type: "typing", user_id, is_typing} # Typing indicator
            - {type: "read", message_ids, reader_user_id} # Read receipt
            - {type: "user_joined", user_id}     # User joined
            - {type: "user_left", user_id}       # User left
            - {type: "ack", message_id}          # Message acknowledgment
            - {type: "error", code, message}     # Error
    """
    # Accept the connection first
    await websocket.accept()

    try:
        # Authenticate
        if not token:
            logger.warning(f"WebSocket connection to {negotiation_id} without token")
            await websocket.send_json({
                "type": "error",
                "code": "auth_required",
                "message": "Authentication required"
            })
            await websocket.close(code=1008, reason="Authentication required")
            return

        auth_service = AuthService(db)
        user = auth_service.get_user_by_session(token)

        if not user:
            logger.warning(f"WebSocket connection with invalid token: {token[:10]}...")
            await websocket.send_json({
                "type": "error",
                "code": "invalid_session",
                "message": "Invalid session"
            })
            await websocket.close(code=1008, reason="Invalid session")
            return

        # Check access
        negotiation_service = NegotiationService(db)
        if not negotiation_service.can_user_access(negotiation_id, user.id):
            logger.warning(f"User {user.id} attempted to access negotiation {negotiation_id} without permission")
            await websocket.send_json({
                "type": "error",
                "code": "access_denied",
                "message": "Access denied"
            })
            await websocket.close(code=1008, reason="Access denied")
            return

        # Register connection
        await ws_manager.connect(negotiation_id, user.id, websocket)
        logger.info(f"WebSocket connected: user {user.id} in negotiation {negotiation_id}")
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")
        return

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "message":
                # Send message
                content = data.get("content", "")

                if not content.strip():
                    await ws_manager.send_error(
                        negotiation_id, user.id,
                        "empty_message", "Message content cannot be empty"
                    )
                    continue

                if len(content) > 10000:
                    await ws_manager.send_error(
                        negotiation_id, user.id,
                        "message_too_long", "Message exceeds 10,000 characters"
                    )
                    continue

                # Persist message
                message_service = MessageService(db)
                result = message_service.send_message(
                    negotiation_id=negotiation_id,
                    sender_user_id=user.id,
                    content=content,
                    message_type="text"
                )

                if result["success"]:
                    # Send acknowledgment to sender
                    await ws_manager.send_acknowledgment(
                        negotiation_id, user.id, result["message"]["id"]
                    )

                    # Broadcast to all users in negotiation
                    await ws_manager.send_message_event(
                        negotiation_id=negotiation_id,
                        message_data=result["message"],
                        sender_user_id=user.id
                    )
                else:
                    await ws_manager.send_error(
                        negotiation_id, user.id,
                        "send_failed", result["error"]
                    )

            elif message_type == "typing":
                # Typing indicator
                is_typing = data.get("is_typing", False)
                await ws_manager.send_typing_indicator(
                    negotiation_id, user.id, is_typing
                )

            elif message_type == "read":
                # Mark messages as read
                message_ids = data.get("message_ids", [])
                if message_ids:
                    message_service = MessageService(db)
                    result = message_service.mark_as_read(message_ids, user.id)

                    if result["success"]:
                        await ws_manager.send_read_receipt(
                            negotiation_id, message_ids, user.id
                        )

            else:
                await ws_manager.send_error(
                    negotiation_id, user.id,
                    "unknown_message_type", f"Unknown message type: {message_type}"
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id} in negotiation {negotiation_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {str(e)}")
    finally:
        # Disconnect
        await ws_manager.disconnect(negotiation_id, user.id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
