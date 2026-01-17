"""Entry point for running the pricing saga worker."""

from .saga_worker import run_pricing_worker

if __name__ == "__main__":
    run_pricing_worker()
