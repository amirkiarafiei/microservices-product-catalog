import os
import sys

# Add src to path so we can import models
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from identity.models import Base  # noqa
from common.database.migrations import run_migrations

# This is the metadata object for 'autogenerate' support
target_metadata = Base.metadata

if __name__ == "__main__":
    # This part is just a fallback, alembic usually calls the functions directly
    pass

# Run the migrations using the shared common-python helper
run_migrations(target_metadata)
