import uuid

import pytest
from offering.domain.models import LifecycleStatus, ProductOffering


def test_product_offering_default_state():
    offering = ProductOffering(name="Test Offering")
    assert offering.lifecycle_status == LifecycleStatus.DRAFT
    assert not offering.can_publish()


def test_can_publish_requirements():
    offering = ProductOffering(name="Test Offering")

    # Needs spec
    offering.specification_ids = [uuid.uuid4()]
    assert not offering.can_publish()

    # Needs price
    offering.pricing_ids = [uuid.uuid4()]
    assert not offering.can_publish()

    # Needs channel
    offering.sales_channels = ["WEB"]
    assert offering.can_publish()


def test_publish_transition_success():
    offering = ProductOffering(
        name="Test Offering",
        specification_ids=[uuid.uuid4()],
        pricing_ids=[uuid.uuid4()],
        sales_channels=["WEB"]
    )

    offering.publish()
    assert offering.lifecycle_status == LifecycleStatus.PUBLISHING


def test_publish_transition_fails_if_requirements_missing():
    offering = ProductOffering(name="Test Offering")
    with pytest.raises(ValueError, match="Offering must have at least one specification"):
        offering.publish()


def test_confirm_publication():
    offering = ProductOffering(name="Test Offering")
    offering.lifecycle_status = LifecycleStatus.PUBLISHING

    offering.confirm_publication()
    assert offering.lifecycle_status == LifecycleStatus.PUBLISHED
    assert offering.published_at is not None


def test_fail_publication():
    offering = ProductOffering(name="Test Offering")
    offering.lifecycle_status = LifecycleStatus.PUBLISHING

    offering.fail_publication()
    assert offering.lifecycle_status == LifecycleStatus.DRAFT


def test_retire_offering():
    offering = ProductOffering(name="Test Offering")
    offering.lifecycle_status = LifecycleStatus.PUBLISHED

    offering.retire()
    assert offering.lifecycle_status == LifecycleStatus.RETIRED
    assert offering.retired_at is not None


def test_invalid_transitions():
    offering = ProductOffering(name="Test Offering")

    # Cannot confirm if not publishing
    with pytest.raises(ValueError):
        offering.confirm_publication()

    # Cannot retire if not published
    with pytest.raises(ValueError):
        offering.retire()
