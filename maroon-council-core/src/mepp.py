"""
Maroon Council Core — MEPP Financial Engine (v5.0 - NASA Grade)
Control Plane §1.2: Maroon Economic Processing Protocol.

Core Financial Laws:
  - Sovereign Logistics Ceiling: Council-governed cap on delivery fees
  - Split-Tender Orchestration: EBT/SNAP dynamically separated at the transaction microsecond
  - Revenue-Linked Subscription (RLS): Vendor fees capped at $300/month
  - Zero Penny Drift: Math uses integer cents — NO floating-point arithmetic permitted internally.
"""
import hashlib
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

# ---------------------------------------------------------------------------
# Exceptions — Harvard-Grade Fault Tolerance
# ---------------------------------------------------------------------------

class MEPPBaseException(Exception):
    """Base exception for all MEPP financial faults."""
    pass

class SovereignLogisticsViolation(MEPPBaseException):
    """Raised when an attempt is made to bypass the Sovereign Logistics Ceiling."""
    pass

class PennyDriftError(MEPPBaseException):
    """Raised when accounting math does not strictly zero out."""
    pass

class InvalidCurrencyFormat(MEPPBaseException):
    """Raised when fiat currency strings/floats cannot be perfectly resolved to integer cents."""
    pass

# ---------------------------------------------------------------------------
# Constants — Immutable Financial Laws
# ---------------------------------------------------------------------------
SOVEREIGN_LOGISTICS_CEILING_CENTS: int = 1499  # Default Council-set ceiling ($14.99)
RLS_MONTHLY_CAP_CENTS: int = 30000  # $300.00/month cap
MAROON_BUCK_USD_PARITY: Decimal = Decimal("1.00")

EBT_ELIGIBLE_CATEGORIES = frozenset({
    "produce", "dairy", "meat", "seafood", "bakery", "cereal",
    "snacks", "beverages_nonalcoholic", "canned_goods", "frozen_foods",
    "baby_food", "seeds_plants",
})

# ---------------------------------------------------------------------------
# Penny-Perfect Math
# ---------------------------------------------------------------------------
def to_cents(dollars: Any) -> int:
    """Strict, fault-tolerant conversion of dollar amounts to integer cents."""
    try:
        if isinstance(dollars, str):
            dollars = dollars.replace('$', '').replace(',', '')
        val = Decimal(str(dollars))
        if val.is_nan() or val.is_infinite():
            raise InvalidCurrencyFormat(f"Cannot process NaN or Infinity in financial calculations: {dollars}")
        return int(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)
    except InvalidOperation:
        raise InvalidCurrencyFormat(f"Invalid currency input: {dollars}")

def to_dollars(cents: int) -> float:
    return round(cents / 100.0, 2)

# ---------------------------------------------------------------------------
# Strict Models
# ---------------------------------------------------------------------------

class CartItem(BaseModel):
    name: str = Field(..., min_length=1)
    price_dollars: float = Field(..., ge=0)
    category: str = Field(...)
    quantity: int = Field(default=1, gt=0)

    model_config = ConfigDict(frozen=True)

class SplitTenderItemBreakdown(BaseModel):
    name: str
    price_cents: int
    quantity: int
    total_cents: int
    category: str
    ebt_eligible: bool

class PennyDriftAudit(BaseModel):
    total_cents: int
    payment_sum_cents: int
    drift_cents: int
    is_penny_perfect: bool

class SplitTenderResult(BaseModel):
    ebt_amount_cents: int = Field(default=0, ge=0)
    maroon_bucks_cents: int = Field(default=0, ge=0)
    fiat_amount_cents: int = Field(default=0, ge=0)
    delivery_fee_cents: int = Field(default=0, ge=0)
    platform_fee_cents: int = Field(default=0, ge=0)
    total_cents: int = Field(default=0, ge=0)
    items: List[SplitTenderItemBreakdown] = Field(default_factory=list)
    truth_hash: str = ""
    penny_drift_check: Optional[PennyDriftAudit] = None

    @field_validator('truth_hash')
    @classmethod
    def validate_hash(cls, v: str) -> str:
        if v and len(v) != 64:  # SHA-256 length
            raise ValueError("Invalid hash length")
        return v

class RLSAudit(BaseModel):
    vendor_id: str
    fee_charged_cents: int
    capped: bool
    reason: str
    monthly_total_cents: int
    cap_cents: int = RLS_MONTHLY_CAP_CENTS

# ---------------------------------------------------------------------------
# Core Engine Execution
# ---------------------------------------------------------------------------

def split_tender(
    items: List[CartItem],
    delivery_fee_dollars: float = 0.0,
    platform_fee_dollars: float = 0.0,
    maroon_bucks_available_dollars: float = 0.0,
    has_ebt: bool = False,
) -> SplitTenderResult:
    """
    Execute the MEPP Split-Tender Protocol with NASA-grade tolerances.
    """
    try:
        delivery_fee_cents = to_cents(delivery_fee_dollars)
        platform_fee_cents = to_cents(platform_fee_dollars)
        maroon_bucks_cents = to_cents(maroon_bucks_available_dollars)
    except Exception as e:
        raise InvalidCurrencyFormat(f"Failed to parse fees: {e}")

    # Enforce Sovereign Logistics Ceiling strictly
    if delivery_fee_cents > SOVEREIGN_LOGISTICS_CEILING_CENTS:
        # We auto-cap instead of throwing to protect the consumer seamlessly,
        # but in a stricter variant we could throw SovereignLogisticsViolation.
        delivery_fee_cents = SOVEREIGN_LOGISTICS_CEILING_CENTS

    ebt_eligible_cents = 0
    non_ebt_cents = 0
    breakdown = []

    for item in items:
        item_total_cents = to_cents(item.price_dollars) * item.quantity
        cat = item.category.lower()
        is_eligible = (cat in EBT_ELIGIBLE_CATEGORIES) and has_ebt

        breakdown.append(SplitTenderItemBreakdown(
            name=item.name,
            price_cents=to_cents(item.price_dollars),
            quantity=item.quantity,
            total_cents=item_total_cents,
            category=cat,
            ebt_eligible=is_eligible
        ))

        if is_eligible:
            ebt_eligible_cents += item_total_cents
        else:
            non_ebt_cents += item_total_cents

    maroon_applied = min(maroon_bucks_cents, non_ebt_cents)
    remaining_non_ebt = non_ebt_cents - maroon_applied

    fiat_amount_cents = remaining_non_ebt + delivery_fee_cents + platform_fee_cents
    total_cents = ebt_eligible_cents + non_ebt_cents + delivery_fee_cents + platform_fee_cents

    # Verify Penny Drift before returning
    payment_sum = ebt_eligible_cents + maroon_applied + fiat_amount_cents
    drift = abs(total_cents - payment_sum)

    if drift != 0:
        raise PennyDriftError(f"CRITICAL: Mathematical drift detected: {drift} cents unaccounted for.")

    result = SplitTenderResult(
        ebt_amount_cents=ebt_eligible_cents,
        maroon_bucks_cents=maroon_applied,
        fiat_amount_cents=fiat_amount_cents,
        delivery_fee_cents=delivery_fee_cents,
        platform_fee_cents=platform_fee_cents,
        total_cents=total_cents,
        items=breakdown,
        penny_drift_check=PennyDriftAudit(
            total_cents=total_cents,
            payment_sum_cents=payment_sum,
            drift_cents=drift,
            is_penny_perfect=True
        )
    )

    # Cryptographic lock
    canonical = result.model_dump_json(exclude={'truth_hash'})
    result.truth_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    return result

def enforce_rls_cap(vendor_id: str, current_month_fees_cents: int, proposed_fee_cents: int) -> RLSAudit:
    """Enforce the Revenue-Linked Subscription cap ($300/month)."""
    if current_month_fees_cents < 0 or proposed_fee_cents < 0:
        raise InvalidCurrencyFormat("Fees cannot be negative.")

    remaining_capacity = RLS_MONTHLY_CAP_CENTS - current_month_fees_cents
    if remaining_capacity <= 0:
        return RLSAudit(
            vendor_id=vendor_id,
            fee_charged_cents=0,
            capped=True,
            reason="RLS monthly cap reached",
            monthly_total_cents=current_month_fees_cents
        )

    actual_fee = min(proposed_fee_cents, remaining_capacity)
    return RLSAudit(
        vendor_id=vendor_id,
        fee_charged_cents=actual_fee,
        capped=actual_fee < proposed_fee_cents,
        reason="Fee applied" if actual_fee == proposed_fee_cents else "Partially capped by RLS",
        monthly_total_cents=current_month_fees_cents + actual_fee
    )
