import argparse
from pathlib import Path

import httpx


def deploy_bpmn(camunda_engine_rest_url: str, bpmn_path: str, deployment_name: str = "e2e-deployment") -> dict:
    """
    Deploy a BPMN file to Camunda via Engine REST API.
    """
    url = camunda_engine_rest_url.rstrip("/") + "/deployment/create"
    bpmn_file = Path(bpmn_path)
    if not bpmn_file.exists():
        raise FileNotFoundError(bpmn_path)

    files = {
        "data": (bpmn_file.name, bpmn_file.read_bytes(), "text/xml"),
    }
    data = {
        "deployment-name": deployment_name,
        "deploy-changed-only": "true",
        "enable-duplicate-filtering": "true",
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, data=data, files=files)
        resp.raise_for_status()
        return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Deploy BPMN to Camunda Engine REST.")
    parser.add_argument("--camunda-url", required=True, help="Camunda engine-rest base URL, e.g. http://localhost:8080/engine-rest")
    parser.add_argument("--bpmn", required=True, help="Path to BPMN file")
    parser.add_argument("--name", default="offering-publication-saga", help="Deployment name")
    args = parser.parse_args()

    result = deploy_bpmn(args.camunda_url, args.bpmn, deployment_name=args.name)
    print(result)


if __name__ == "__main__":
    main()

