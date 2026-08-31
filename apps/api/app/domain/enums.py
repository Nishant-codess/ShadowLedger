"""Domain enumerations for ShadowLedger."""

from enum import StrEnum


class EventType(StrEnum):
    """Types of financial and economic events."""

    PAYMENT = "payment"
    SETTLEMENT = "settlement"
    REFUND = "refund"
    FEE = "fee"
    ADJUSTMENT = "adjustment"
    INVENTORY_MOVE = "inventory_move"
    CREDIT_ISSUE = "credit_issue"
    CREDIT_REDEEM = "credit_redeem"
    REVERSAL = "reversal"


class EventStatus(StrEnum):
    """Strict Four-Level Event Taxonomy.

    Level 1: OBSERVED             - Fact directly observed in a source record.
    Level 2: DERIVED              - Mathematically implied from observed records.
    Level 3: INFERRED_LATENT      - Unrecorded but strongly supported latent event.
    Level 4: UNOBSERVED_DEVIATION - Discrepancy pattern detected without direct transaction record.
                                    NEVER allowed to auto-resolve.
    """

    OBSERVED = "observed"
    DERIVED = "derived"
    INFERRED_LATENT = "inferred_latent"
    UNOBSERVED_DEVIATION = "unobserved_deviation"


class HypothesisType(StrEnum):
    """Categorization of candidate latent economic events."""

    REFUND = "refund"
    FEE_ADJUSTMENT = "fee_adjustment"
    PARTIAL_SETTLEMENT = "partial_settlement"
    INVENTORY_SETTLEMENT = "inventory_settlement"
    STORE_CREDIT = "store_credit"
    DUPLICATE_REVERSAL = "duplicate_reversal"
    TIMING_OFFSET = "timing_offset"
    MISSING_PAYMENT = "missing_payment"
    OFF_LEDGER_DEVIATION = "off_ledger_deviation"
    UNKNOWN = "unknown"


class ValueType(StrEnum):
    """Economic value denomination."""

    CASH = "cash"
    INVENTORY = "inventory"
    CREDIT = "credit"
    OBLIGATION = "obligation"


class DecisionType(StrEnum):
    """Explicit decision gate outcomes."""

    AUTO_RESOLVE = "auto_resolve"
    HUMAN_REVIEW = "human_review"
    UNRESOLVED = "unresolved"


class ValuationBasis(StrEnum):
    """Valuation basis for non-cash and inventory items."""

    RETAIL = "retail"
    COST = "cost"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class SourceSystem(StrEnum):
    """Source system categories."""

    POS = "pos"
    BANK = "bank"
    GATEWAY = "gateway"
    INVENTORY = "inventory"
    RIDE_PLATFORM = "ride_platform"


class ActionRisk(StrEnum):
    """Financial and operational risk classification for actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReconciliationStatus(StrEnum):
    """Deterministic matching status."""

    MATCHED = "matched"
    UNMATCHED = "unmatched"
    PARTIALLY_MATCHED = "partially_matched"
    DUPLICATE = "duplicate"
    ANOMALY = "anomaly"
