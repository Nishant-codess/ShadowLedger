"""Data normalization engine for multi-source financial records."""

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.domain.enums import EventType, ValuationBasis
from app.domain.models import InventoryMove, Observation


def parse_utc_timestamp(val: Any) -> datetime:
    """Parse various timestamp formats into a timezone-aware UTC datetime."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=UTC)
        return val.astimezone(UTC)

    if isinstance(val, (int, float)):
        # Handle epoch timestamps in seconds or milliseconds
        if val > 1e11:  # milliseconds
            return datetime.fromtimestamp(val / 1000.0, tz=UTC)
        return datetime.fromtimestamp(val, tz=UTC)

    if isinstance(val, str):
        val_clean = val.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(val_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(UTC)
        except ValueError:
            # Try alternate common banking formats
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d",
            ):
                try:
                    dt = datetime.strptime(val_clean, fmt)
                    return dt.replace(tzinfo=UTC)
                except ValueError:
                    continue

    return datetime.now(UTC)


def normalize_amount(val: Any) -> Decimal:
    """Normalize numerical amounts into standard 2-decimal Decimal values."""
    if isinstance(val, Decimal):
        return val.quantize(Decimal("0.01"))

    if isinstance(val, (int, float)):
        return Decimal(str(val)).quantize(Decimal("0.01"))

    if isinstance(val, str):
        # Clean currency symbols, commas, whitespace
        cleaned = val.replace("₹", "").replace("INR", "").replace(",", "").replace("$", "").strip()
        try:
            return Decimal(cleaned).quantize(Decimal("0.01"))
        except InvalidOperation:
            return Decimal("0.00")

    return Decimal("0.00")


def normalize_record(raw: dict[str, Any], batch_id: str = "default") -> tuple[Observation, InventoryMove | None]:
    """Transform a raw source record dict into a canonical Observation and optional InventoryMove."""
    source_system = str(raw.get("source_system", "pos")).lower().strip()
    source_record_id = str(raw.get("source_record_id", raw.get("id", "")))
    raw_event_type = str(raw.get("event_type", "payment")).lower().strip()

    try:
        event_type = EventType(raw_event_type)
    except ValueError:
        event_type = EventType.PAYMENT

    amount = normalize_amount(raw.get("amount", 0))
    timestamp = parse_utc_timestamp(raw.get("timestamp", datetime.now(UTC)))
    currency = str(raw.get("currency", "INR")).upper().strip()
    description = str(raw.get("description", ""))

    # Extract entity IDs
    entity_ids: dict[str, str] = {}
    if "entity_ids" in raw and isinstance(raw["entity_ids"], dict):
        entity_ids = {str(k): str(v) for k, v in raw["entity_ids"].items()}
    else:
        for key in ("order_id", "payment_id", "merchant_id", "customer_id", "driver_id", "passenger_id", "batch_ref"):
            if key in raw:
                entity_ids[key] = str(raw[key])

    obs = Observation(
        source_system=source_system,
        source_record_id=source_record_id,
        raw_payload=raw,
        event_type=event_type,
        amount=amount,
        currency=currency,
        timestamp=timestamp,
        entity_ids=entity_ids,
        description=description,
        batch_id=batch_id,
    )

    # Check for inventory movement payload
    inv_move = None
    if "inventory_move" in raw and isinstance(raw["inventory_move"], dict):
        inv_raw = raw["inventory_move"]
        basis_raw = str(inv_raw.get("valuation_basis", "unknown")).lower()
        try:
            val_basis = ValuationBasis(basis_raw)
        except ValueError:
            val_basis = ValuationBasis.UNKNOWN

        inv_move = InventoryMove(
            observation_id=obs.observation_id,
            sku=inv_raw.get("sku"),
            item_description=str(inv_raw.get("item_description", "Inventory Item")),
            quantity=Decimal(str(inv_raw.get("quantity", 1.0))),
            unit_cost=normalize_amount(inv_raw.get("unit_cost")) if "unit_cost" in inv_raw else None,
            retail_value=normalize_amount(inv_raw.get("retail_value")) if "retail_value" in inv_raw else None,
            valuation_basis=val_basis,
            linked_order_id=inv_raw.get("linked_order_id") or entity_ids.get("order_id"),
            timestamp=obs.timestamp,
        )

    return obs, inv_move
