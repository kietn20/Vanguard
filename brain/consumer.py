"""
Kafka consumer that feeds events to the agent workflow.

This consumer:
1. Listens to factory_events topic
2. Deserializes JSON messages
3. Passes events to the agent workflow
4. Logs results
"""

import json
import logging
import signal
import sys
from prometheus_client import start_http_server, Counter
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from agents.workflow import AgentWorkflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AgentKafkaConsumer:
    """
    Kafka consumer for the AI agent system.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092", topic: str = "factory_events"):
        """
        Initialize the consumer.

        Args:
            bootstrap_servers: Kafka broker address
            topic: Topic to consume from
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = None
        self.workflow = AgentWorkflow()
        self.running = False
        
        # Metrics
        self.events_processed = Counter('ai_agent_events_processed_total', 'Total number of events processed by AI agents')
        self.processing_errors = Counter('ai_agent_processing_errors_total', 'Total number of processing errors')

        # handle shutdown signals
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)



    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        self.running = False



    def start(self):
        """Start consuming events."""
        # Start Prometheus metrics server
        logger.info("Starting Prometheus metrics server on port 8000")
        start_http_server(8000)

        logger.info("=" * 60)
        logger.info("VANGUARD AI AGENT SYSTEM STARTING")
        logger.info("=" * 60)
        logger.info(f"Kafka Broker: {self.bootstrap_servers}")
        logger.info(f"Topic: {self.topic}")
        logger.info("")

        try:
            # create Kafka consumer
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

            # main consumption loop
            for message in self.consumer:
                if not self.running:
                    break

                try:
                    event = message.value

                    # process through agent workflow
                    state = self.workflow.process_event(event)
                    self.events_processed.inc()









                    # todo: store results in database
                    # todo: send notifications if escalation needed









                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)
                    self.processing_errors.inc()

        except KafkaError as e:
            logger.error(f"Kafka error: {e}")

        finally:
            self._shutdown()


    def _shutdown(self):
        """Clean shutdown."""
        logger.info("Shutting down agent consumer...")

        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")

        logger.info("Agent system stopped")



import os

def main():
    """Entry point."""
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "factory_events")
    
    consumer = AgentKafkaConsumer(bootstrap_servers=bootstrap_servers, topic=topic)
    consumer.start()


if __name__ == "__main__":
    main()
