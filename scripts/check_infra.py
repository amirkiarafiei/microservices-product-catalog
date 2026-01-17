import socket
import sys


def check_port(host, port, name):
    print(f"Checking {name} on {host}:{port}...", end=" ")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect((host, port))
        print("\033[92mSUCCESS\033[0m")
        return True
    except (socket.timeout, ConnectionRefusedError):
        print("\033[91mFAILED\033[0m")
        return False
    finally:
        s.close()

def main():
    infra_services = [
        ("localhost", 5432, "PostgreSQL"),
        ("localhost", 5672, "RabbitMQ (AMQP)"),
        ("localhost", 15672, "RabbitMQ (Management)"),
        ("localhost", 27017, "MongoDB"),
        ("localhost", 9200, "Elasticsearch"),
        ("localhost", 8085, "Camunda"),
        ("localhost", 9411, "Zipkin"),
        ("localhost", 5601, "Kibana"),
    ]

    print("--- Infrastructure Health Check ---")
    all_ok = True
    for host, port, name in infra_services:
        if not check_port(host, port, name):
            all_ok = False

    if all_ok:
        print("\n\033[92mAll services are up and reachable!\033[0m")
        sys.exit(0)
    else:
        print("\n\033[91mSome services are not reachable. Please check your docker-compose status.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
