#!/usr/bin/env python3
"""
Wait for infrastructure services to be healthy before starting microservices.
"""
import sys
import time
from scripts.check_infra import check_all_infrastructure


def wait_for_infrastructure(max_wait_seconds=60, check_interval=2):
    """
    Wait for all infrastructure services to be ready.
    
    Args:
        max_wait_seconds: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
    
    Returns:
        bool: True if all services are ready, False if timeout
    """
    print("⏳ Waiting for infrastructure to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        all_ready, failed_services = check_all_infrastructure()
        
        if all_ready:
            print("✅ All infrastructure services are ready!")
            return True
        
        elapsed = int(time.time() - start_time)
        print(f"⏳ Waiting... ({elapsed}s) - Services not ready: {', '.join(failed_services)}")
        time.sleep(check_interval)
    
    print(f"❌ Timeout after {max_wait_seconds}s. Infrastructure not ready.")
    return False


if __name__ == "__main__":
    if not wait_for_infrastructure():
        sys.exit(1)
