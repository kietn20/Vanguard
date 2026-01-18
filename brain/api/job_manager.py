"""
Job manager for tracking workflow executions.

This manages the lifecycle of workflow jobs:
- Creating jobs
- Tracking status
- Storing results
- Cleanup
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from collections import defaultdict

from api.models import WorkflowStatus, WorkflowResult, EventType, Severity
from agents.state import AgentState

logger = logging.getLogger(__name__)


class Job:
    """Represents a single workflow job."""

    def __init__(self, job_id: str, event: Dict):
        self.job_id = job_id
        self.event = event
        self.status = WorkflowStatus.PENDING
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.result: Optional[AgentState] = None
        self.error: Optional[str] = None
        self.task: Optional[asyncio.Task] = None

    def to_result(self) -> WorkflowResult:
        """Convert job to WorkflowResult."""
        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.created_at).total_seconds()

        if self.result:
            return WorkflowResult(
                job_id=self.job_id,
                status=self.status,
                event_id=self.result.get("event_id", ""),
                event_type=EventType(self.result.get("event_type", "")),
                machine_id=self.result.get("machine_id", ""),
                severity=Severity(self.result.get("severity", "MEDIUM")),
                analysis=self.result.get("analysis"),
                final_decision=self.result.get("final_decision"),
                recommended_actions=self.result.get("recommended_actions", []),
                actions_taken=self.result.get("actions_taken", []),
                parts_available=self.result.get("parts_available", {}),
                should_escalate=self.result.get("should_escalate", False),
                human_approval_needed=self.result.get("human_approval_needed", False),
                created_at=self.created_at,
                completed_at=self.completed_at,
                duration_seconds=duration,
                error_message=self.error,
            )
        else:
            # Job not completed yet
            return WorkflowResult(
                job_id=self.job_id,
                status=self.status,
                event_id=self.event.get("event_id", ""),
                event_type=EventType(self.event.get("event_type", "")),
                machine_id=self.event.get("machine_id", ""),
                severity=Severity(self.event.get("severity", "MEDIUM")),
                created_at=self.created_at,
                error_message=self.error,
            )


class JobManager:
    """
    Manages workflow job lifecycle.

    This is a simple in-memory implementation.
    In production, you'd use Redis or a database.
    """

    def __init__(self, max_jobs: int = 1000):
        """
        Initialize job manager.

        Args:
            max_jobs: Maximum number of jobs to keep in memory
        """
        self.jobs: Dict[str, Job] = {}
        self.max_jobs = max_jobs
        self._lock = asyncio.Lock()

        # Stats
        self.stats = defaultdict(int)

        logger.info(f"JobManager initialized (max_jobs={max_jobs})")

    async def create_job(self, event: Dict) -> str:
        """
        Create a new job.

        Args:
            event: Factory event data

        Returns:
            Job ID
        """
        async with self._lock:
            job_id = f"job-{uuid.uuid4().hex[:12]}"

            job = Job(job_id, event)
            self.jobs[job_id] = job

            self.stats["total"] += 1
            self.stats["pending"] += 1

            # Cleanup old jobs if we exceed max
            await self._cleanup_old_jobs()

            logger.info(f"Created job: {job_id}")
            return job_id

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    async def update_job_status(
        self,
        job_id: str,
        status: WorkflowStatus,
        result: Optional[AgentState] = None,
        error: Optional[str] = None,
    ):
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status
            result: Workflow result (if completed)
            error: Error message (if failed)
        """
        async with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return

            old_status = job.status
            job.status = status

            if status == WorkflowStatus.COMPLETED:
                job.result = result
                job.completed_at = datetime.utcnow()
                self.stats["completed"] += 1
                self.stats["pending"] -= (
                    1 if old_status == WorkflowStatus.PENDING else 0
                )
                self.stats["running"] -= (
                    1 if old_status == WorkflowStatus.RUNNING else 0
                )

            elif status == WorkflowStatus.FAILED:
                job.error = error
                job.completed_at = datetime.utcnow()
                self.stats["failed"] += 1
                self.stats["pending"] -= (
                    1 if old_status == WorkflowStatus.PENDING else 0
                )
                self.stats["running"] -= (
                    1 if old_status == WorkflowStatus.RUNNING else 0
                )

            elif status == WorkflowStatus.RUNNING:
                self.stats["running"] += 1
                self.stats["pending"] -= (
                    1 if old_status == WorkflowStatus.PENDING else 0
                )

            logger.info(f"Job {job_id}: {old_status.value} → {status.value}")

    async def list_jobs(
        self, status: Optional[WorkflowStatus] = None, limit: int = 100
    ) -> List[Job]:
        """
        List jobs.

        Args:
            status: Filter by status
            limit: Maximum number of jobs to return

        Returns:
            List of jobs
        """
        jobs = list(self.jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by created_at (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return jobs[:limit]

    async def get_stats(self) -> Dict[str, int]:
        """Get job statistics."""
        return dict(self.stats)

    async def _cleanup_old_jobs(self):
        """Remove old completed/failed jobs if we exceed max_jobs."""
        if len(self.jobs) <= self.max_jobs:
            return

        # Sort jobs by completion time
        completed_jobs = [
            (job_id, job)
            for job_id, job in self.jobs.items()
            if job.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        ]

        completed_jobs.sort(key=lambda x: x[1].completed_at or datetime.min)

        # Remove oldest completed jobs
        to_remove = len(self.jobs) - self.max_jobs
        for job_id, job in completed_jobs[:to_remove]:
            del self.jobs[job_id]
            logger.debug(f"Cleaned up old job: {job_id}")


# Global job manager instance
job_manager = JobManager()
