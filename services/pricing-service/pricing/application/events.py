from common.schemas import Event


class PriceCreated(Event):
    event_type: str = "PriceCreated"


class PriceUpdated(Event):
    event_type: str = "PriceUpdated"


class PriceDeleted(Event):
    event_type: str = "PriceDeleted"


class PriceLocked(Event):
    event_type: str = "PriceLocked"


class PriceUnlocked(Event):
    event_type: str = "PriceUnlocked"
