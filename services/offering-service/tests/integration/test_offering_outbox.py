import uuid
import pytest
from sqlalchemy.orm import Session
from offering.application.schemas import OfferingCreate
from offering.application.service import OfferingService
from offering.infrastructure.models import OutboxORM
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_offering_outbox_flow(db_session: Session):
    service = OfferingService(db_session)
    
    offering_in = OfferingCreate(
        name=f"Integration Test Offering {uuid.uuid4()}",
        specification_ids=[uuid.uuid4()],
        pricing_ids=[uuid.uuid4()],
        sales_channels=["WEB"]
    )

    # Mock external validation
    with patch("offering.application.service.OfferingService._validate_external_ids", new_callable=AsyncMock):
        # 1. Create offering
        created_offering = await service.create_offering(offering_in)
        assert created_offering.id is not None

        # 2. Check outbox
        outbox_entry = (
            db_session.query(OutboxORM)
            .filter(OutboxORM.topic == "product.offering.events")
            .filter(OutboxORM.status == "PENDING")
            .order_by(OutboxORM.created_at.desc())
            .first()
        )

        assert outbox_entry is not None
        assert outbox_entry.payload["payload"]["id"] == str(created_offering.id)
        assert outbox_entry.payload["event_type"] == "OfferingCreated"

