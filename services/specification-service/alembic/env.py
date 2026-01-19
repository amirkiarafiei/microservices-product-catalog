from common.database.migrations import run_migrations
from specification.infrastructure.models import Base

# This is the MetaData object of your models
target_metadata = Base.metadata

if __name__ == "__main__":
    # This block is not strictly necessary for alembic but good for clarity
    pass

# We call the shared run_migrations function
run_migrations(target_metadata)
