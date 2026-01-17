"""Entry point for running the saga worker."""

from .saga_worker import run_offering_worker

if __name__ == "__main__":
    run_offering_worker()
