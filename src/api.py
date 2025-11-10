"""FastAPI application for AI Legal Assistant."""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .core.config import settings
from .agents.contract_analyzer import ContractAnalyzer
from .vector_store.embeddings import PolicyEmbeddings

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for analysis jobs (use database in production)
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


@app.post("/api/contracts/upload", response_model=AnalysisResponse)
async def upload_contract(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
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

        # Initialize job
        analysis_jobs[job_id] = {
            "job_id": job_id,
            "status": "uploaded",
            "filename": file.filename,
            "upload_path": str(upload_path),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

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

        # Initialize analyzer
        analyzer = ContractAnalyzer()

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
async def get_analysis_status(job_id: str):
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
