"""
Pydantic models for FastAPI requests and responses.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Factory event types."""

    SENSOR_OVERHEAT = "SENSOR_OVERHEAT"
    PART_FAILED_QC = "PART_FAILED_QC"
    MACHINE_VIBRATION = "MACHINE_VIBRATION"
    LOW_INVENTORY = "LOW_INVENTORY"
    MAINTENANCE_DUE = "MAINTENANCE_DUE"


class Severity(str, Enum):
    """Event severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WorkflowTriggerRequest(BaseModel):
    """Request to trigger a workflow."""

    event_type: EventType = Field(..., description="Type of factory event")
    machine_id: str = Field(..., description="Machine identifier", min_length=1)
    severity: Severity = Field(default=Severity.MEDIUM, description="Event severity")
    description: str = Field(..., description="Event description", min_length=1)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional event data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "SENSOR_OVERHEAT",
                "machine_id": "PRESS-001",
                "severity": "CRITICAL",
                "description": "Temperature sensor reading 120°C exceeds threshold",
                "metadata": {
                    "temperature_celsius": 120,
                    "threshold_celsius": 80,
                    "sensor_id": "TEMP-05",
                },
            }
        }


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowResponse(BaseModel):
    """Response after triggering a workflow."""

    job_id: str = Field(..., description="Unique job identifier")
    status: WorkflowStatus = Field(..., description="Current workflow status")
    event_id: str = Field(..., description="Factory event ID")
    created_at: datetime = Field(..., description="Workflow creation time")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job-abc123",
                "status": "pending",
                "event_id": "evt-xyz789",
                "created_at": "2026-01-17T10:00:00Z",
                "message": "Workflow queued for execution",
            }
        }


class WorkflowResult(BaseModel):
    """Final workflow execution result."""

    job_id: str
    status: WorkflowStatus
    event_id: str
    event_type: EventType
    machine_id: str
    severity: Severity

    # Workflow outputs
    analysis: Optional[str] = None
    final_decision: Optional[str] = None
    recommended_actions: List[str] = Field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    parts_available: Dict[str, bool] = Field(default_factory=dict)

    # Flags
    should_escalate: bool = False
    human_approval_needed: bool = False

    # Timing
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Error info (if failed)
    error_message: Optional[str] = None


class WorkflowStreamUpdate(BaseModel):
    """Streaming update during workflow execution."""

    job_id: str
    node_name: str = Field(..., description="Graph node that executed")
    timestamp: datetime
    state_updates: Dict[str, Any] = Field(
        ..., description="State changes from this node"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job-abc123",
                "node_name": "supervisor",
                "timestamp": "2026-01-17T10:00:01Z",
                "state_updates": {
                    "analysis": "Critical overheat detected...",
                    "next_agent": "inventory",
                },
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    components: Dict[str, str] = Field(
        ..., description="Status of individual components"
    )
    version: str = "0.1.0"


class StatsResponse(BaseModel):
    """System statistics."""

    total_workflows: int
    pending_workflows: int
    running_workflows: int
    completed_workflows: int
    failed_workflows: int
    average_duration_seconds: Optional[float] = None
