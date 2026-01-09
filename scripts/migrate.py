import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd):
    print(f"Executing: {' '.join(command)} in {cwd}")
    try:
        # Use shell=False for security, pass environment variables explicitly if needed
        # uv run will handle the virtualenv for us
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=False  # Show output in real-time
        )
    except subprocess.CalledProcessError as e:
        print(f"\nError executing command in {cwd}")
        # e.stderr is None if capture_output=False
        sys.exit(1)

def main():
    # Simple help
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Monorepo Migration Tool")
        print("Usage: python scripts/migrate.py [options] <alembic-command>")
        print("\nOptions:")
        print("  --service <name>    Run migration for a specific service only")
        print("\nExamples:")
        print("  python scripts/migrate.py upgrade head")
        print("  python scripts/migrate.py --service identity-service history")
        print("  python scripts/migrate.py revision --autogenerate -m 'description'")
        sys.exit(1)

    # Parse arguments
    args = sys.argv[1:]
    target_service = None
    
    if "--service" in args:
        try:
            idx = args.index("--service")
            target_service = args[idx + 1]
            # Remove --service and its value from args
            args = args[:idx] + args[idx + 2:]
        except (IndexError, ValueError):
            print("Error: --service requires a service name")
            sys.exit(1)

    project_root = Path(__file__).parent.parent
    services_dir = project_root / "services"
    
    # Find all services in the services directory
    if not services_dir.exists():
        print(f"Error: Services directory not found at {services_dir}")
        sys.exit(1)

    # Find services with alembic.ini
    services_with_alembic = []
    for service_path in services_dir.iterdir():
        if service_path.is_dir() and (service_path / "alembic.ini").exists():
            services_with_alembic.append(service_path.name)

    if not services_with_alembic:
        print("No services with alembic.ini found.")
        sys.exit(1)

    if target_service:
        if target_service not in services_with_alembic:
            print(f"Service '{target_service}' not found or doesn't have alembic.ini.")
            print(f"Available services: {', '.join(services_with_alembic)}")
            sys.exit(1)
        services_to_migrate = [target_service]
    else:
        services_to_migrate = sorted(services_with_alembic)

    for service_name in services_to_migrate:
        print(f"\n{'='*60}")
        print(f" Service: {service_name}")
        print(f"{'='*60}")
        
        cwd = services_dir / service_name
        
        # Build command: uv run alembic <args>
        # We use uv run to ensure the service's specific environment is used
        command = ["uv", "run", "alembic"] + args
        run_command(command, cwd)

if __name__ == "__main__":
    main()
