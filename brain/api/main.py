"""
FastAPI Gateway for Vanguard AI Agent System.

This provides REST and WebSocket endpoints to:
- Trigger workflows
- Check workflow status
- Stream workflow execution
- Monitor system health
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from agents.workflow_langgraph import LangGraphWorkflow
from api.job_manager import Job, job_manager
from api.models import (
    HealthResponse,
    StatsResponse,
    WorkflowResponse,
    WorkflowResult,
    WorkflowStatus,
    WorkflowStreamUpdate,
    WorkflowTriggerRequest,
)
from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize workflow
workflow = LangGraphWorkflow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    logger.info("🚀 FastAPI Gateway starting...")
    logger.info("=" * 60)
    logger.info("✅ LangGraph workflow initialized")
    logger.info("✅ Job manager ready")
    logger.info("=" * 60)
    yield
    logger.info("👋 FastAPI Gateway shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Vanguard AI Agent Gateway",
    description="REST and WebSocket API for the Vanguard multi-agent factory orchestration system",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Background Task Executor =====


async def execute_workflow_background(job_id: str, event: dict):
    """
    Execute workflow in background.

    Args:
        job_id: Job identifier
        event: Factory event data
    """
    try:
        logger.info(f"[{job_id}] Starting workflow execution...")

        # Update status to running
        await job_manager.update_job_status(job_id, WorkflowStatus.RUNNING)

        # Execute workflow (runs synchronously in executor)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, workflow.process_event, event)

        # Update job with result
        await job_manager.update_job_status(
            job_id, WorkflowStatus.COMPLETED, result=result
        )

        logger.info(f"[{job_id}] ✅ Workflow completed successfully")

    except Exception as e:
        logger.error(f"[{job_id}] ❌ Workflow failed: {e}", exc_info=True)
        await job_manager.update_job_status(job_id, WorkflowStatus.FAILED, error=str(e))


# ===== REST Endpoints =====


@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "service": "Vanguard AI Agent Gateway",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """
    Health check endpoint.

    Returns system health status and component statuses.
    """
    # Check workflow
    workflow_status = "healthy" if workflow.graph else "unhealthy"

    # Check job manager
    job_manager_status = "healthy"

    # Overall status
    overall_status = (
        "healthy"
        if all([workflow_status == "healthy", job_manager_status == "healthy"])
        else "degraded"
    )

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        components={
            "workflow": workflow_status,
            "job_manager": job_manager_status,
            "mcp_client": "healthy",  # Assume healthy for now
        },
    )


@app.post("/workflows/trigger", response_model=WorkflowResponse, tags=["Workflows"])
async def trigger_workflow(
    request: WorkflowTriggerRequest, background_tasks: BackgroundTasks
):
    """
    Trigger a new workflow execution.

    This creates a background job that processes the event through
    the LangGraph agent workflow.

    Returns immediately with a job ID for status tracking.
    """
    # Create event dict
    event = {
        "event_id": f"evt-{asyncio.current_task().get_name()}-{datetime.utcnow().timestamp()}",
        "event_type": request.event_type.value,
        "machine_id": request.machine_id,
        "severity": request.severity.value,
        "description": request.description,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": request.metadata,
    }

    # Create job
    job_id = await job_manager.create_job(event)

    # Schedule background execution
    background_tasks.add_task(execute_workflow_background, job_id, event)

    logger.info(f"Triggered workflow: {job_id} for event {event['event_id']}")

    return WorkflowResponse(
        job_id=job_id,
        status=WorkflowStatus.PENDING,
        event_id=event["event_id"],
        created_at=datetime.utcnow(),
        message="Workflow queued for execution",
    )


@app.get("/workflows/{job_id}", response_model=WorkflowResult, tags=["Workflows"])
async def get_workflow_status(job_id: str):
    """
    Get the status and result of a workflow job.

    Args:
        job_id: Job identifier returned from /workflows/trigger

    Returns:
        Workflow result including status, decisions, and actions
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return job.to_result()


@app.get("/workflows", response_model=List[WorkflowResult], tags=["Workflows"])
async def list_workflows(
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
):
    """
    List recent workflows.

    Args:
        status: Optional status filter
        limit: Maximum number of workflows to return

    Returns:
        List of workflow results
    """
    jobs = await job_manager.list_jobs(status=status, limit=limit)
    return [job.to_result() for job in jobs]


@app.get("/stats", response_model=StatsResponse, tags=["General"])
async def get_stats():
    """
    Get system statistics.

    Returns counts of workflows by status and performance metrics.
    """
    stats = await job_manager.get_stats()

    # Calculate average duration
    completed_jobs = await job_manager.list_jobs(status=WorkflowStatus.COMPLETED)
    durations = [
        (job.completed_at - job.created_at).total_seconds()
        for job in completed_jobs
        if job.completed_at
    ]
    avg_duration = sum(durations) / len(durations) if durations else None

    return StatsResponse(
        total_workflows=stats.get("total", 0),
        pending_workflows=stats.get("pending", 0),
        running_workflows=stats.get("running", 0),
        completed_workflows=stats.get("completed", 0),
        failed_workflows=stats.get("failed", 0),
        average_duration_seconds=avg_duration,
    )


# ===== WebSocket Endpoint =====


@app.websocket("/ws/workflows/{job_id}")
async def websocket_workflow_stream(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for streaming workflow execution.

    Connects to a running workflow and streams updates as each
    graph node completes.

    Args:
        job_id: Job identifier to stream
    """
    await websocket.accept()

    try:
        logger.info(f"WebSocket connected for job: {job_id}")

        job = await job_manager.get_job(job_id)
        if not job:
            await websocket.send_json({"error": f"Job not found: {job_id}"})
            await websocket.close()
            return

        # Send initial status
        await websocket.send_json(
            {
                "type": "status",
                "job_id": job_id,
                "status": job.status.value,
                "message": "Connected to workflow stream",
            }
        )

        # Stream workflow execution
        # Note: This is a simplified version. Full implementation would
        # use workflow.stream_event() and publish updates in real-time

        # For now, wait for completion and send final result
        while job.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
            await asyncio.sleep(0.5)
            job = await job_manager.get_job(job_id)

            if not job:
                break

        # Send final result
        if job:
            result = job.to_result()
            await websocket.send_json(
                {
                    "type": "complete",
                    "job_id": job_id,
                    "status": result.status.value,
                    "result": result.dict(),
                }
            )

        logger.info(f"WebSocket stream completed for job: {job_id}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@app.websocket("/ws/workflows/stream")
async def websocket_workflow_stream_live(websocket: WebSocket):
    """
    WebSocket endpoint for real-time workflow streaming.

    Client sends event data, and receives streaming updates
    as each node in the graph executes.

    Usage:
        1. Connect to ws://localhost:8000/ws/workflows/stream
        2. Send JSON event data
        3. Receive streaming updates as workflow executes
    """
    await websocket.accept()

    try:
        logger.info("WebSocket connected for live streaming")

        # Wait for event data from client
        data = await websocket.receive_json()

        # Validate and create event
        try:
            request = WorkflowTriggerRequest(**data)
        except Exception as e:
            await websocket.send_json(
                {"type": "error", "message": f"Invalid request: {e}"}
            )
            await websocket.close()
            return

        # Create event
        event = {
            "event_id": f"evt-ws-{datetime.utcnow().timestamp()}",
            "event_type": request.event_type.value,
            "machine_id": request.machine_id,
            "severity": request.severity.value,
            "description": request.description,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": request.metadata,
        }

        # Create job
        job_id = await job_manager.create_job(event)

        # Send job created notification
        await websocket.send_json(
            {
                "type": "started",
                "job_id": job_id,
                "event_id": event["event_id"],
                "message": "Workflow execution started",
            }
        )

        # Update status to running
        await job_manager.update_job_status(job_id, WorkflowStatus.RUNNING)

        try:
            # Stream workflow execution
            for node_name, state_update in workflow.stream_event(event):
                # Send update to client
                update = WorkflowStreamUpdate(
                    job_id=job_id,
                    node_name=node_name,
                    timestamp=datetime.utcnow(),
                    state_updates=state_update,
                )

                await websocket.send_json({"type": "update", "data": update.dict()})

                logger.info(f"[{job_id}] Streamed update from node: {node_name}")

            # Get final state
            job = await job_manager.get_job(job_id)
            if job and job.result:
                await job_manager.update_job_status(
                    job_id, WorkflowStatus.COMPLETED, result=job.result
                )

                # Send completion
                await websocket.send_json(
                    {
                        "type": "completed",
                        "job_id": job_id,
                        "result": job.to_result().dict(),
                    }
                )

        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            await job_manager.update_job_status(
                job_id, WorkflowStatus.FAILED, error=str(e)
            )
            await websocket.send_json(
                {"type": "error", "job_id": job_id, "message": str(e)}
            )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
