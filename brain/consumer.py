"""
Kafka consumer that feeds events to the LangGraph workflow.
"""

import json
import logging
import os
import signal
import sys

from agents.workflow_langgraph import LangGraphWorkflow
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from metrics.agent_metrics import (
    active_agents,
    event_processing_duration,
    events_processed_total,
)
from prometheus_client import start_http_server

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# check which workflow to use
USE_LANGGRAPH = os.getenv("USE_LANGGRAPH", "true").lower() == "true"

if USE_LANGGRAPH:
    from agents.workflow_langgraph import LangGraphWorkflow
    logger.info("🎯 Using LangGraph-based workflow")
else:
    from agents.workflow import AgentWorkflow
    logger.info("⚠️  Using legacy manual routing workflow")


class AgentKafkaConsumer:
    """
    Kafka consumer for the AI agent system (now with LangGraph).
    """

    def __init__(
        self, bootstrap_servers: str = "localhost:9092", topic: str = "factory_events"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = None

        # choose workflow based on env var
        if USE_LANGGRAPH:
            self.workflow = LangGraphWorkflow()
        else:
            self.workflow = AgentWorkflow()

        self.running = False

        # set active agents gauge
        active_agents.set(1)

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}. Shutting down...")
        self.running = False
        active_agents.set(0)

    def start(self):
        logger.info("=" * 60)
        if USE_LANGGRAPH:
            logger.info("VANGUARD AI AGENT SYSTEM STARTING (LangGraph)")
        else:
            logger.info("VANGUARD AI AGENT SYSTEM STARTING (Legacy)")
        logger.info("=" * 60)
        logger.info(f"Kafka Broker: {self.bootstrap_servers}")
        logger.info(f"Topic: {self.topic}")
        logger.info(f"Metrics available at: http://0.0.0.0:8000/metrics")
        logger.info("")

        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id="ai-agent-group",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )

            logger.info("Connected to Kafka")
            logger.info("Listening for factory events...")

            self.running = True

            for message in self.consumer:
                if not self.running:
                    break

                try:
                    event = message.value

                    # Track event in metrics
                    event_type = event.get("event_type", "UNKNOWN")
                    severity = event.get("severity", "UNKNOWN")

                    # Increment event counter
                    events_processed_total.labels(
                        event_type=event_type, severity=severity
                    ).inc()

                    # Process with LangGraph workflow
                    import time

                    start_time = time.time()

                    state = self.workflow.process_event(event)

                    # Record processing duration
                    duration = time.time() - start_time
                    event_processing_duration.labels(event_type=event_type).observe(
                        duration
                    )

                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)

        except KafkaError as e:
            logger.error(f"Kafka error: {e}")

        finally:
            self._shutdown()

    def _shutdown(self):
        logger.info("Shutting down agent consumer...")

        active_agents.set(0)

        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")

        logger.info("Agent system stopped")


def main():
    """Entry point."""
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "factory_events")

    # start metrics HTTP server
    start_http_server(8000)
    logger.info("Vanguard Metrics server started on port 8000")

    consumer = AgentKafkaConsumer(bootstrap_servers=bootstrap_servers, topic=topic)
    consumer.start()


if __name__ == "__main__":
    main()
