import json
import logging
import signal
import sys
import time
from typing import Optional

from config import Config
from events import EventGenerator
from kafka import KafkaProducer
from kafka.errors import KafkaError


class FactorySimulator:
    """Main simulator class that orchestrates event generation and publishing"""

    def __init__(self, config: Config):
        """
        Initialize the simulator with config

        Args:
            config: configuration object with Kafka and simulator settings
        """
        self.config = config
        self.producer: Optional[KafkaProducer] = None
        self.running = False
        self.event_count = 0

        logging.basicConfig(
            level=config.simulator.log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # register signal handlers for shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals (ctrl + c)

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False

    def _create_producer(self) -> KafkaProducer:
        """
        Create and configure kafka producer

        returns:
            KafkaProducer: configured producers instance

        Raises:
            KafkaError: if connection to kafka fails
        """
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.config.kafka.bootstrap_servers,
                client_id=self.config.kafka.client_id,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),

                # reliability settings
                acks='all',
                retires=3,
                max_in_flight_requests_per_connection=1
            )
            self.logger.info(f"Connected to Kafka at {self.config.kafka.bootstrap_servers}")
            return producer
        except KafkaError as e:
            self.logger.error(f"Failed to connect to Kafka: {e}")
            raise

    def _publish_event(self, event_dict: dict) -> bool:
        """
        Publish a single event to Kafka

        Args:
            event_dict: Event data as dictionary

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # send msg async and get a future
            future = self.producer.send(
                self.config.kafka.topic,
                value=event_dict
            )

            # block until msg is sent or timeout
            record_metadata = future.get(timeout=10)

            self.logger.info(
                f"Published event {event_dict['event_id'][:8]}... "
                f"[{event_dict['event_type']}] to partition {record_metadata.partition}"
            )
            return True

        except KafkaError as e:
            self.logger.error(f"Failed to publish event: {e}")
            return False

    def run(self):
        """
        Main simulation loop
        Generates and publish events at configured intervals
        """
        self.logger.info("Starting Factory Simulator")
        self.logger.info(f"Publishing to topic: {self.config.kafka.topic}")
        self.logger.info(
            f"Event interval: {self.config.simulator.event_interval_seconds} seconds"
        )

        try:
            # initialize kafka producer
            self.producer = self._create_producer()
            self.running = True

            # main event generation loop
            while self.running:
                event = EventGenerator.generate_random_event()

                event_dict = event.model_dumps()

                success = self._publish_event(event_dict)
                if success:
                    self.event_count += 1
                    self.logger.info(
                        f"Event #{self.event_count}: {event.event_type} "
                        f"on {event.machine_id} (Severity: {event.severity})"
                    )

                # wait before generating next event
                time.sleep(self.config.simulator.event_interval_seconds)

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)

        finally:
            self._shutdown()

    def _shutdown(self):
        """Clean up resources before exit"""
        self.logger.info(f"Shutting down. Total events published: {self.event_count}")

        if self.producer:
            self.logger.info("Flushing remaining messages...")
            self.producer.flush()  # ensure all msg are sent
            self.producer.close()
            self.logger.info("Kafka producer closed")

        self.logger.info("Simulator stopped")



def main():
    """entry point for the simulator."""
    print("=" * 60)
    print("VANGUARD FACTORY SIMULATOR")
    print("=" * 60)

    # load configuration
    config = Config.load()

    # create and run simulator
    simulator = FactorySimulator(config)
    simulator.run()

    sys.exit(0)


if __name__ == "__main__":
    main()
