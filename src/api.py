"""FastAPI application for AI Legal Assistant."""

import logging
import os
import uuid
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form, Request, Response, Query, Header
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
from .database import init_db, get_db, User as DBUser, Session as DBSession, AnalysisJob as DBAnalysisJob, Negotiation, NegotiationMessage, Document
from sqlalchemy.orm import Session as DBSessionType
from fastapi import Depends, WebSocket, WebSocketDisconnect
from .services.negotiation_service import NegotiationService
from .services.message_service import MessageService
from .services.websocket_manager import ws_manager
from .services.document_service import DocumentService
from .services.docx_parser_service import DocxParserService
from .services.document_sync_service import document_sync_service
from .services.collab_websocket_adapter import collab_ws_manager

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

# Configure CORS origins - support local, VPS, and Azure deployments
def get_cors_origins():
    """Get CORS origins from environment or use defaults."""
    # Base origins for development
    origins = [
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Word Add-in dev server
        "https://localhost:3001",  # Word Add-in HTTPS
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://127.0.0.1:3001",
        "null",  # For Office Add-in iframe
    ]

    # Add custom CORS origins from environment variable
    # This supports both VPS and Azure deployments
    custom_origins = os.getenv("CORS_ORIGINS", "")
    if custom_origins:
        # Format: "https://contract.cirilla.ai,https://api.contract.cirilla.ai,https://contracts.cirilla.ai"
        origins.extend([origin.strip() for origin in custom_origins.split(",") if origin.strip()])

    # Backward compatibility: Add Azure-specific origins
    azure_origins = os.getenv("AZURE_CORS_ORIGINS", "")
    if azure_origins:
        origins.extend([origin.strip() for origin in azure_origins.split(",") if origin.strip()])

    # Default production domains (fallback if env vars not set)
    default_production = [
        "https://contract.cirilla.ai",      # VPS frontend
        "https://api.contract.cirilla.ai",  # VPS API
        "https://collab.contract.cirilla.ai",  # VPS collaboration
        "https://word.contract.cirilla.ai", # VPS Word add-in
        "https://contracts.cirilla.ai",     # Azure frontend custom domain
        "https://api.cirilla.ai",           # Azure API custom domain
        "https://collab.cirilla.ai",        # Azure collaboration custom domain
        "https://ailegal.cirilla.ai",       # Legacy domain
        "https://api.ailegal.cirilla.ai",   # Legacy API
        # Azure default Container Apps URLs
        "https://frontend.niceground-5231e36c.uaenorth.azurecontainerapps.io",
        "https://backend-api.niceground-5231e36c.uaenorth.azurecontainerapps.io",
        "https://collab-server.niceground-5231e36c.uaenorth.azurecontainerapps.io",
        "https://word-addin.niceground-5231e36c.uaenorth.azurecontainerapps.io",
    ]

    origins.extend(default_production)

    # Remove duplicates while preserving order
    seen = set()
    unique_origins = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)

    logger.info(f"CORS allowed origins: {unique_origins}")
    return unique_origins

# Add CORS middleware - must specify exact origins when credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Regional Knowledge Base Middleware
@app.middleware("http")
async def inject_region_context(request: Request, call_next):
    """
    Inject region_code into request state based on client IP.

    Extracts client IP from request headers (respecting proxy headers),
    uses GeoLocationService to detect region, and stores result in request.state.
    """
    from .services.geolocation_service import get_geo_service

    # Extract client IP (respect proxy headers)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.headers.get("X-Real-IP", "")
    if not client_ip and request.client:
        client_ip = request.client.host

    # Detect region from IP
    region_code = None
    try:
        if client_ip:
            geo_service = get_geo_service()
            region_code = geo_service.get_region_from_ip(client_ip)
    except Exception as e:
        logger.debug(f"Error detecting region for IP {client_ip}: {e}")

    # Store in request state
    request.state.region_code = region_code
    request.state.client_ip = client_ip

    # Log for observability (debug level to avoid log spam)
    if region_code:
        logger.debug(f"Request from IP {client_ip} → region {region_code}")
    else:
        logger.debug(f"Request from IP {client_ip} → no regional KB")

    response = await call_next(request)
    return response


# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database and regional knowledge bases on application startup."""
    logger.info("🚀 Starting AI Legal Assistant API...")
    try:
        init_db()
        logger.info("✅ Database initialized and ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}", exc_info=True)
        # Continue anyway so container stays up for debugging

    # Start collaboration WebSocket manager
    try:
        await collab_ws_manager.start()
        logger.info("✅ Collaboration service started")
    except Exception as e:
        logger.error(f"❌ Failed to start collaboration service: {e}", exc_info=True)

    # Ingest regional knowledge bases
    try:
        from .core.config import REGION_CONFIG, get_enabled_regions, settings as config_settings
        from .vector_store.embeddings import PolicyEmbeddings

        if not config_settings.regional_kb_enabled:
            logger.info("ℹ️  Regional knowledge bases disabled (REGIONAL_KB_ENABLED=false)")
        else:
            enabled_regions = get_enabled_regions()
            if not enabled_regions:
                logger.info("ℹ️  No enabled regional knowledge bases configured")
            else:
                logger.info(f"📚 Ingesting regional knowledge bases for: {', '.join(enabled_regions)}")

                embeddings = PolicyEmbeddings()
                total_chunks = 0

                for region_code in enabled_regions:
                    region_config = REGION_CONFIG[region_code]
                    data_directory = region_config["data_directory"]

                    logger.info(f"🌍 Processing region: {region_config['metadata']['region_name']} ({region_code})")

                    try:
                        chunks = embeddings.ingest_regional_directory(
                            region_code=region_code,
                            directory_path=data_directory
                        )

                        if chunks > 0:
                            total_chunks += chunks
                            logger.info(f"✅ Ingested {chunks} chunks for {region_code}")
                        else:
                            logger.info(f"ℹ️  Region {region_code} already populated or no documents found")

                    except Exception as e:
                        logger.error(f"❌ Failed to ingest region {region_code}: {e}", exc_info=True)
                        # Continue with other regions

                if total_chunks > 0:
                    logger.info(f"✅ Regional knowledge bases ready: {total_chunks} total chunks ingested")
                else:
                    logger.info("ℹ️  All regional knowledge bases already populated")

    except Exception as e:
        logger.error(f"❌ Failed to initialize regional knowledge bases: {e}", exc_info=True)
        logger.error("⚠️  Regional feature will be unavailable, but application will continue")
        # Don't crash the application, just log the error


# Shutdown event to clean up resources
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    logger.info("🛑 Shutting down AI Legal Assistant API...")
    try:
        await collab_ws_manager.stop()
        logger.info("✅ Collaboration service stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping collaboration service: {e}")


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


# Helper function to get DocumentService with database session
def get_document_service(db: DBSessionType = Depends(get_db)) -> DocumentService:
    """Get DocumentService instance with database session."""
    return DocumentService(db)


# Helper dependency to get current authenticated user (requires authentication)
def require_auth(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    authorization: Optional[str] = Header(None)
) -> DBUser:
    """Get current authenticated user or raise 401.

    Supports both cookie-based and token-based authentication for Word Add-in compatibility.
    """
    session_id = None

    # Try Authorization header first (for Word Add-in)
    if authorization and authorization.startswith("Bearer "):
        session_id = authorization[7:]  # Remove "Bearer " prefix

    # Fall back to cookie-based auth
    if not session_id:
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
    session_token: Optional[str] = None  # For Word Add-in Bearer token auth


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


class CreateDocumentRequest(BaseModel):
    """Request model for creating a document."""
    title: str
    negotiation_id: Optional[str] = None
    analysis_job_id: Optional[str] = None
    import_source: Optional[str] = None


class UpdateDocumentRequest(BaseModel):
    """Request model for updating a document."""
    title: Optional[str] = None
    status: Optional[str] = None
    yjs_state_vector: Optional[str] = None


class AddCollaboratorRequest(BaseModel):
    """Request model for adding a collaborator to a document."""
    user_id: str
    permission: str = "edit"


class WordAddinAnalyzeTextRequest(BaseModel):
    """Request model for Word Add-in text analysis."""
    document_text: str
    paragraphs: List[str]
    paragraph_indices: Optional[List[int]] = None  # Original Word paragraph indices


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
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "model": getattr(settings, 'gemini_model', 'unknown'),
            "vector_store": getattr(settings, 'chroma_collection_name', 'unknown')
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        # Return healthy anyway so container stays up for debugging
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
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
            # Use domain=".cirilla.ai" to work across all subdomains
            response.set_cookie(
                key="session_id",
                value=result["session_id"],
                httponly=True,
                secure=True,  # Require HTTPS
                samesite="none",  # Allow cross-subdomain
                domain=".cirilla.ai",  # Share across all *.cirilla.ai
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            # Set WebSocket token cookie (non-HttpOnly so JS can read it)
            response.set_cookie(
                key="ws_token",
                value=result["session_id"],
                httponly=False,  # Allow JS access for WebSocket
                secure=True,  # Require HTTPS
                samesite="none",  # Allow cross-subdomain
                domain=".cirilla.ai",  # Share across all *.cirilla.ai
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
            # Use domain=".cirilla.ai" to work across all subdomains
            response.set_cookie(
                key="session_id",
                value=result["session_id"],
                httponly=True,
                secure=True,  # Require HTTPS
                samesite="none",  # Allow cross-subdomain
                domain=".cirilla.ai",  # Share across all *.cirilla.ai
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            # Set WebSocket token cookie (non-HttpOnly so JS can read it)
            response.set_cookie(
                key="ws_token",
                value=result["session_id"],
                httponly=False,  # Allow JS access for WebSocket
                secure=True,  # Require HTTPS
                samesite="none",  # Allow cross-subdomain
                domain=".cirilla.ai",  # Share across all *.cirilla.ai
                max_age=7 * 24 * 60 * 60  # 7 days
            )

            return AuthResponse(
                success=True,
                message="Login successful",
                user=result["user"],
                session_token=result["session_id"]  # Include for Word Add-in
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
    Upload and parse a policy document.

    Parses the document to extract metadata and sections,
    stores in database, and updates vector store for RAG.

    Args:
        file: Policy document (PDF, TXT, or MD)

    Returns:
        Parsed policy with metadata and sections
    """
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.txt', '.md', '.docx']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Save uploaded file
        policy_dir = Path(settings.upload_dir) / "policies" / user.company_id
        policy_dir.mkdir(parents=True, exist_ok=True)

        file_path = policy_dir / file.filename
        content = await file.read()
        file_size = len(content)

        with open(file_path, "wb") as f:
            f.write(content)

        # Create policy using PolicyService
        from .services.policy_service import PolicyService
        db = next(get_db())
        try:
            policy_service = PolicyService(db)

            # Parse and create policy with sections
            policy = policy_service.create_policy_from_upload(
                file_path=str(file_path),
                original_filename=file.filename,
                file_size=file_size,
                file_type=file_ext.lstrip('.'),
                company_id=user.company_id,
                user_id=user.id
            )

            # Update vector store with sections
            from .vector_store.embeddings import PolicyEmbeddings
            embeddings = PolicyEmbeddings()

            # Embed each section separately with metadata (skip empty sections)
            embedded_count = 0
            for section in policy.sections:
                # Skip sections with empty or whitespace-only content
                if not section.section_content or not section.section_content.strip():
                    logger.warning(f"Skipping empty section {section.id} in policy {policy.id}")
                    continue

                try:
                    embeddings.embed_policy_section(
                        section_id=section.id,
                        section_content=section.section_content,
                        metadata={
                            'policy_id': policy.id,
                            'policy_number': policy.policy_number or '',
                            'policy_title': policy.title,
                            'section_id': section.id,
                            'section_number': section.section_number or '',
                            'section_title': section.section_title or '',
                            'company_id': user.company_id,
                            'version': policy.version
                        },
                        company_id=user.company_id
                    )
                    embedded_count += 1
                except Exception as e:
                    logger.error(f"Error embedding section {section.id}: {e}")
                    # Continue with other sections instead of failing completely
                    continue

            logger.info(f"Policy uploaded by {user.email}: {policy.title} ({len(policy.sections)} sections, {embedded_count} embedded)")

            return {
                "success": True,
                "policy": policy.to_dict(include_sections=True),
                "parsing_status": policy.status,
                "message": f"Policy uploaded and parsed successfully ({embedded_count} sections embedded)"
            }

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to upload policy: {str(e)}")


@app.get("/api/policies")
async def list_policies(
    user: DBUser = Depends(require_auth),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: DBSessionType = Depends(get_db)
):
    """
    List user's uploaded policies with structured data.

    Args:
        status: Filter by status ('active', 'archived', 'draft')
        search: Search by title or policy_number

    Returns:
        List of policies with full metadata and section counts
    """
    try:
        from .services.policy_service import PolicyService
        policy_service = PolicyService(db)

        policies = policy_service.list_policies(
            company_id=user.company_id,
            status=status,
            search=search
        )

        # Add section count to each policy
        policies_data = []
        for policy in policies:
            policy_dict = policy.to_dict(include_sections=False)
            policy_dict['section_count'] = len(policy.sections) if policy.sections else 0
            policies_data.append(policy_dict)

        return {
            "success": True,
            "policies": policies_data,
            "total": len(policies_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List policies error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list policies")


@app.get("/api/policies/{policy_id}")
async def get_policy(
    policy_id: str,
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
):
    """
    Get a single policy with all sections and version history.

    Args:
        policy_id: Policy ID

    Returns:
        Policy with full details
    """
    try:
        from .services.policy_service import PolicyService
        policy_service = PolicyService(db)

        policy = policy_service.get_policy(policy_id, user.company_id)

        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        return {
            "success": True,
            "policy": policy.to_dict(include_sections=True, include_versions=True)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get policy error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get policy")


@app.put("/api/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    update_data: dict,
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
):
    """
    Update a policy's metadata and/or sections.

    Creates a version snapshot before updating.

    Args:
        policy_id: Policy ID
        update_data: Fields to update

    Returns:
        Updated policy
    """
    try:
        from .services.policy_service import PolicyService
        policy_service = PolicyService(db)

        policy = policy_service.update_policy(
            policy_id=policy_id,
            company_id=user.company_id,
            user_id=user.id,
            update_data=update_data,
            change_description=update_data.get('change_description')
        )

        # Update vector store if sections or content changed
        if 'sections' in update_data or 'full_text' in update_data:
            from .vector_store.embeddings import PolicyEmbeddings
            embeddings = PolicyEmbeddings()

            # Delete old embeddings
            embeddings.delete_policy_embeddings(policy_id, user.company_id)

            # Re-embed sections (skip empty ones)
            for section in policy.sections:
                if not section.section_content or not section.section_content.strip():
                    continue

                try:
                    embeddings.embed_policy_section(
                        section_id=section.id,
                        section_content=section.section_content,
                        metadata={
                            'policy_id': policy.id,
                            'policy_number': policy.policy_number or '',
                            'policy_title': policy.title,
                            'section_id': section.id,
                            'section_number': section.section_number or '',
                            'section_title': section.section_title or '',
                            'company_id': user.company_id,
                            'version': policy.version
                        },
                        company_id=user.company_id
                    )
                except Exception as e:
                    logger.error(f"Error embedding section {section.id} during update: {e}")
                    continue

        logger.info(f"Policy {policy_id} updated by {user.email}")

        return {
            "success": True,
            "policy": policy.to_dict(include_sections=True),
            "message": "Policy updated successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update policy error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update policy")


@app.delete("/api/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
):
    """
    Delete a policy and all related data.

    Removes:
    - Policy record (CASCADE deletes sections and versions)
    - Vector store embeddings
    - Original file from disk

    Args:
        policy_id: Policy ID

    Returns:
        Success confirmation
    """
    try:
        from .services.policy_service import PolicyService
        from .vector_store.embeddings import PolicyEmbeddings

        policy_service = PolicyService(db)
        embeddings = PolicyEmbeddings()

        # Delete vector store embeddings first
        embeddings.delete_policy_embeddings(policy_id, user.company_id)

        # Delete policy (CASCADE handles sections and versions)
        success = policy_service.delete_policy(policy_id, user.company_id)

        if not success:
            raise HTTPException(status_code=404, detail="Policy not found")

        logger.info(f"Policy {policy_id} deleted by {user.email}")

        return {
            "success": True,
            "message": "Policy deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete policy error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete policy")


# Policy Chat Models
class PolicyChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class PolicyChatResponse(BaseModel):
    response: str
    policy_id: str
    timestamp: str


@app.post("/api/policies/{policy_id}/chat", response_model=PolicyChatResponse)
async def policy_chat(
    policy_id: str,
    request: PolicyChatRequest,
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
):
    """
    Chat with an AI assistant about a specific policy.

    Args:
        policy_id: Policy ID
        request: Chat request with message and optional conversation history

    Returns:
        AI assistant response
    """
    try:
        from .services.policy_service import PolicyService

        # Validate message
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        if len(request.message) > 5000:
            raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)")

        # Get policy and verify access
        policy_service = PolicyService(db)
        policy = policy_service.get_policy(policy_id, user.company_id)

        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        # Build policy context
        context_parts = [
            f"POLICY METADATA:",
            f"Title: {policy.title}",
            f"Policy Number: {policy.policy_number or 'N/A'}",
            f"Version: {policy.version}",
            f"Effective Date: {policy.effective_date or 'N/A'}",
            f"Status: {policy.status}",
            "",
            "POLICY CONTENT:",
        ]

        # Add sections
        if policy.sections and len(policy.sections) > 0:
            context_parts.append("\nPOLICY SECTIONS:")
            for section in sorted(policy.sections, key=lambda s: s.section_order):
                section_header = f"\n{section.section_number}. {section.section_title}" if section.section_number and section.section_title else f"\nSection {section.section_order + 1}"
                context_parts.append(section_header)
                context_parts.append(section.section_content)
        elif policy.full_text:
            context_parts.append(policy.full_text)

        policy_context = "\n".join(context_parts)

        # Truncate if too long (keep under 100k chars)
        if len(policy_context) > 100000:
            policy_context = policy_context[:100000] + "\n... (content truncated)"
            logger.warning(f"Policy context truncated for policy {policy_id}")

        # Build system prompt
        system_prompt = f"""You are an AI assistant helping users understand policy documents.
You have access to the full content of the policy titled "{policy.title}".

{policy_context}

Answer user questions about this policy clearly and accurately. Be helpful and conversational.
If information is not in the policy, say so - do not make up information.
Provide specific references to sections when applicable."""

        # Initialize Gemini
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.7,
            max_output_tokens=2048
        )

        # Build messages for Gemini
        messages = [("system", system_prompt)]

        # Add conversation history if provided
        if request.conversation_history:
            for msg in request.conversation_history[-10:]:  # Only last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role and content:
                    messages.append((role, content))

        # Add current user message
        messages.append(("user", request.message))

        # Call Gemini
        logger.info(f"Policy chat for {policy_id} by {user.email}: {request.message[:50]}...")
        response = await llm.ainvoke(messages)

        return PolicyChatResponse(
            response=response.content,
            policy_id=policy_id,
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Policy chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@app.post("/api/contracts/upload", response_model=AnalysisResponse)
async def upload_contract(
    file: UploadFile = File(...),
    request: Request = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
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

        # Get region from request state (injected by middleware)
        region_code = getattr(request.state, "region_code", None) if request else None

        # Create database record
        db_job = DBAnalysisJob(
            job_id=job_id,
            user_id=user.id,
            filename=file.filename,
            upload_path=str(upload_path),
            status="uploaded",
            source="web_upload"
        )
        db.add(db_job)
        db.commit()

        # Also add to in-memory dict for backwards compatibility
        job_data = {
            "job_id": job_id,
            "status": "uploaded",
            "filename": file.filename,
            "upload_path": str(upload_path),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "user_id": user.id,
            "company_name": user.company_name,
            "region_code": region_code  # Store region for background task
        }
        analysis_jobs[job_id] = job_data

        logger.info(f"Contract uploaded and persisted: {job_id} - {file.filename}")

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
async def list_contracts(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
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


@app.get("/api/analysis/history")
async def get_analysis_history(
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db),
    page: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    source: Optional[str] = Query(None)
):
    """
    Get analysis history for the current user.

    Args:
        page: Page number (0-indexed)
        limit: Number of results per page (max 100)
        source: Optional filter by source ('web_upload' or 'word_addin')

    Returns:
        Paginated list of analysis results with metadata
    """
    try:
        # Build query
        query = db.query(DBAnalysisJob).filter(DBAnalysisJob.user_id == user.id)

        # Apply source filter if provided
        if source and source in ['web_upload', 'word_addin']:
            query = query.filter(DBAnalysisJob.source == source)

        # Get total count
        total_count = query.count()

        # Get paginated results
        analyses = query.order_by(DBAnalysisJob.created_at.desc()).offset(page * limit).limit(limit).all()

        # Transform results for frontend
        results = []
        for analysis in analyses:
            result_dict = {
                "job_id": analysis.job_id,
                "filename": analysis.filename,
                "status": analysis.status,
                "source": analysis.source,
                "created_at": analysis.created_at.isoformat(),
                "updated_at": analysis.updated_at.isoformat()
            }

            # Include summary if analysis is completed and has results
            if analysis.status == "completed" and analysis.result_json:
                try:
                    full_results = json.loads(analysis.result_json)

                    # Calculate summary from actual analysis_results (same logic as status endpoint)
                    if "analysis_results" in full_results:
                        analysis_results = full_results["analysis_results"]
                        total_clauses = len(analysis_results)

                        # Count compliant/non-compliant based on the 'compliant' field
                        compliant = sum(1 for r in analysis_results if r.get("compliant", False))
                        non_compliant = sum(1 for r in analysis_results if not r.get("compliant", True))

                        compliance_rate = (compliant / total_clauses * 100) if total_clauses > 0 else 0

                        # Determine overall risk from analysis results
                        risk_levels = [r.get("risk_level", "").lower() for r in analysis_results if r.get("risk_level")]
                        if "critical" in risk_levels:
                            overall_risk = "Critical"
                        elif "high" in risk_levels:
                            overall_risk = "High"
                        elif "medium" in risk_levels:
                            overall_risk = "Medium"
                        elif "low" in risk_levels:
                            overall_risk = "Low"
                        else:
                            overall_risk = "Unknown"

                        result_dict["summary"] = {
                            "total_clauses": total_clauses,
                            "compliant_clauses": compliant,
                            "non_compliant_clauses": non_compliant,
                            "compliance_rate": compliance_rate,
                            "overall_risk": overall_risk
                        }
                    # Fallback to summary field if analysis_results not available
                    elif "summary" in full_results:
                        summary = full_results["summary"]
                        # Normalize old format to new format
                        if "total_clauses_reviewed" in summary:
                            total = summary.get("total_clauses_reviewed", 0)
                            compliant = summary.get("compliant_clauses", 0)
                            result_dict["summary"] = {
                                "total_clauses": total,
                                "compliant_clauses": compliant,
                                "non_compliant_clauses": summary.get("non_compliant_clauses", total - compliant),
                                "compliance_rate": (compliant / total * 100) if total > 0 else 0,
                                "overall_risk": summary.get("overall_risk_assessment", "Unknown").title()
                            }
                        else:
                            result_dict["summary"] = summary
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse result_json for job {analysis.job_id}")

            results.append(result_dict)

        return {
            "success": True,
            "analyses": results,
            "pagination": {
                "total": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit
            }
        }

    except Exception as e:
        logger.error(f"Error fetching analysis history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis history")


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
    db = next(get_db())
    try:
        logger.info(f"Running analysis for job: {job_id}")

        # Get job from database
        db_job = db.query(DBAnalysisJob).filter(DBAnalysisJob.job_id == job_id).first()
        if not db_job:
            logger.error(f"Job {job_id} not found in database")
            return

        # Get user for company_id
        user = db.query(DBUser).filter(DBUser.id == db_job.user_id).first()
        company_id = user.company_id if user else None

        # Get region_code from job data
        region_code = analysis_jobs.get(job_id, {}).get("region_code")

        logger.info(f"Using company-specific policies for company: {company_id}{' region: ' + region_code if region_code else ''}")

        # Initialize analyzer with company_id and region_code
        analyzer = ContractAnalyzer(company_id=company_id, region_code=region_code)

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

        # Update database with results
        db_job.status = "completed"
        db_job.updated_at = datetime.now()
        db_job.output_path = str(output_path)
        db_job.result_json = json.dumps(results)  # Store full results as JSON
        db.commit()

        # Also update in-memory for backwards compatibility
        if job_id in analysis_jobs:
            analysis_jobs[job_id].update({
                "status": "completed",
                "updated_at": datetime.now().isoformat(),
                "output_path": str(output_path),
                "results": results
            })

        logger.info(f"Analysis completed and persisted for job: {job_id}")

    except Exception as e:
        logger.error(f"Error in analysis job {job_id}: {e}")
        # Update database with error
        db_job = db.query(DBAnalysisJob).filter(DBAnalysisJob.job_id == job_id).first()
        if db_job:
            db_job.status = "failed"
            db_job.updated_at = datetime.now()
            db_job.error = str(e)
            db.commit()

        # Also update in-memory for backwards compatibility
        if job_id in analysis_jobs:
            analysis_jobs[job_id].update({
                "status": "failed",
                "updated_at": datetime.now().isoformat(),
                "error": str(e)
            })
    finally:
        db.close()


@app.get("/api/contracts/{job_id}/status")
async def get_analysis_status(
    request: Request,
    job_id: str,
    auth_service: AuthService = Depends(get_auth_service),
    db: DBSessionType = Depends(get_db)
):
    """
    Get the status of a contract analysis job.

    Args:
        job_id: Job ID

    Returns:
        Job status and results (if completed)
    """
    # First, try to get job from database (persistent storage)
    db_job = db.query(DBAnalysisJob).filter(DBAnalysisJob.job_id == job_id).first()

    if not db_job:
        # Fallback to in-memory (for backward compatibility with active jobs)
        if job_id not in analysis_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        job = analysis_jobs[job_id]
        use_db = False
    else:
        use_db = True

    # Check ownership if user is authenticated
    session_id = request.cookies.get("session_id")
    current_user = auth_service.get_user_by_session(session_id) if session_id else None

    if current_user:
        # Check ownership from database or in-memory
        owner_user_id = db_job.user_id if use_db else job.get("user_id")
        if owner_user_id and owner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied - not your contract")

    # Map backend status to frontend status
    status_map = {
        "uploaded": "pending",
        "analyzing": "processing",
        "completed": "completed",
        "failed": "failed"
    }

    # Get status from database or in-memory
    job_status = db_job.status if use_db else job["status"]

    # Calculate progress
    progress = 0
    if job_status == "uploaded":
        progress = 0
    elif job_status == "analyzing":
        progress = 50  # Default to 50% during analysis
    elif job_status == "completed":
        progress = 100
    elif job_status == "failed":
        progress = 0

    response = {
        "job_id": job_id,
        "status": status_map.get(job_status, job_status),
        "progress": progress,
        "message": db_job.error if (use_db and db_job.error) else job.get("message", "") if not use_db else "",
    }

    # Include full result with analysis details if completed
    if job_status == "completed":
        # Get results from database or in-memory
        if use_db and db_job.result_json:
            try:
                results = json.loads(db_job.result_json)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse result_json for job {job_id}")
                results = {}
        elif not use_db and "results" in job:
            results = job["results"]
        else:
            results = {}

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

        # Get file info from database or in-memory
        contract_name = db_job.filename if use_db else job["filename"]
        created_at = db_job.created_at.isoformat() if use_db else job["created_at"]
        completed_at = db_job.updated_at.isoformat() if use_db else job["updated_at"]
        output_path = db_job.output_path if use_db else job.get("output_path", "")

        response["result"] = {
            "job_id": job_id,
            "contract_name": contract_name,
            "status": "completed",
            "created_at": created_at,
            "completed_at": completed_at,
            "analysis_results": analysis_results,
            "summary": summary,
            "output_files": {
                "reviewed_contract": output_path,
                "detailed_report": output_path.replace(".docx", "_DETAILED_REPORT.docx") if output_path else "",
                "html_summary": output_path.replace(".docx", "_SUMMARY.html") if output_path else ""
            }
        }

    # Include error if failed
    if job_status == "failed":
        if use_db and db_job.error:
            response["message"] = db_job.error
        elif not use_db and "error" in job:
            response["message"] = job["error"]

    return response


@app.get("/api/contracts/{job_id}/download/{report_type}")
async def download_report(
    job_id: str,
    report_type: str,
    db: DBSessionType = Depends(get_db)
):
    """
    Download analysis report.

    Args:
        job_id: Job ID
        report_type: Type of report (reviewed, detailed, html)

    Returns:
        Report file
    """
    # First, try to get job from database (persistent storage)
    db_job = db.query(DBAnalysisJob).filter(DBAnalysisJob.job_id == job_id).first()

    if not db_job:
        # Fallback to in-memory (for backward compatibility with active jobs)
        if job_id not in analysis_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        job = analysis_jobs[job_id]
        use_db = False
    else:
        use_db = True

    # Check if completed
    job_status = db_job.status if use_db else job["status"]
    if job_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {job_status}"
        )

    # Get output path and filename
    output_path = db_job.output_path if use_db else job.get("output_path")
    filename = db_job.filename if use_db else job.get("filename", "contract.docx")

    if not output_path:
        raise HTTPException(status_code=404, detail="Output file not found")

    # Determine file path based on report type
    if report_type == "reviewed":
        file_path = output_path
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        download_filename = f"reviewed_{filename}"
    elif report_type == "detailed":
        file_path = output_path.replace(".docx", "_DETAILED_REPORT.docx")
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        download_filename = f"detailed_report_{filename}"
    elif report_type == "html":
        file_path = output_path.replace(".docx", "_SUMMARY.html")
        media_type = "text/html"
        download_filename = f"summary_{filename.replace('.docx', '.html')}"
    else:
        raise HTTPException(status_code=400, detail="Invalid report type")

    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"{report_type} report not found")

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=download_filename
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
async def chat_with_assistant(
    job_id: str,
    chat_request: ChatRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
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


# ===== Document Endpoints =====

@app.post("/api/documents")
async def create_document(
    request: CreateDocumentRequest,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Create a new document.

    Args:
        request: Document creation request
        user: Authenticated user (creator)
        document_service: Document service instance

    Returns:
        Created document data or error
    """
    result = document_service.create_document(
        title=request.title,
        created_by_user_id=user.id,
        negotiation_id=request.negotiation_id,
        analysis_job_id=request.analysis_job_id,
        import_source=request.import_source
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result["document"]


@app.get("/api/documents")
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    List user's documents with pagination.

    Args:
        limit: Maximum number of results (default: 50)
        offset: Number of results to skip (default: 0)
        user: Authenticated user
        document_service: Document service instance

    Returns:
        List of documents with pagination metadata
    """
    result = document_service.list_user_documents(
        user_id=user.id,
        limit=limit,
        offset=offset
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@app.get("/api/documents/{document_id}")
async def get_document(
    document_id: str,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get document details.

    Args:
        document_id: ID of the document
        user: Authenticated user
        document_service: Document service instance

    Returns:
        Document data or error
    """
    result = document_service.get_document(
        document_id=document_id,
        user_id=user.id
    )

    if not result["success"]:
        if result.get("error") == "Access denied":
            raise HTTPException(status_code=403, detail="You do not have access to this document")
        raise HTTPException(status_code=404, detail=result["error"])

    return result["document"]


@app.patch("/api/documents/{document_id}")
async def update_document(
    document_id: str,
    request: UpdateDocumentRequest,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Update document metadata or content state.

    Args:
        document_id: ID of the document
        request: Update request with optional fields
        user: Authenticated user
        document_service: Document service instance

    Returns:
        Updated document data or error
    """
    result = document_service.update_document(
        document_id=document_id,
        user_id=user.id,
        title=request.title,
        status=request.status,
        yjs_state_vector=request.yjs_state_vector
    )

    if not result["success"]:
        if result.get("error") == "Access denied":
            raise HTTPException(status_code=403, detail="You do not have access to this document")
        raise HTTPException(status_code=404, detail=result["error"])

    return result["document"]


@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Delete a document (only creator can delete).

    Args:
        document_id: ID of the document
        user: Authenticated user
        document_service: Document service instance

    Returns:
        Success status
    """
    result = document_service.delete_document(
        document_id=document_id,
        user_id=user.id
    )

    if not result["success"]:
        if result.get("error") == "Access denied":
            raise HTTPException(status_code=403, detail="Only the creator can delete this document")
        raise HTTPException(status_code=404, detail=result["error"])

    return {"status": "success", "message": "Document deleted successfully"}


@app.post("/api/documents/{document_id}/content")
async def update_document_content(
    document_id: str,
    file: UploadFile = File(...),
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
):
    """
    Update document content by uploading a new DOCX file.
    Used by SuperDoc editor for saving document changes.

    Args:
        document_id: ID of the document
        file: Uploaded DOCX file
        user: Authenticated user
        db: Database session

    Returns:
        Updated document data
    """
    # Verify file type
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only DOCX files are supported")

    # Get document service
    document_service = DocumentService(db)

    # Check if user has access to the document
    if not document_service.can_user_access(document_id, user.id):
        raise HTTPException(status_code=403, detail="You do not have access to this document")

    # Get the document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Initialize DOCX parser service
    docx_parser = DocxParserService()

    # Save the uploaded file
    try:
        file_path, file_name, file_size = await docx_parser.save_uploaded_file(
            file, document_id
        )

        # Update document with new file path
        document.original_file_path = file_path
        document.original_file_name = file_name
        document.original_file_size = file_size
        document.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(document)

        # Return updated document
        return {
            "id": document.id,
            "title": document.title,
            "status": document.status,
            "created_by_user_id": document.created_by_user_id,
            "negotiation_id": document.negotiation_id,
            "analysis_job_id": document.analysis_job_id,
            "original_file_path": document.original_file_path,
            "original_file_name": document.original_file_name,
            "original_file_size": document.original_file_size,
            "import_source": document.import_source,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update document content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save document: {str(e)}")


@app.get("/api/documents/{document_id}/collaborators")
async def get_collaborators(
    document_id: str,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Get list of collaborators for a document.

    Args:
        document_id: ID of the document
        user: Authenticated user
        document_service: Document service instance

    Returns:
        List of collaborators with user details
    """
    result = document_service.get_collaborators(
        document_id=document_id,
        user_id=user.id
    )

    if not result["success"]:
        if result.get("error") == "Access denied":
            raise HTTPException(status_code=403, detail="You do not have access to this document")
        raise HTTPException(status_code=404, detail=result["error"])

    return {"collaborators": result["collaborators"]}


@app.post("/api/documents/{document_id}/collaborators")
async def add_collaborator(
    document_id: str,
    request: AddCollaboratorRequest,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Add a collaborator to a document.

    Args:
        document_id: ID of the document
        request: Collaborator addition request
        user: Authenticated user (must be existing collaborator)
        document_service: Document service instance

    Returns:
        Success status with collaborator details
    """
    result = document_service.add_collaborator(
        document_id=document_id,
        user_id=request.user_id,
        added_by_user_id=user.id,
        permission=request.permission
    )

    if not result["success"]:
        if result.get("error") == "Access denied":
            raise HTTPException(status_code=403, detail="You do not have access to this document")
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# ===== DOCX Import Endpoints =====

@app.post("/api/documents/import-docx")
async def import_docx(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    import_source: str = Form("original"),
    negotiation_id: Optional[str] = Form(None),
    analysis_job_id: Optional[str] = Form(None),
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
):
    """
    Import a DOCX file and convert it to a Lexical document.

    Args:
        file: Uploaded DOCX file
        title: Document title (defaults to filename)
        import_source: 'original' or 'ai_redlined'
        negotiation_id: Optional link to negotiation
        analysis_job_id: Optional link to AI analysis
        user: Authenticated user
        db: Database session

    Returns:
        Document ID, HTML content, track changes, and metadata
    """
    # Validate file
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="File must be a .docx file")

    # Read file content
    file_content = await file.read()

    # Limit file size to 10MB
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")

    # Generate document ID
    document_id = str(uuid.uuid4())

    # Initialize services
    docx_parser = DocxParserService()
    document_service = DocumentService(db)

    # Save file to disk
    file_info = docx_parser.save_uploaded_file(file_content, document_id, file.filename)

    # Parse DOCX and extract content
    structure = docx_parser.parse_docx_structure(file_info["file_path"])
    if not structure["success"]:
        raise HTTPException(status_code=500, detail=f"Failed to parse DOCX: {structure.get('error')}")

    # Extract track changes
    track_changes = docx_parser.extract_track_changes(file_info["file_path"])

    # Convert to HTML
    html_result = docx_parser.convert_to_html(file_info["file_path"])
    if not html_result["success"]:
        raise HTTPException(status_code=500, detail=f"Failed to convert to HTML: {html_result.get('error')}")

    # Get metadata
    metadata = docx_parser.get_document_metadata(file_info["file_path"])

    # Use title from form or metadata or filename
    doc_title = title or metadata.get("title") or file.filename.replace('.docx', '')

    # Create document in database
    result = document_service.create_document(
        title=doc_title,
        created_by_user_id=user.id,
        negotiation_id=negotiation_id,
        analysis_job_id=analysis_job_id,
        import_source=import_source
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))

    # Update document with file info and HTML content
    doc = db.query(Document).filter(Document.id == result["document"]["id"]).first()
    if doc:
        doc.original_file_path = file_info["file_path"]
        doc.original_file_name = file_info["file_name"]
        doc.original_file_size = file_info["file_size"]

        # Validate HTML is not empty
        if not html_result["html"] or html_result["html"].strip() == "":
            logger.error("HTML conversion resulted in empty content")
            raise HTTPException(status_code=500, detail="DOCX conversion produced empty content")

        # Store the HTML in lexical_state so frontend can convert it
        # Frontend will convert HTML to Lexical and save it back
        # NOTE: yjs_state_vector is reserved for Yjs binary data only
        doc.lexical_state = html_result["html"]
        logger.info(f"Storing HTML content for document {doc.id}: {len(html_result['html'])} characters")

        # CRITICAL: Commit to database before returning
        db.commit()
        db.refresh(doc)
        logger.info(f"Document {doc.id} updated and committed successfully")

    # Store track changes in database
    from .database import DocumentChange
    for change in track_changes:
        doc_change = DocumentChange(
            id=str(uuid.uuid4()),
            document_id=result["document"]["id"],
            change_type=change["type"],
            position=change["position"],
            content=change["content"],
            user_id=user.id,  # Will need to map author name to user later
            change_metadata=json.dumps({
                "author": change["author"],
                "date": change["date"],
                "change_id": change["change_id"]
            })
        )
        db.add(doc_change)

    db.commit()

    return {
        "success": True,
        "document_id": result["document"]["id"],
        "html": html_result["html"],
        "track_changes": track_changes,
        "metadata": metadata,
        "paragraph_count": structure.get("paragraph_count", 0),
        "table_count": structure.get("table_count", 0)
    }


@app.get("/api/documents/{document_id}/original")
async def download_original_docx(
    document_id: str,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service),
    db: DBSessionType = Depends(get_db)
):
    """
    Download the original DOCX file for a document.

    Args:
        document_id: ID of the document
        user: Authenticated user
        document_service: Document service instance
        db: Database session

    Returns:
        DOCX file as download
    """
    # Check access
    if not document_service.can_user_access(document_id, user.id):
        raise HTTPException(status_code=403, detail="You do not have access to this document")

    # Get document
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.original_file_path:
        raise HTTPException(status_code=404, detail="Original file not found")

    # Check if file exists
    if not os.path.exists(doc.original_file_path):
        raise HTTPException(status_code=404, detail="Original file not found on disk")

    # Return file
    return FileResponse(
        path=doc.original_file_path,
        filename=doc.original_file_name or "document.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.get("/api/documents/{document_id}/track-changes")
async def get_track_changes(
    document_id: str,
    user: DBUser = Depends(require_auth),
    document_service: DocumentService = Depends(get_document_service),
    db: DBSessionType = Depends(get_db)
):
    """
    Get track changes for a document.

    Args:
        document_id: ID of the document
        user: Authenticated user
        document_service: Document service instance
        db: Database session

    Returns:
        List of track changes
    """
    # Check access
    if not document_service.can_user_access(document_id, user.id):
        raise HTTPException(status_code=403, detail="You do not have access to this document")

    # Get track changes
    from .database import DocumentChange
    changes = db.query(DocumentChange).filter(
        DocumentChange.document_id == document_id
    ).order_by(DocumentChange.created_at).all()

    return {
        "success": True,
        "changes": [
            {
                "id": change.id,
                "type": change.change_type,
                "position": change.position,
                "content": change.content,
                "user_id": change.user_id,
                "created_at": change.created_at.isoformat(),
                "metadata": json.loads(change.change_metadata) if change.change_metadata else {}
            }
            for change in changes
        ]
    }


# ===== Word Add-in Endpoints =====

@app.post("/api/word-addin/analyze-text")
async def analyze_text_from_addin(
    request: WordAddinAnalyzeTextRequest,
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
):
    """
    Analyze document text directly from Word Add-in.

    This endpoint accepts raw document text and paragraphs, analyzes them
    using the existing ContractAnalyzer, and returns results with paragraph
    indices for Word navigation.

    Args:
        request: Document text and paragraphs array
        user: Authenticated user

    Returns:
        Analysis results with paragraph indices for Word operations
    """
    try:
        logger.info(f"Word Add-in analysis request from user {user.email}")
        logger.info(f"Document: {len(request.document_text)} chars, {len(request.paragraphs)} paragraphs")

        if not request.paragraphs:
            raise HTTPException(
                status_code=400,
                detail="No paragraphs provided for analysis"
            )

        # Initialize analyzer with user's company policies
        analyzer = ContractAnalyzer(company_id=user.company_id)

        # Convert string paragraphs to the expected format
        # Use original Word indices if provided, otherwise use array index
        formatted_paragraphs = []
        for idx, para in enumerate(request.paragraphs):
            if para.strip():  # Skip empty paragraphs
                # Use original Word index if available
                word_index = request.paragraph_indices[idx] if request.paragraph_indices and idx < len(request.paragraph_indices) else idx
                formatted_paragraphs.append({
                    "text": para.strip(),
                    "index": word_index,  # Use original Word paragraph index
                    "style": "Normal",
                    "is_heading": False
                })

        # Extract clauses from provided paragraphs
        clauses = analyzer.clause_extractor.extract_clauses_from_paragraphs(
            formatted_paragraphs
        )

        if not clauses:
            raise HTTPException(
                status_code=400,
                detail="No analyzable clauses found in document"
            )

        logger.info(f"Extracted {len(clauses)} clauses for analysis")

        # Run batch analysis (reusing existing logic)
        if analyzer.batch_mode and len(clauses) > 0:
            batch_result = analyzer.batch_analyzer.analyze_contract_batch(
                contract_text=request.document_text,
                clauses=clauses
            )
            analysis_results = batch_result["analysis_results"]
        else:
            # Single clause analysis fallback
            classified_clauses = analyzer.clause_extractor.classify_all_clauses_sync(clauses)
            analysis_results = []
            for clause in classified_clauses:
                result = analyzer.analyze_single_clause(clause)
                analysis_results.append(result)

        # Map results to paragraph indices
        def find_paragraph_index(clause_text: str, paragraphs: List[str], word_indices: Optional[List[int]]) -> int:
            """Find the Word paragraph index that contains the clause text."""
            # Normalize for comparison
            clause_normalized = clause_text.strip().lower()[:100]

            for i, para in enumerate(paragraphs):
                para_normalized = para.strip().lower()
                if clause_normalized in para_normalized or para_normalized in clause_normalized:
                    # Return the original Word index if available
                    if word_indices and i < len(word_indices):
                        return word_indices[i]
                    return i

            # If no direct match, try to find best match
            best_match_idx = 0
            best_match_score = 0

            for i, para in enumerate(paragraphs):
                # Count matching words
                clause_words = set(clause_normalized.split())
                para_words = set(para.strip().lower().split())
                common_words = clause_words.intersection(para_words)
                score = len(common_words)

                if score > best_match_score:
                    best_match_score = score
                    best_match_idx = i

            # Return the original Word index for the best match
            if word_indices and best_match_idx < len(word_indices):
                return word_indices[best_match_idx]
            return best_match_idx

        # Transform results for Word Add-in format
        transformed_results = []
        for idx, result in enumerate(analysis_results):
            clause_text = result.get("text", result.get("clause_text", ""))
            paragraph_index = find_paragraph_index(clause_text, request.paragraphs, request.paragraph_indices)

            transformed = {
                "clause_number": idx + 1,
                "clause_text": clause_text,
                "clause_type": result.get("type", result.get("clause_type", "Unknown")),
                "paragraph_index": paragraph_index,
                "compliance_status": "Compliant" if result.get("compliant", True) else "Non-Compliant",
                "risk_level": result.get("risk_level", "Medium"),
                "issues": result.get("issues", []),
                "recommendations": result.get("recommendations", []),
                "policy_references": result.get("policy_references", result.get("relevant_policies", [])),
                "suggested_text": result.get("suggested_alternative", result.get("suggested_text"))
            }
            transformed_results.append(transformed)

        # Generate summary
        total_clauses = len(transformed_results)
        compliant_count = sum(1 for r in transformed_results if r["compliance_status"] == "Compliant")
        non_compliant_count = total_clauses - compliant_count

        critical_count = sum(1 for r in transformed_results if r["risk_level"] == "Critical")
        high_count = sum(1 for r in transformed_results if r["risk_level"] == "High")
        medium_count = sum(1 for r in transformed_results if r["risk_level"] == "Medium")
        low_count = sum(1 for r in transformed_results if r["risk_level"] == "Low")

        compliance_rate = (compliant_count / total_clauses * 100) if total_clauses > 0 else 100

        # Determine overall risk
        if critical_count > 0:
            overall_risk = "Critical"
        elif high_count > 0:
            overall_risk = "High"
        elif medium_count > 0:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"

        job_id = str(uuid.uuid4())

        logger.info(f"Analysis complete: {compliant_count}/{total_clauses} compliant, overall risk: {overall_risk}")

        # Prepare results to return
        result_data = {
            "job_id": job_id,
            "status": "completed",
            "analysis_results": transformed_results,
            "summary": {
                "total_clauses": total_clauses,
                "compliant_clauses": compliant_count,
                "non_compliant_clauses": non_compliant_count,
                "critical_issues": critical_count,
                "high_risk_issues": high_count,
                "medium_risk_issues": medium_count,
                "low_risk_issues": low_count,
                "compliance_rate": compliance_rate,
                "overall_risk": overall_risk
            }
        }

        # Persist analysis to database
        db_job = DBAnalysisJob(
            job_id=job_id,
            user_id=user.id,
            filename=f"Word_Document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            upload_path="",  # Word add-in doesn't upload files
            status="completed",
            source="word_addin",
            result_json=json.dumps(result_data)
        )
        db.add(db_job)
        db.commit()

        logger.info(f"Word add-in analysis persisted to database: {job_id}")

        return result_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Word Add-in analysis error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


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


# ===== WebSocket Endpoint for Document Sync =====

@app.websocket("/ws/documents/{document_id}")
async def websocket_document_sync(
    websocket: WebSocket,
    document_id: str
):
    """
    WebSocket endpoint for real-time document synchronization using Yjs.

    Args:
        websocket: WebSocket connection
        document_id: ID of the document to sync

    Protocol:
        - Clients send Yjs updates as binary messages
        - Server broadcasts updates to all other connected clients
        - Server periodically persists state to database
    """
    # MUST accept the WebSocket connection FIRST
    await websocket.accept()

    try:
        # Get database session manually
        db = next(get_db())

        # Get user_id from query params
        user_id = websocket.query_params.get("userId")
        if not user_id:
            logger.warning(f"WebSocket connection rejected: No userId in query params")
            await websocket.close(code=1008, reason="userId required")
            return

        # Validate user AFTER accepting connection
        auth_service = AuthService(db)
        user = db.query(DBUser).filter(DBUser.id == user_id).first()
        if not user:
            logger.warning(f"WebSocket connection rejected: User {user_id} not found")
            await websocket.close(code=1008, reason="User not found")
            return

        # Check document access
        document_service = DocumentService(db)
        if not document_service.can_user_access(document_id, user_id):
            logger.warning(f"WebSocket connection rejected: User {user_id} denied access to document {document_id}")
            await websocket.close(code=1008, reason="Access denied")
            return

        logger.info(f"WebSocket connected: User {user_id} ({user.email}) to document {document_id}")

        # Connect to document room
        await document_sync_service.connect(websocket, document_id, user_id)

        # Notify other users
        await document_sync_service.send_user_joined(
            document_id, user_id, user.email
        )

        try:
            while True:
                # Receive Yjs update from client
                message = await websocket.receive_bytes()

                # Handle the update
                await document_sync_service.handle_client_message(
                    websocket, document_id, user_id, message
                )

        except WebSocketDisconnect:
            logger.info(f"Document sync disconnected for user {user_id} in document {document_id}")
        except Exception as e:
            logger.error(f"Document sync error for user {user_id}: {str(e)}")
        finally:
            # Disconnect and notify others
            document_sync_service.disconnect(websocket, document_id, user_id)
            await document_sync_service.send_user_left(document_id, user_id)

            # Persist current state before disconnect
            await document_sync_service.persist_state(document_id, db)

            # Close database session
            db.close()

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
        finally:
            # Ensure db is closed even on error
            try:
                db.close()
            except:
                pass


@app.websocket("/ws/collab/{document_id}")
async def websocket_collaboration(
    websocket: WebSocket,
    document_id: str
):
    """
    WebSocket endpoint for real-time collaborative editing using pycrdt-websocket.

    This endpoint provides Y.js-based collaborative editing with automatic
    conflict resolution via CRDTs.

    Args:
        websocket: WebSocket connection
        document_id: ID of the document to collaborate on

    Query Parameters:
        userId: User ID for authentication and awareness
        token: Optional JWT token (for future auth)

    Protocol:
        - Uses Y.js sync protocol (handled by pycrdt-websocket)
        - Binary messages containing Y.js updates
        - Automatic conflict resolution via CRDT
    """
    # MUST accept the WebSocket connection FIRST
    await websocket.accept()

    try:
        # Get database session manually
        db = next(get_db())

        # Get user_id from query params
        user_id = websocket.query_params.get("userId")
        if not user_id:
            logger.warning(f"Collaboration WebSocket rejected: No userId in query params")
            await websocket.close(code=1008, reason="userId required")
            return

        # Validate user AFTER accepting connection
        user = db.query(DBUser).filter(DBUser.id == user_id).first()
        if not user:
            logger.warning(f"Collaboration WebSocket rejected: User {user_id} not found")
            await websocket.close(code=1008, reason="User not found")
            return

        # Check document access
        document_service = DocumentService(db)
        if not document_service.can_user_access(document_id, user_id):
            logger.warning(f"Collaboration WebSocket rejected: User {user_id} denied access to document {document_id}")
            await websocket.close(code=1008, reason="Access denied")
            return

        logger.info(f"Collaboration WebSocket connected: User {user_id} ({user.email}) to document {document_id}")

        # Load any persisted state for this document
        document = db.query(Document).filter(Document.id == document_id).first()
        if document and hasattr(document, 'yjs_state_vector') and document.yjs_state_vector:
            import base64
            try:
                state_bytes = base64.b64decode(document.yjs_state_vector)
                await collab_ws_manager.collab_service.load_document_state(document_id, state_bytes)
                logger.info(f"Loaded persisted state for document {document_id}")
            except Exception as e:
                logger.error(f"Failed to load persisted state: {e}")

        try:
            # Handle the collaboration connection
            await collab_ws_manager.handle_connection(
                websocket, document_id, user_id, user.email
            )
        finally:
            # Persist state on disconnect
            try:
                state_b64 = collab_ws_manager.collab_service.get_document_state_base64(document_id)
                if state_b64 and document:
                    document.yjs_state_vector = state_b64
                    document.updated_at = datetime.now()
                    db.commit()
                    logger.info(f"Persisted collaboration state for document {document_id}")
            except Exception as e:
                logger.error(f"Failed to persist collaboration state: {e}")

            db.close()

    except Exception as e:
        logger.error(f"Collaboration WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
        finally:
            try:
                db.close()
            except:
                pass


@app.get("/api/documents/{document_id}/collaborators")
async def get_document_collaborators(
    document_id: str,
    db: DBSessionType = Depends(get_db)
):
    """
    Get list of currently active collaborators on a document.

    Returns awareness state including user info, cursor positions, and selections.
    """
    awareness = collab_ws_manager.get_awareness_for_document(document_id)
    return {
        "document_id": document_id,
        "collaborators": list(awareness.values()),
        "count": len(awareness)
    }


@app.get("/api/collab/rooms")
async def get_active_collaboration_rooms():
    """
    Get all active collaboration rooms (for debugging/monitoring).

    Returns list of room IDs and their client counts.
    """
    rooms = collab_ws_manager.get_active_rooms()
    return {
        "rooms": rooms,
        "total_rooms": len(rooms),
        "total_clients": sum(rooms.values())
    }


# ==================== HocusPocus Integration Endpoints ====================

@app.get("/api/documents/{document_id}/yjs-state")
async def get_document_yjs_state(
    document_id: str,
    db: DBSessionType = Depends(get_db)
):
    """
    Get Y.js state for a document (used by HocusPocus for persistence).

    Returns base64-encoded Y.js state vector.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document_id,
        "state": document.yjs_state_vector if hasattr(document, 'yjs_state_vector') else None
    }


@app.put("/api/documents/{document_id}/yjs-state")
async def update_document_yjs_state(
    document_id: str,
    state_data: dict,
    db: DBSessionType = Depends(get_db)
):
    """
    Update Y.js state for a document (used by HocusPocus for persistence).

    Accepts base64-encoded Y.js state vector.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    state = state_data.get("state")
    if state and hasattr(document, 'yjs_state_vector'):
        document.yjs_state_vector = state
        document.updated_at = datetime.now()
        db.commit()
        logger.info(f"Updated Y.js state for document {document_id}")

    return {
        "document_id": document_id,
        "status": "updated"
    }


@app.get("/api/documents/{document_id}/docx-binary")
async def get_document_docx_binary(
    document_id: str,
    db: DBSessionType = Depends(get_db)
):
    """
    Get the original DOCX file for a document (internal endpoint for collaboration server).

    This endpoint is used by the collaboration server to initialize Y.js state
    with the DOCX binary. No user authentication required as this is server-to-server.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.original_file_path:
        raise HTTPException(status_code=404, detail="No DOCX file available for this document")

    # Read the file
    file_path = document.original_file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="DOCX file not found on disk")

    # Return as binary response
    with open(file_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename={document.title}.docx"
        }
    )


@app.post("/api/documents/{document_id}/enable-collaboration")
async def enable_document_collaboration(
    document_id: str,
    user: DBUser = Depends(require_auth),
    db: DBSessionType = Depends(get_db)
):
    """
    Enable collaboration for a document by creating an initial Y.js state marker.

    This creates a minimal Y.js state that signals collaboration is enabled.
    The first client to connect will initialize the actual document data.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if user has access
    document_service = DocumentService(db)
    if not document_service.can_user_access(document_id, user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Create a minimal Y.js state marker (just 'COLLAB_ENABLED' as base64)
    # This is enough to pass the length > 10 check and signal collaboration is enabled
    collaboration_marker = "Q09MTEJJX0VOQUJMRUQ="  # Base64 of 'COLLAB_ENABLED'

    if hasattr(document, 'yjs_state_vector'):
        document.yjs_state_vector = collaboration_marker
        document.updated_at = datetime.now()
        db.commit()
        logger.info(f"Enabled collaboration for document {document_id}")

    return {
        "document_id": document_id,
        "status": "collaboration_enabled"
    }


@app.get("/api/documents/{document_id}/access")
async def check_document_access(
    document_id: str,
    userId: str,
    db: DBSessionType = Depends(get_db)
):
    """
    Check if a user has access to a document (used by HocusPocus for auth).

    Returns user info if access is granted.
    """
    # Check if user exists
    user = db.query(DBUser).filter(DBUser.id == userId).first()
    if not user:
        raise HTTPException(status_code=403, detail="User not found")

    # Check document access
    document_service = DocumentService(db)
    if not document_service.can_user_access(document_id, userId):
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "document_id": document_id,
        "user_id": userId,
        "user_email": user.email,
        "access": True
    }


# ===== Regional Knowledge Base Debug Endpoint =====

@app.get("/api/debug/regional-kb-info")
async def get_regional_kb_info(
    request: Request,
    user: DBUser = Depends(require_auth)
):
    """
    Debug endpoint to view regional knowledge base information.

    Returns:
        Regional KB status, detected region, collection statistics
    """
    try:
        from .core.config import REGION_CONFIG, get_enabled_regions, settings as config_settings
        from .vector_store.embeddings import PolicyEmbeddings
        from .services.geolocation_service import get_geo_service

        # Get detected region from request state
        region_code = getattr(request.state, "region_code", None)
        client_ip = getattr(request.state, "client_ip", None)

        # Get GeoIP service status
        geo_service = get_geo_service()
        geolocation_available = geo_service.is_available()

        # Get enabled regions
        enabled_regions = get_enabled_regions()

        # Get collection statistics
        embeddings = PolicyEmbeddings()
        collection_stats = {}

        # Global collection stats
        try:
            global_stats = embeddings.get_collection_stats()
            collection_stats["global"] = global_stats
        except Exception as e:
            collection_stats["global"] = {"error": str(e)}

        # Regional collection stats
        for region in enabled_regions:
            try:
                regional_stats = embeddings.get_regional_collection_stats(region)
                collection_stats[region] = regional_stats
            except Exception as e:
                collection_stats[region] = {"error": str(e)}

        return {
            "regional_kb_enabled": config_settings.regional_kb_enabled,
            "detected_region": region_code,
            "client_ip": client_ip,
            "available_regions": enabled_regions,
            "region_config": {
                region: {
                    "region_name": REGION_CONFIG[region]["metadata"]["region_name"],
                    "legal_jurisdiction": REGION_CONFIG[region]["metadata"]["legal_jurisdiction"],
                    "countries": REGION_CONFIG[region]["countries"],
                    "enabled": REGION_CONFIG[region]["enabled"]
                }
                for region in enabled_regions
            },
            "collection_stats": collection_stats,
            "geolocation_database_loaded": geolocation_available,
            "global_weight_multiplier": config_settings.regional_global_weight
        }

    except Exception as e:
        logger.error(f"Error getting regional KB info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
