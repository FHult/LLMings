"""Session API routes."""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.schemas.session import SessionCreate, SessionResponse
from app.models.session import Session as SessionModel
from app.services.session_orchestrator import SessionOrchestrator

router = APIRouter()


@router.post("/session/create")
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create and run a new council session with Server-Sent Events streaming.

    Args:
        session_data: Session configuration
        db: Database session

    Returns:
        StreamingResponse: SSE stream of session progress
    """
    orchestrator = SessionOrchestrator(db)

    # Create session
    session = await orchestrator.create_session(session_data)

    async def event_generator():
        """Generate SSE events for session progress."""
        try:
            # Send initial session info
            yield f"data: {json.dumps({'type': 'session_created', 'session_id': session.id})}\n\n"

            # Run session and stream updates
            async for update in orchestrator.run_session(session):
                yield f"data: {json.dumps(update)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/session/resume")
async def resume_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a paused council session with Server-Sent Events streaming.

    This endpoint handles resuming sessions that were paused mid-execution.
    It analyzes the resume_state to determine which responses are incomplete
    and re-requests them.

    Args:
        session_data: Session configuration with resume_state
        db: Database session

    Returns:
        StreamingResponse: SSE stream of session progress
    """
    orchestrator = SessionOrchestrator(db)

    # Extract resume state if provided
    resume_state = getattr(session_data, 'resume_state', None)

    # Create session (it will be a new session internally)
    session = await orchestrator.create_session(session_data)

    async def event_generator():
        """Generate SSE events for session progress."""
        try:
            # Send initial session info
            yield f"data: {json.dumps({'type': 'session_created', 'session_id': session.id})}\n\n"

            # Determine where to resume from
            if resume_state:
                # Run session with resume state
                async for update in orchestrator.run_session_with_resume(session, resume_state):
                    yield f"data: {json.dumps(update)}\n\n"
            else:
                # No resume state, run normally
                async for update in orchestrator.run_session(session):
                    yield f"data: {json.dumps(update)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get session details.

    Args:
        session_id: Session ID
        db: Database session

    Returns:
        SessionResponse: Session information
    """
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.id,
        status=session.status,
        created_at=session.created_at,
    )


@router.get("/sessions/test")
async def test_endpoint():
    """Test endpoint to verify API is working."""
    return {"message": "Session API is working!"}
