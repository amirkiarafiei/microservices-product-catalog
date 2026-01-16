import uuid
from typing import Dict, Any
from common.schemas import Event

class CharacteristicCreated(Event):
    event_type: str = "CharacteristicCreated"

class CharacteristicUpdated(Event):
    event_type: str = "CharacteristicUpdated"

class CharacteristicDeleted(Event):
    event_type: str = "CharacteristicDeleted"
