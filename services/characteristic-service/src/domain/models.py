from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


class UnitOfMeasure(str, Enum):
    MBPS = "Mbps"
    GBPS = "Gbps"
    MB = "MB"
    GB = "GB"
    TB = "TB"
    GHZ = "GHz"
    VOLT = "Volt"
    WATT = "Watt"
    METER = "Meter"
    NONE = "None"
    # Adding more common units as per "many many more"
    PERCENT = "%"
    SECONDS = "Seconds"
    MINUTES = "Minutes"
    HOURS = "Hours"
    DAYS = "Days"
    MONTHS = "Months"
    YEARS = "Years"
    UNIT = "Unit"


@dataclass
class Characteristic:
    """
    Characteristic Domain Entity.
    """
    id: uuid.UUID
    name: str
    value: str
    unit_of_measure: UnitOfMeasure
    created_at: datetime
    updated_at: datetime

    def validate(self):
        """
        Business rules validation.
        """
        if not self.name or not (1 <= len(self.name) <= 200):
            raise ValueError("Name must be between 1 and 200 characters")
        if not self.value or not (1 <= len(self.value) <= 100):
            raise ValueError("Value must be between 1 and 100 characters")
        # UnitOfMeasure is already validated by Enum if passed correctly, 
        # but we check if it is part of the Enum.
        if not isinstance(self.unit_of_measure, UnitOfMeasure):
             raise ValueError(f"Invalid UnitOfMeasure: {self.unit_of_measure}")
