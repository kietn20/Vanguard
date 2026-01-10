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

        # handle shutdown signals
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)



    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        self.running = False



    def start(self):
        """Start consuming events."""
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









                    # todo: store results in database
                    # todo: send notifications if escalation needed









                except Exception as e:
                    logger.error(f"Error processing event: {e}", exc_info=True)

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



def main():
    """Entry point."""
    consumer = AgentKafkaConsumer()
    consumer.start()


if __name__ == "__main__":
    main()
