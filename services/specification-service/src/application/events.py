import uuid
from typing import Dict, Any
from common.schemas import Event

class SpecificationCreated(Event):
    event_type: str = "SpecificationCreated"

class SpecificationUpdated(Event):
    event_type: str = "SpecificationUpdated"

class SpecificationDeleted(Event):
    event_type: str = "SpecificationDeleted"
