import json
from pathlib import Path

import httpx


def load_openapi_spec(service_name: str) -> dict:
    project_root = Path(__file__).resolve().parents[2]
    spec_path = project_root / f"docs/api/{service_name}-openapi.json"
    with open(spec_path, "r") as f:
        return json.load(f)

def validate_structure(data: dict | list, schema: dict, definitions: dict):
    """
    A very basic structural validation.
    """
    # Simple check: if schema refers to a definition, check if data has keys.
    if isinstance(data, list):
        # Assuming array response
        item_schema = schema.get("items", {})
        if "$ref" in item_schema:
            ref = item_schema["$ref"].split("/")[-1]
            def_schema = definitions.get(ref, {})
            required_props = def_schema.get("required", [])
            properties = def_schema.get("properties", {})

            for item in data:
                for prop in required_props:
                    assert prop in item, f"Missing required property {prop}"
                # Check types for known properties
                for key, val in item.items():
                    if key in properties:
                        prop_type = properties[key].get("type")
                        if prop_type == "string":
                            assert isinstance(val, str) or val is None, f"{key} should be string"
                        elif prop_type == "integer":
                            assert isinstance(val, int) or val is None, f"{key} should be integer"
                        # Add more types as needed

def test_characteristic_contract(e2e_ctx):
    spec = load_openapi_spec("characteristic")
    gw = e2e_ctx.services["gateway"]

    # Login
    r = httpx.post(
        f"{gw}/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    # Create one to ensure list is not empty
    httpx.post(
        f"{gw}/api/v1/characteristics",
        headers=auth,
        json={"name": "ContractTestChar", "value": "10", "unit_of_measure": "Mbps"},
    )

    # Get List
    r = httpx.get(f"{gw}/api/v1/characteristics", headers=auth)
    assert r.status_code == 200
    data = r.json()

    # Validate against spec
    # Path: /api/v1/characteristics GET responses 200 content application/json schema
    path_item = spec["paths"]["/api/v1/characteristics"]["get"]
    resp_schema = path_item["responses"]["200"]["content"]["application/json"]["schema"]
    components = spec.get("components", {}).get("schemas", {})

    validate_structure(data, resp_schema, components)

def test_specification_contract(e2e_ctx):
    spec = load_openapi_spec("specification")
    gw = e2e_ctx.services["gateway"]

    # Login
    r = httpx.post(
        f"{gw}/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    # Create dependency
    r_c = httpx.post(
        f"{gw}/api/v1/characteristics",
        headers=auth,
        json={"name": "SpecContractChar", "value": "10", "unit_of_measure": "Mbps"},
    )
    char_id = r_c.json()["id"]

    # Create Spec to ensure list not empty
    # Retry loop because of eventual consistency (cache sync)
    import time
    for _ in range(10):
        r_s = httpx.post(
            f"{gw}/api/v1/specifications",
            headers=auth,
            json={"name": "ContractSpec", "characteristic_ids": [char_id]},
        )
        if r_s.status_code == 201:
            break
        time.sleep(1)

    r = httpx.get(f"{gw}/api/v1/specifications", headers=auth)
    assert r.status_code == 200
    data = r.json()

    path_item = spec["paths"]["/api/v1/specifications"]["get"]
    resp_schema = path_item["responses"]["200"]["content"]["application/json"]["schema"]
    components = spec.get("components", {}).get("schemas", {})

    validate_structure(data, resp_schema, components)

def test_pricing_contract(e2e_ctx):
    spec = load_openapi_spec("pricing")
    gw = e2e_ctx.services["gateway"]

    r = httpx.post(
        f"{gw}/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    httpx.post(
        f"{gw}/api/v1/prices",
        headers=auth,
        json={"name": "ContractPrice", "value": "10.00", "unit": "month", "currency": "USD"},
    )

    r = httpx.get(f"{gw}/api/v1/prices", headers=auth)
    assert r.status_code == 200
    data = r.json()

    path_item = spec["paths"]["/api/v1/prices"]["get"]
    resp_schema = path_item["responses"]["200"]["content"]["application/json"]["schema"]
    components = spec.get("components", {}).get("schemas", {})

    validate_structure(data, resp_schema, components)

def test_offering_contract(e2e_ctx):
    spec = load_openapi_spec("offering")
    gw = e2e_ctx.services["gateway"]

    r = httpx.post(
        f"{gw}/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    # We won't create an offering here because of complex dependencies,
    # but we assume the system might be empty or have previous test data.
    # If empty, validation passes on empty list.

    r = httpx.get(f"{gw}/api/v1/offerings", headers=auth)
    assert r.status_code == 200
    data = r.json()

    path_item = spec["paths"]["/api/v1/offerings"]["get"]
    resp_schema = path_item["responses"]["200"]["content"]["application/json"]["schema"]
    components = spec.get("components", {}).get("schemas", {})

    validate_structure(data, resp_schema, components)
