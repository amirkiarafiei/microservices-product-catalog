from src.domain.models import UnitOfMeasure
from src.infrastructure.models import CharacteristicORM
from src.infrastructure.repository import CharacteristicRepository


def test_repo_create_and_get(db_session):
    repo = CharacteristicRepository(db_session)
    char_orm = CharacteristicORM(
        name="Latency",
        value="20",
        unit_of_measure=UnitOfMeasure.SECONDS # Assuming SECONDS exists in Enum
    )

    # Create
    created = repo.create(char_orm)
    assert created.id is not None
    assert created.name == "Latency"

    # Get by ID
    retrieved = repo.get_by_id(created.id)
    assert retrieved is not None
    assert retrieved.name == "Latency"
    assert retrieved.value == "20"

def test_repo_get_by_name(db_session):
    repo = CharacteristicRepository(db_session)
    char_orm = CharacteristicORM(
        name="UniqueName",
        value="test",
        unit_of_measure=UnitOfMeasure.NONE
    )
    repo.create(char_orm)

    retrieved = repo.get_by_name("UniqueName")
    assert retrieved is not None
    assert retrieved.name == "UniqueName"

def test_repo_list(db_session):
    repo = CharacteristicRepository(db_session)
    for i in range(5):
        repo.create(CharacteristicORM(
            name=f"Char {i}",
            value=str(i),
            unit_of_measure=UnitOfMeasure.NONE
        ))

    chars = repo.list()
    assert len(chars) == 5

def test_repo_update(db_session):
    repo = CharacteristicRepository(db_session)
    char_orm = CharacteristicORM(name="Original", value="1", unit_of_measure=UnitOfMeasure.NONE)
    repo.create(char_orm)

    char_orm.name = "Updated"
    char_orm.value = "2"
    repo.update(char_orm)

    retrieved = repo.get_by_id(char_orm.id)
    assert retrieved.name == "Updated"
    assert retrieved.value == "2"

def test_repo_delete(db_session):
    repo = CharacteristicRepository(db_session)
    char_orm = CharacteristicORM(name="ToDelete", value="0", unit_of_measure=UnitOfMeasure.NONE)
    repo.create(char_orm)

    repo.delete(char_orm)
    assert repo.get_by_id(char_orm.id) is None
