import random
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Enumeration of possible factory events"""

    SENSOR_OVERHEAT = "SENSOR_OVERHEAT"
    PART_FAILED_QC = "PART_FAILED_QC"
    MACHINE_VIBRATION = "MACHINE_VIBRATION"
    LOW_INVENTORY = "LOW_INVENTORY"
    MAINTENANCE_DUE = "MAINTENANCE_DUE"


class Severity(str, Enum):
    """Event severity levels"""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FactoryEvent(BaseModel):
    """Base model for all factory events"""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    machine_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: Severity
    description: str
    metadata: Optional[dict] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class EventGenerator:
    """
    Generates realistic factory events with appropriate metadata
    """

    # Factory machines (realistic IDs)
    MACHINES = [
        "PRESS-001",
        "PRESS-002",
        "PRESS-003",
        "WELDER-A01",
        "WELDER-A02",
        "CNC-M10",
        "CNC-M11",
        "CNC-M12",
        "ASSEMBLY-LINE-1",
        "ASSEMBLY-LINE-2",
        "QC-STATION-01",
        "QC-STATION-02",
    ]

    # Spare parts inventory
    PARTS = [
        "HYDRAULIC_PUMP",
        "BEARING_6205",
        "SERVO_MOTOR",
        "PRESSURE_SENSOR",
        "WELDING_TIP",
        "CNC_TOOL_BIT",
    ]

    @classmethod
    def generate_random_event(cls) -> FactoryEvent:
        """
        Generate a random but realistic factory event

        Returns:
            FactoryEvent: A randomly generated event with appropraite metadata
        """
        event_type = random.choice(list(EventType))
        machine_id = random.choice(list(cls.MACHINES))

        # Generate event-specific details
        if event_type == EventType.SENSOR_OVERHEAT:
            return cls._generate_overheat_event(machine_id)
        elif event_type == EventType.PART_FAILED_QC:
            return cls._generate_qc_failure_event(machine_id)
        elif event_type == EventType.MACHINE_VIBRATION:
            return cls._generate_vibration_event(machine_id)
        elif event_type == EventType.LOW_INVENTORY:
            return cls._generate_inventory_event()
        else:  # MAINTENANCE_DUE
            return cls._generate_maintenance_event(machine_id)

    @classmethod
    def _generate_overheat_event(cls, machine_id: str) -> FactoryEvent:
        """Generate a sensor overheat event"""
        temp = random.randint(85, 120)  # Celsius
        threshold = 80
        severity = Severity.CRITICAL if temp > 100 else Severity.HIGH

        return FactoryEvent(
            event_type=EventType.SENSOR_OVERHEAT,
            machine_id=machine_id,
            severity=severity,
            description=f"Temperature sensor reading {temp}°C exceeds threshold of {threshold}°C",
            metadata={
                "temperature_celsius": temp,
                "threshold_celsius": threshold,
                "sensor_id": f"TEMP-{random.randint(1, 5):02d}",
            },
        )

    @classmethod
    def _generate_qc_failure_event(cls, machine_id: str) -> FactoryEvent:
        """Generate a quality control failure event"""
        defect_types = [
            "DIMENSIONAL",
            "SURFACE_FINISH",
            "MATERIAL_DEFECT",
            "ASSEMBLY_ERROR",
        ]
        defect = random.choice(defect_types)

        return FactoryEvent(
            event_type=EventType.PART_FAILED_QC,
            machine_id=machine_id,
            severity=Severity.MEDIUM,
            description=f"Part failed QC inspection: {defect}",
            metadata={
                "defect_type": defect,
                "batch_id": f"BATCH-{random.randint(1000, 9999)}",
                "inspector_id": f"QC{random.randint(1, 5)}",
            },
        )

    @classmethod
    def _generate_vibration_event(cls, machine_id: str) -> FactoryEvent:
        """Generate an abnormal vibration event"""
        vibration_level = round(random.uniform(5.0, 15.0), 2)  # mm/s
        normal_range = 3.0

        severity = Severity.CRITICAL if vibration_level > 12 else Severity.HIGH

        return FactoryEvent(
            event_type=EventType.MACHINE_VIBRATION,
            machine_id=machine_id,
            severity=severity,
            description=f"Abnormal vibration detected: {vibration_level} mm/s (normal: <{normal_range})",
            metadata={
                "vibration_mm_per_sec": vibration_level,
                "normal_threshold": normal_range,
                "axis": random.choice(["X", "Y", "Z"]),
            },
        )

    @classmethod
    def _generate_inventory_event(cls) -> FactoryEvent:
        """Generate a low inventory alert"""
        part = random.choice(cls.PARTS)
        current_stock = random.randint(1, 5)
        min_stock = 10

        return FactoryEvent(
            event_type=EventType.LOW_INVENTORY,
            machine_id="INVENTORY-SYSTEM",
            severity=Severity.MEDIUM,
            description=f"Low stock alert: {part} has only {current_stock} units (min: {min_stock})",
            metadata={
                "part_name": part,
                "current_stock": current_stock,
                "minimum_stock": min_stock,
                "recommended_order_quantity": min_stock * 3,
            },
        )

    @classmethod
    def _generate_maintenance_event(cls, machine_id: str) -> FactoryEvent:
        """Generate a maintenance due event"""
        hours_until_due = random.randint(1, 24)

        severity = Severity.HIGH if hours_until_due <= 4 else Severity.MEDIUM

        return FactoryEvent(
            event_type=EventType.MAINTENANCE_DUE,
            machine_id=machine_id,
            severity=severity,
            description=f"Scheduled maintenance due in {hours_until_due} hours",
            metadata={
                "hours_until_due": hours_until_due,
                "maintenance_type": random.choice(
                    ["PREVENTIVE", "INSPECTION", "CALIBRATION"]
                ),
                "estimated_duration_hours": random.randint(1, 4),
            },
        )
