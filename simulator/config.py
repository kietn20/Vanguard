import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class KafkaConfig:
    """Kafka connection configuration"""

    bootstrap_servers: str
    topic: str
    client_id: str = "factory-simulator"

    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """
        create config from env variables

        Returns:
            KafkaConfig: config object with values from .env
        """
        return cls(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            topic=os.getenv("KAFKA_TOPIC", "factory_events"),
            client_id=os.getenv("KAFKA_CLIENT_ID", "factory-simulator"),
        )


@dataclass
class SimulatorConfig:
    """Simulator behavior configuration"""

    event_interval_seconds: int
    log_level: str

    @classmethod
    def from_env(cls) -> "SimulatorConfig":
        """create config from env variables"""
        return cls(
            event_interval_seconds=int(os.getenv("EVENT_INTERVAL_SECONDS", "10")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


@dataclass
class Config:
    """main config container"""

    kafka: KafkaConfig
    simulator: SimulatorConfig

    @classmethod
    def load(cls) -> "Config":
        """
        Load all configuration from environment

        Usage:
            config = Config.load()
            print(config.kafka.bootstrap_servers)
        """
        return cls(kafka=KafkaConfig.from_env(), simulator=SimulatorConfig.from_env())
