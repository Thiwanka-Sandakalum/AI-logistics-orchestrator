"""SQLite-backed local data layer for shipment assistant tools."""

from __future__ import annotations

from functools import cache
import secrets
import sqlite3
import string
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import settings
from src.tools.zone_mapper import get_zone_mapper


DEFAULT_RATE_CARDS = [
    ("ground", 8.0, 1.25, 5, "Loomis Ground"),
    ("express", 12.5, 1.75, 2, "Loomis 2Day"),
    ("priority", 14.0, 1.95, 3, "Loomis Priority"),
    ("overnight", 24.0, 2.75, 1, "Loomis Express"),
]

DEFAULT_CUSTOMERS = [
    (
        "CUST-10001",
        "John Doe",
        "john@example.com",
        "5551234567",
        "active",
    ),
    (
        "CUST-10002",
        "Jane Smith",
        "jane@example.com",
        "5559876543",
        "active",
    ),
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteDataStore:
    """Encapsulates all local SQLite operations used by tools."""

    def __init__(self, db_path: str = settings.sqlite_db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()
        self._ensure_shipments_columns()
        self._seed_if_empty()

    def _init_schema(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    account_status TEXT NOT NULL DEFAULT 'active'
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS shipments (
                    tracking_number TEXT PRIMARY KEY,
                    customer_id TEXT,
                    sender_name TEXT NOT NULL,
                    sender_address TEXT NOT NULL,
                    sender_city TEXT NOT NULL,
                    sender_state TEXT NOT NULL,
                    sender_zip TEXT NOT NULL,
                    sender_phone TEXT,
                    recipient_name TEXT NOT NULL,
                    recipient_address TEXT NOT NULL,
                    recipient_city TEXT NOT NULL,
                    recipient_state TEXT NOT NULL,
                    recipient_zip TEXT NOT NULL,
                    recipient_phone TEXT,
                    weight_lbs REAL NOT NULL,
                    service_type TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    current_location TEXT NOT NULL,
                    estimated_delivery TEXT,
                    last_update TEXT NOT NULL,
                    carrier TEXT,
                    total_cost REAL NOT NULL,
                    confirmation_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS complaints (
                    ticket_id TEXT PRIMARY KEY,
                    tracking_number TEXT NOT NULL,
                    issue_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    contact_email TEXT NOT NULL,
                    contact_phone TEXT,
                    status TEXT NOT NULL,
                    next_steps TEXT NOT NULL,
                    estimated_resolution TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (tracking_number) REFERENCES shipments(tracking_number)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_cards (
                    service_type TEXT PRIMARY KEY,
                    base_cost REAL NOT NULL,
                    per_lb REAL NOT NULL,
                    estimated_delivery_days INTEGER NOT NULL,
                    carrier TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_shipments_customer_id
                ON shipments(customer_id)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_shipments_created_at
                ON shipments(created_at)
                """
            )
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_shipments_confirmation_id
                ON shipments(confirmation_id)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_customers_email
                ON customers(email)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_customers_phone
                ON customers(phone)
                """
            )
            self._conn.commit()

    def _ensure_shipments_columns(self) -> None:
        """Backfill new shipments columns and constraints for existing databases."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("PRAGMA table_info(shipments)")
            columns = {row[1] for row in cur.fetchall()}
            if "sender_phone" not in columns:
                cur.execute("ALTER TABLE shipments ADD COLUMN sender_phone TEXT")
            if "recipient_phone" not in columns:
                cur.execute("ALTER TABLE shipments ADD COLUMN recipient_phone TEXT")

            # Guard against ambiguous verification lookups before enforcing uniqueness.
            cur.execute(
                """
                SELECT confirmation_id, COUNT(*) AS cnt
                FROM shipments
                GROUP BY confirmation_id
                HAVING COUNT(*) > 1
                LIMIT 1
                """
            )
            duplicate = cur.fetchone()
            if duplicate is not None:
                raise ValueError(
                    "Cannot enforce unique confirmation_id index due to duplicate values in shipments table."
                )

            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_shipments_confirmation_id
                ON shipments(confirmation_id)
                """
            )
            self._conn.commit()

    def _seed_if_empty(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.executemany(
                """
                INSERT OR IGNORE INTO rate_cards (service_type, base_cost, per_lb, estimated_delivery_days, carrier)
                VALUES (?, ?, ?, ?, ?)
                """,
                DEFAULT_RATE_CARDS,
            )
            self._conn.commit()

        if settings.seed_demo_data:
            self.seed_demo_data(force=False)

    def seed_demo_data(self, force: bool = False) -> Dict[str, int]:
        """
        Seed demo rows for local development.

        Args:
            force: If True, clears demo tables and re-seeds from scratch.

        Returns:
            Summary of inserted rows.
        """
        with self._lock:
            cur = self._conn.cursor()
            inserted_customers = 0
            inserted_shipments = 0

            if force:
                cur.execute("DELETE FROM complaints")
                cur.execute("DELETE FROM shipments")
                cur.execute("DELETE FROM customers")

            # Backfill required services on every startup, including existing databases.
            cur.executemany(
                """
                INSERT OR IGNORE INTO rate_cards (service_type, base_cost, per_lb, estimated_delivery_days, carrier)
                VALUES (?, ?, ?, ?, ?)
                """,
                DEFAULT_RATE_CARDS,
            )

            cur.execute("SELECT COUNT(*) AS count FROM customers")
            if cur.fetchone()["count"] == 0:
                cur.executemany(
                    """
                    INSERT INTO customers (customer_id, name, email, phone, account_status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    DEFAULT_CUSTOMERS,
                )
                inserted_customers = len(DEFAULT_CUSTOMERS)

            cur.execute("SELECT COUNT(*) AS count FROM shipments")
            if cur.fetchone()["count"] == 0:
                now = datetime.now(timezone.utc)
                seed_shipments = [
                    (
                        "123456789",
                        "CUST-10001",
                        "Loomis Store A",
                        "10 Main St",
                        "Los Angeles",
                        "CA",
                        "90210",
                        "5551234567",
                        "John Doe",
                        "22 Market St",
                        "New York",
                        "NY",
                        "10001",
                        "5551234567",
                        4.2,
                        "ground",
                        "Books",
                        "in_transit",
                        "Chicago, IL",
                        (now + timedelta(days=2)).date().isoformat(),
                        now.isoformat(),
                        "Loomis Ground",
                        18.25,
                        "CONF-SEED-001",
                        now.isoformat(),
                    ),
                    (
                        "987654321",
                        "CUST-10002",
                        "Loomis Store B",
                        "80 Pine St",
                        "Austin",
                        "TX",
                        "73301",
                        "5559876543",
                        "Jane Smith",
                        "5 Cedar Ave",
                        "Seattle",
                        "WA",
                        "98101",
                        "5559876543",
                        2.5,
                        "priority",
                        "Documents",
                        "delivered",
                        "Seattle, WA",
                        (now - timedelta(days=1)).date().isoformat(),
                        now.isoformat(),
                        "Loomis Priority",
                        20.35,
                        "CONF-SEED-002",
                        now.isoformat(),
                    ),
                ]
                cur.executemany(
                    """
                    INSERT INTO shipments (
                        tracking_number, customer_id,
                        sender_name, sender_address, sender_city, sender_state, sender_zip, sender_phone,
                        recipient_name, recipient_address, recipient_city, recipient_state, recipient_zip, recipient_phone,
                        weight_lbs, service_type, description,
                        status, current_location, estimated_delivery, last_update, carrier,
                        total_cost, confirmation_id, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    seed_shipments,
                )
                inserted_shipments = len(seed_shipments)

            self._conn.commit()
            return {
                "customers": inserted_customers,
                "shipments": inserted_shipments,
                "rate_cards": len(DEFAULT_RATE_CARDS),
            }

    def _generate_tracking_number(self) -> str:
        with self._lock:
            cur = self._conn.cursor()
            while True:
                numeric_part = "".join(secrets.choice(string.digits) for _ in range(10))
                suffix = "".join(secrets.choice(string.ascii_uppercase) for _ in range(3))
                candidate = f"{numeric_part}{suffix}"
                cur.execute(
                    "SELECT 1 FROM shipments WHERE tracking_number = ?",
                    (candidate,),
                )
                if cur.fetchone() is None:
                    return candidate

    def get_tracking(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                SELECT tracking_number, status, current_location, estimated_delivery, last_update, carrier
                FROM shipments
                WHERE tracking_number = ?
                """,
                (tracking_number,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_rates(
        self,
        origin_zip: str,
        destination_zip: str,
        weight_lbs: float,
        service_type: str,
    ) -> Dict[str, Any]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                SELECT service_type, base_cost, per_lb, estimated_delivery_days, carrier
                FROM rate_cards
                WHERE service_type = ?
                """,
                (service_type,),
            )
            rows = cur.fetchall()

        surcharge = round((get_zone_mapper().distance_zone(origin_zip, destination_zip) - 1) * 2.0, 2)
        rates = []
        for row in rows:
            cost = round(row["base_cost"] + (row["per_lb"] * weight_lbs) + surcharge, 2)
            rates.append(
                {
                    "service_type": row["service_type"],
                    "cost": cost,
                    "estimated_delivery_days": row["estimated_delivery_days"],
                    "carrier": row["carrier"],
                }
            )

        return {
            "rates": rates,
            "origin_zip": origin_zip,
            "destination_zip": destination_zip,
            "weight_lbs": weight_lbs,
        }

    def create_shipment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        tracking_number = self._generate_tracking_number()
        created_at = _utc_now_iso()
        confirmation_id = f"CONF-{uuid.uuid4().hex[:10].upper()}"
        service_type = payload["service_type"]
        rates = self.get_rates(
            origin_zip=payload["sender_zip"],
            destination_zip=payload["recipient_zip"],
            weight_lbs=payload["weight_lbs"],
            service_type=service_type,
        )
        if not rates["rates"]:
            raise ValueError(f"No rates available for service type: {service_type}")

        selected_rate = rates["rates"][0]

        required_quote_fields = ("selected_carrier", "quoted_service_type", "quoted_total_cost")
        missing_quote_fields = [field for field in required_quote_fields if payload.get(field) is None]
        if missing_quote_fields:
            raise ValueError(
                "Missing required quote consistency fields: " + ", ".join(missing_quote_fields)
            )

        expected_carrier = payload.get("selected_carrier")
        actual_carrier = selected_rate.get("carrier")
        if (
            expected_carrier
            and actual_carrier
            and actual_carrier.strip().lower() != expected_carrier.strip().lower()
        ):
            raise ValueError(
                f"Selected carrier mismatch. Expected '{expected_carrier}', got '{actual_carrier}'."
            )

        quoted_service_type = payload.get("quoted_service_type")
        if quoted_service_type and quoted_service_type != service_type:
            raise ValueError(
                f"Quoted service mismatch. Expected '{quoted_service_type}', got '{service_type}'."
            )

        quoted_total_cost = payload.get("quoted_total_cost")
        if quoted_total_cost is not None and abs(float(quoted_total_cost) - float(selected_rate["cost"])) > 0.01:
            raise ValueError(
                f"Quoted price changed from {quoted_total_cost} to {selected_rate['cost']}. Please reconfirm."
            )

        estimated_delivery = (
            datetime.now(timezone.utc) + timedelta(days=selected_rate["estimated_delivery_days"])
        ).date().isoformat()

        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO shipments (
                    tracking_number, customer_id,
                    sender_name, sender_address, sender_city, sender_state, sender_zip, sender_phone,
                    recipient_name, recipient_address, recipient_city, recipient_state, recipient_zip, recipient_phone,
                    weight_lbs, service_type, description,
                    status, current_location, estimated_delivery, last_update, carrier,
                    total_cost, confirmation_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tracking_number,
                    None,
                    payload["sender_name"],
                    payload["sender_address"],
                    payload["sender_city"],
                    payload["sender_state"],
                    payload["sender_zip"],
                    payload["sender_phone"],
                    payload["recipient_name"],
                    payload["recipient_address"],
                    payload["recipient_city"],
                    payload["recipient_state"],
                    payload["recipient_zip"],
                    payload["recipient_phone"],
                    payload["weight_lbs"],
                    service_type,
                    payload.get("description"),
                    "pending",
                    f"{payload['sender_city']}, {payload['sender_state']}",
                    estimated_delivery,
                    created_at,
                    selected_rate.get("carrier"),
                    selected_rate["cost"],
                    confirmation_id,
                    created_at,
                ),
            )
            self._conn.commit()

        return {
            "tracking_number": tracking_number,
            "estimated_delivery": estimated_delivery,
            "total_cost": selected_rate["cost"],
            "confirmation_id": confirmation_id,
            "carrier": selected_rate.get("carrier"),
        }

    def get_shipment_details(self, confirmation_id: str, phone_number: str) -> Dict[str, Any]:
        normalized_phone = "".join(ch for ch in phone_number if ch.isdigit())
        if not normalized_phone:
            raise ValueError("Phone number is required for verification.")

        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                SELECT
                    tracking_number,
                    confirmation_id,
                    status,
                    carrier,
                    estimated_delivery,
                    sender_name,
                    sender_address,
                    sender_city,
                    sender_state,
                    sender_zip,
                    recipient_name,
                    recipient_address,
                    recipient_city,
                    recipient_state,
                    recipient_zip,
                    sender_phone,
                    recipient_phone
                FROM shipments
                WHERE confirmation_id = ?
                LIMIT 1
                """,
                (confirmation_id.upper(),),
            )
            row = cur.fetchone()

        if row is None:
            raise ValueError("Verification failed. Please check confirmation ID and phone number.")

        sender_phone = "".join(ch for ch in (row["sender_phone"] or "") if ch.isdigit())
        recipient_phone = "".join(ch for ch in (row["recipient_phone"] or "") if ch.isdigit())
        if normalized_phone not in {sender_phone, recipient_phone}:
            raise ValueError("Verification failed. Please check confirmation ID and phone number.")

        details = dict(row)
        details.pop("sender_phone", None)
        details.pop("recipient_phone", None)
        return details

    def file_complaint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT 1 FROM shipments WHERE tracking_number = ?",
                (payload["tracking_number"],),
            )
            if cur.fetchone() is None:
                raise ValueError("Tracking number does not exist in local database.")

            ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"
            estimated_resolution = (
                datetime.now(timezone.utc) + timedelta(days=3)
            ).date().isoformat()
            cur.execute(
                """
                INSERT INTO complaints (
                    ticket_id, tracking_number, issue_type, description,
                    contact_email, contact_phone, status, next_steps,
                    estimated_resolution, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    payload["tracking_number"],
                    payload["issue_type"],
                    payload["description"],
                    payload["contact_email"],
                    payload.get("contact_phone"),
                    "received",
                    "Our team will investigate and contact you within 24 hours",
                    estimated_resolution,
                    _utc_now_iso(),
                ),
            )
            self._conn.commit()

        return {
            "ticket_id": ticket_id,
            "status": "received",
            "next_steps": "Our team will investigate and contact you within 24 hours",
            "estimated_resolution": estimated_resolution,
        }

    def lookup_customer(self, phone_or_email: str) -> Dict[str, Any]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                SELECT customer_id, name, email, phone, account_status
                FROM customers
                WHERE email = ? OR phone = ?
                LIMIT 1
                """,
                (phone_or_email, phone_or_email),
            )
            customer = cur.fetchone()
            if customer is None:
                raise ValueError("Customer not found.")

            cur.execute(
                """
                SELECT tracking_number, status, recipient_city, recipient_state, estimated_delivery
                FROM shipments
                WHERE customer_id = ?
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (customer["customer_id"],),
            )
            shipments = cur.fetchall()

            cur.execute(
                "SELECT COUNT(*) AS count FROM shipments WHERE customer_id = ?",
                (customer["customer_id"],),
            )
            total_count = cur.fetchone()["count"]

        recent_shipments = [
            {
                "tracking_number": row["tracking_number"],
                "status": row["status"],
                "destination_city": row["recipient_city"],
                "destination_state": row["recipient_state"],
                "estimated_delivery": row["estimated_delivery"],
            }
            for row in shipments
        ]

        return {
            "customer_id": customer["customer_id"],
            "name": customer["name"],
            "email": customer["email"],
            "phone": customer["phone"],
            "recent_shipments": recent_shipments,
            "total_shipments": total_count,
            "account_status": customer["account_status"],
        }


@cache
def get_sqlite_store() -> SQLiteDataStore:
    """Get singleton SQLite store."""
    return SQLiteDataStore()


def seed_sqlite_store(force: bool = False) -> Dict[str, int]:
    """Seed the active SQLite store with demo data."""
    return get_sqlite_store().seed_demo_data(force=force)
