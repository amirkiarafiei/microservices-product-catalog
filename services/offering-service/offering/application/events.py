from common.schemas import Event


class OfferingCreated(Event):
    event_type: str = "OfferingCreated"


class OfferingUpdated(Event):
    event_type: str = "OfferingUpdated"


class OfferingPublicationInitiated(Event):
    event_type: str = "OfferingPublicationInitiated"


class OfferingPublished(Event):
    event_type: str = "OfferingPublished"


class OfferingPublicationFailed(Event):
    event_type: str = "OfferingPublicationFailed"


class OfferingRetired(Event):
    event_type: str = "OfferingRetired"
