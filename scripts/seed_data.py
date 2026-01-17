#!/usr/bin/env python
"""
Initialize the application with sample entities.

This script creates sample data via API calls:
1. Login with default admin credentials
2. Create sample characteristics
3. Create sample specifications using those characteristics
4. Create sample prices
5. Create sample offerings with specs and prices
6. Publish offerings to make them visible in the store
"""

import time
from typing import Dict, List

import httpx


class DataSeeder:
    """Initialize application with sample data via API."""

    def __init__(
        self, base_url: str = "http://localhost:8000", admin_user: str = "admin", admin_pass: str = "admin"
    ):
        self.base_url = base_url
        self.admin_user = admin_user
        self.admin_pass = admin_pass
        self.token = None
        self.client = httpx.Client(base_url=base_url, timeout=10.0)

    def login(self) -> bool:
        """Login and get JWT token."""
        print("🔐 Logging in...")
        try:
            # Use form data instead of JSON for OAuth2PasswordRequestForm
            resp = self.client.post(
                "/api/v1/auth/login",
                data={"username": self.admin_user, "password": self.admin_pass},
            )
            if resp.status_code != 200:
                print(f"❌ Login failed: {resp.status_code} - {resp.text}")
                return False

            data = resp.json()
            self.token = data.get("access_token")
            print(f"✅ Logged in as {self.admin_user}")
            return True
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def _headers(self) -> Dict[str, str]:
        """Get request headers with auth token."""
        return {"Authorization": f"Bearer {self.token}"}

    def create_characteristics(self) -> List[str]:
        """Create sample characteristics."""
        print("\n📝 Creating sample characteristics...")

        characteristics_data = [
            {
                "name": "Speed",
                "value": "100",
                "unit_of_measure": "Mbps",
            },
            {
                "name": "Storage",
                "value": "500",
                "unit_of_measure": "GB",
            },
            {
                "name": "Reliability",
                "value": "99.9",
                "unit_of_measure": "Percent",
            },
            {
                "name": "Latency",
                "value": "10",
                "unit_of_measure": "ms",
            },
            {
                "name": "Bandwidth",
                "value": "1000",
                "unit_of_measure": "Mbps",
            },
        ]

        char_ids = []
        for char_data in characteristics_data:
            try:
                resp = self.client.post(
                    "/api/v1/characteristics",
                    json=char_data,
                    headers=self._headers(),
                )
                if resp.status_code in [200, 201]:
                    char_id = resp.json()["id"]
                    char_ids.append(char_id)
                    print(f"  ✅ Created characteristic: {char_data['name']} ({char_id})")
                else:
                    print(f"  ❌ Failed to create {char_data['name']}: {resp.status_code}")
            except Exception as e:
                print(f"  ❌ Error creating characteristic: {e}")

        return char_ids

    def create_specifications(self, char_ids: List[str]) -> List[str]:
        """Create sample specifications using characteristics."""
        print("\n📋 Creating sample specifications...")

        specifications_data = [
            {
                "name": "Basic Internet Plan",
                "characteristic_ids": [char_ids[0]] if len(char_ids) > 0 else [],
            },
            {
                "name": "Premium Internet Plan",
                "characteristic_ids": [char_ids[0], char_ids[1]] if len(char_ids) > 1 else [char_ids[0]],
            },
            {
                "name": "Enterprise Plan",
                "characteristic_ids": char_ids[:3] if len(char_ids) >= 3 else char_ids,
            },
        ]

        spec_ids = []
        for spec_data in specifications_data:
            try:
                resp = self.client.post(
                    "/api/v1/specifications",
                    json=spec_data,
                    headers=self._headers(),
                )
                if resp.status_code in [200, 201]:
                    spec_id = resp.json()["id"]
                    spec_ids.append(spec_id)
                    print(f"  ✅ Created specification: {spec_data['name']} ({spec_id})")
                else:
                    print(f"  ❌ Failed to create {spec_data['name']}: {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"  ❌ Error creating specification: {e}")

        return spec_ids

    def create_prices(self) -> List[str]:
        """Create sample prices."""
        print("\n💰 Creating sample prices...")

        prices_data = [
            {
                "name": "$29.99/month",
                "value": 29.99,
                "unit": "per month",
                "currency": "USD",
            },
            {
                "name": "$49.99/month",
                "value": 49.99,
                "unit": "per month",
                "currency": "USD",
            },
            {
                "name": "$99.99/month",
                "value": 99.99,
                "unit": "per month",
                "currency": "USD",
            },
            {
                "name": "$199.99/month",
                "value": 199.99,
                "unit": "per month",
                "currency": "USD",
            },
        ]

        price_ids = []
        for price_data in prices_data:
            try:
                resp = self.client.post(
                    "/api/v1/prices",
                    json=price_data,
                    headers=self._headers(),
                )
                if resp.status_code in [200, 201]:
                    price_id = resp.json()["id"]
                    price_ids.append(price_id)
                    print(f"  ✅ Created price: {price_data['name']} ({price_id})")
                else:
                    print(f"  ❌ Failed to create {price_data['name']}: {resp.status_code}")
            except Exception as e:
                print(f"  ❌ Error creating price: {e}")

        return price_ids

    def create_offerings(self, spec_ids: List[str], price_ids: List[str]) -> List[str]:
        """Create sample offerings."""
        print("\n🎁 Creating sample offerings...")

        offerings_data = [
            {
                "name": "Basic Fiber Internet",
                "description": "High-speed fiber internet for home users with basic needs.",
                "specification_ids": [spec_ids[0]] if len(spec_ids) > 0 else [],
                "pricing_ids": [price_ids[0]] if len(price_ids) > 0 else [],
                "sales_channels": ["WEB", "PHONE"],
            },
            {
                "name": "Premium Fiber Internet",
                "description": "Premium fiber internet service with enhanced features and support.",
                "specification_ids": [spec_ids[1]] if len(spec_ids) > 1 else spec_ids,
                "pricing_ids": [price_ids[1]] if len(price_ids) > 1 else price_ids,
                "sales_channels": ["WEB", "PHONE", "PARTNER"],
            },
            {
                "name": "Enterprise Connectivity",
                "description": "Dedicated enterprise-grade connectivity solution for large organizations.",
                "specification_ids": spec_ids[2:3] if len(spec_ids) > 2 else spec_ids,
                "pricing_ids": [price_ids[3]] if len(price_ids) > 3 else price_ids,
                "sales_channels": ["WEB", "SALES_TEAM"],
            },
        ]

        offering_ids = []
        for offering_data in offerings_data:
            try:
                resp = self.client.post(
                    "/api/v1/offerings",
                    json=offering_data,
                    headers=self._headers(),
                )
                if resp.status_code in [200, 201]:
                    offering_id = resp.json()["id"]
                    offering_ids.append(offering_id)
                    print(f"  ✅ Created offering (DRAFT): {offering_data['name']} ({offering_id})")
                else:
                    print(f"  ❌ Failed to create {offering_data['name']}: {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"  ❌ Error creating offering: {e}")

        return offering_ids

    def publish_offerings(self, offering_ids: List[str]) -> None:
        """Publish offerings and wait for completion."""
        print("\n🚀 Publishing offerings...")

        for offering_id in offering_ids:
            try:
                # Initiate publish
                resp = self.client.post(
                    f"/api/v1/offerings/{offering_id}/publish",
                    headers=self._headers(),
                )
                if resp.status_code in [200, 202]:
                    print(f"  📤 Publishing initiated for {offering_id}...")

                    # Poll for publication completion
                    max_attempts = 30
                    for attempt in range(max_attempts):
                        time.sleep(0.5)
                        status_resp = self.client.get(
                            f"/api/v1/offerings/{offering_id}",
                            headers=self._headers(),
                        )
                        if status_resp.status_code == 200:
                            status = status_resp.json().get("lifecycle_status")
                            if status == "PUBLISHED":
                                print(f"  ✅ Published: {offering_id}")
                                break
                            elif status == "DRAFT":
                                print(f"  ❌ Publication failed, reverted to DRAFT: {offering_id}")
                                break
                        if attempt == max_attempts - 1:
                            print(f"  ⏱️  Publication timeout for {offering_id} (may still complete)")
                else:
                    print(f"  ❌ Failed to publish {offering_id}: {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"  ❌ Error publishing offering: {e}")

    def run(self) -> bool:
        """Run the complete seeding process."""
        print("=" * 60)
        print("APPLICATION DATA SEEDING")
        print("=" * 60)

        if not self.login():
            return False

        try:
            char_ids = self.create_characteristics()
            if not char_ids:
                print("⚠️  No characteristics created, continuing anyway...")

            spec_ids = self.create_specifications(char_ids)
            if not spec_ids:
                print("⚠️  No specifications created, continuing anyway...")

            price_ids = self.create_prices()
            if not price_ids:
                print("⚠️  No prices created, stopping...")
                return False

            offering_ids = self.create_offerings(spec_ids, price_ids)
            if not offering_ids:
                print("⚠️  No offerings created, stopping...")
                return False

            self.publish_offerings(offering_ids)

            print("\n" + "=" * 60)
            print("✅ Sample data created successfully!")
            print("=" * 60)
            print("\nYou can now:")
            print("1. Visit http://localhost:3000 to see the store")
            print("2. Login at http://localhost:3000/login with admin/admin")
            print("3. View offerings in the Store page")
            print("4. Create more entities via the Builder tab")

            return True
        except Exception as e:
            print(f"\n❌ Seeding failed: {e}")
            return False
        finally:
            self.client.close()


if __name__ == "__main__":
    seeder = DataSeeder()
    success = seeder.run()
    exit(0 if success else 1)
