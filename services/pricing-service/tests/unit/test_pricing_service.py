import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from common.exceptions import ConflictError, NotFoundError, AppException

from src.application.schemas import PriceCreate, PriceUpdate
from src.application.service import PricingService
from src.domain.models import CurrencyEnum
from src.infrastructure.models import PriceORM


@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.query.return_value.filter.return_value.first.return_value = None
    return session


@pytest.fixture
def service(mock_db_session):
    return PricingService(mock_db_session)


def test_create_price_success(service, mock_db_session):
    price_in = PriceCreate(name="Test Price", value=Decimal("19.99"), unit="per month", currency=CurrencyEnum.USD)

    created_price = service.create_price(price_in)

    assert created_price.name == "Test Price"
    assert created_price.value == Decimal("19.99")
    mock_db_session.add.assert_called()
    mock_db_session.commit.assert_called()


def test_create_price_duplicate_name(service, mock_db_session):
    price_in = PriceCreate(name="Duplicate", value=Decimal("10.00"), unit="once", currency=CurrencyEnum.EUR)
    
    # Mock existing price
    mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock()

    with pytest.raises(ConflictError):
        service.create_price(price_in)


def test_update_locked_price_fails(service, mock_db_session):
    price_id = uuid.uuid4()
    existing_price = PriceORM(id=price_id, name="Locked", value=10, unit="once", currency="USD", locked=True, locked_by_saga_id=uuid.uuid4())
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_price

    price_update = PriceUpdate(name="New Name", value=Decimal("20.00"), unit="once", currency=CurrencyEnum.USD)

    with pytest.raises(AppException) as exc:
        service.update_price(price_id, price_update)
    assert exc.value.code == "LOCKED"


def test_lock_price_success(service, mock_db_session):
    price_id = uuid.uuid4()
    saga_id = uuid.uuid4()
    existing_price = PriceORM(id=price_id, name="To Lock", value=10, unit="once", currency="USD", locked=False)
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_price

    locked_price = service.lock_price(price_id, saga_id)

    assert locked_price.locked is True
    assert locked_price.locked_by_saga_id == saga_id
    mock_db_session.commit.assert_called()


def test_lock_already_locked_price_fails(service, mock_db_session):
    price_id = uuid.uuid4()
    saga_id_1 = uuid.uuid4()
    saga_id_2 = uuid.uuid4()
    existing_price = PriceORM(id=price_id, name="Locked", value=10, unit="once", currency="USD", locked=True, locked_by_saga_id=saga_id_1)
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_price

    with pytest.raises(AppException) as exc:
        service.lock_price(price_id, saga_id_2)
    assert exc.value.code == "LOCKED"
