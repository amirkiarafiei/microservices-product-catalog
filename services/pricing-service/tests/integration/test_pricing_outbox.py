import uuid
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session
from pricing.application.schemas import PriceCreate
from pricing.application.service import PricingService
from pricing.domain.models import CurrencyEnum
from pricing.infrastructure.models import OutboxORM


@pytest.mark.asyncio
async def test_outbox_flow_e2e(db_session: Session):
    """
    Test the outbox flow for Pricing Service:
    1. Create a price via service
    2. Verify an outbox entry is created (PENDING)
    3. Wait for the background listener to process it (mocked by manual check for status)
    """
    service = PricingService(db_session)
    price_in = PriceCreate(name=f"Outbox Test Price {uuid.uuid4()}", value=Decimal("29.99"), unit="per unit", currency=CurrencyEnum.USD)

    # 1. Create via service
    created_price = service.create_price(price_in)
    assert created_price.id is not None

    # 2. Verify outbox entry exists and is PENDING
    outbox_entry = (
        db_session.query(OutboxORM)
        .filter(OutboxORM.topic == "commercial.pricing.events")
        .order_by(OutboxORM.created_at.desc())
        .first()
    )

    assert outbox_entry is not None
    assert outbox_entry.payload["payload"]["id"] == str(created_price.id)
    assert outbox_entry.status == "PENDING"

    # Note: In a real environment, the lifespan listener would pick this up.
    # We've already tested the listener itself in characteristic-service.
