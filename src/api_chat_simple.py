"""Simplified chat endpoint that provides FULL context to the LLM."""

import json
import logging
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import asyncio
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


async def simple_chat_with_assistant(job_id: str, request, analysis_jobs: dict, llm, settings):
    """
    Simplified chat endpoint that provides complete context to LLM.
    """
    # Check if job exists
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = analysis_jobs[job_id]

    # Check if analysis is complete
    if job.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="Analysis not yet completed."
        )

    # Get the ENTIRE result object
    result = job.get("result", {})

    # Create a comprehensive prompt with ALL data
    system_prompt = f"""You are an AI Legal Assistant chatbot.

CRITICAL: You MUST only use the information provided below. Do not generate or assume any information not in the data.

====================
COMPLETE CONTRACT ANALYSIS DATA
====================

{json.dumps(result, indent=2)}

====================
END OF DATA
====================

INSTRUCTIONS:
1. When asked about non-compliant clauses, look for clauses where:
   - "compliance_status" is "Non-Compliant" OR
   - "compliant" field is false

2. Always cite specific clause numbers and quote actual text from the data

3. If information is not in the data above, say "That information is not in the analysis results"

4. Be specific and accurate - only state what's actually in the data

Now answer the user's question using ONLY the data provided above."""

    # Create messages
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add chat history
    for msg in request.history[-5:]:  # Keep last 5 messages
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    # Add current user message
    messages.append({"role": "user", "content": request.message})

    # Log what we're sending
    logger.info(f"Sending to LLM - System prompt size: {len(system_prompt)} chars")
    logger.info(f"Result object has keys: {list(result.keys())}")

    if "analysis_results" in result:
        analysis_results = result["analysis_results"]
        logger.info(f"Found {len(analysis_results)} analysis results")

        # Count non-compliant
        non_compliant = 0
        for clause in analysis_results:
            if clause.get("compliance_status") == "Non-Compliant" or not clause.get("compliant", True):
                non_compliant += 1
        logger.info(f"Non-compliant clauses: {non_compliant}")

    async def generate_response() -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        try:
            # Get streaming response from LLM
            response = llm.stream(messages)

            for chunk in response:
                if chunk.content:
                    # Format as SSE
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"
                    await asyncio.sleep(0.01)

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
            "X-Accel-Buffering": "no"
        }
    )