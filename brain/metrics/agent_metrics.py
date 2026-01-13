"""
Custom Prometheus metrics for AI agents.

This module exposes metrics about agent decisions and performance.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps

# ===== COUNTERS (monotonically increasing) =====

# Total events processed by the agent system
events_processed_total = Counter(
    "vanguard_events_processed_total",
    "Total number of factory events processed",
    ["event_type", "severity"],
)

# Total decisions made
decisions_made_total = Counter(
    "vanguard_decisions_made_total",
    "Total number of decisions made by agents",
    ["agent", "decision_type"],  # decision_type: approve/escalate/reject
)

# Actions taken by agents
actions_taken_total = Counter(
    "vanguard_actions_taken_total",
    "Total number of actions executed",
    ["action_type", "result"],  # result: success/failed
)

# Guardrail validations
guardrail_validations_total = Counter(
    "vanguard_guardrail_validations_total",
    "Total guardrail validation requests",
    ["action_type", "result"],  # result: approved/rejected/requires_approval
)

# ===== HISTOGRAMS (track distributions) =====

# Event processing duration
event_processing_duration = Histogram(
    "vanguard_event_processing_seconds",
    "Time taken to process an event",
    ["event_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],  # Buckets in seconds
)

# Agent decision latency
agent_decision_latency = Histogram(
    "vanguard_agent_decision_seconds",
    "Time taken for agent to make a decision",
    ["agent"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

# ===== GAUGES (can go up or down) =====

# Current number of parts with low stock
low_stock_parts = Gauge(
    "vanguard_low_stock_parts", "Number of parts currently below minimum quantity"
)

# Parts requiring human approval
parts_awaiting_approval = Gauge(
    "vanguard_parts_awaiting_approval", "Number of actions awaiting human approval"
)

# Active agent workers
active_agents = Gauge("vanguard_active_agents", "Number of active agent instances")

# ===== INFO (metadata about the system) =====

agent_info = Info("vanguard_agent", "Information about the agent system")

# Set agent metadata
agent_info.info({"version": "0.1.0", "system": "vanguard", "component": "ai-agents"})

# ===== DECORATOR FOR AUTOMATIC TIMING =====


def track_processing_time(event_type: str):
    """
    Decorator to automatically track event processing time.

    Usage:
        @track_processing_time('SENSOR_OVERHEAT')
        def process_event(event):
            # your code here
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                event_processing_duration.labels(event_type=event_type).observe(
                    duration
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                event_processing_duration.labels(event_type=event_type).observe(
                    duration
                )
                raise

        return wrapper

    return decorator


def track_decision_time(agent_name: str):
    """
    Decorator to track agent decision latency.

    Usage:
        @track_decision_time('inventory-agent')
        def make_decision(state):
            # decision logic
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            agent_decision_latency.labels(agent=agent_name).observe(duration)
            return result

        return wrapper

    return decorator
