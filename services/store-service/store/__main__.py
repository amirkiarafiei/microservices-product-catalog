"""Entry point for running the store saga worker."""

from .saga_worker import run_store_worker

if __name__ == "__main__":
    run_store_worker()
