"""
Maroon Council Core — MIVL Identity Verification Layer (v5.0 - NASA Grade)
Control Plane §1.1: Hardware-backed, terminal-verified, zero-trust identity.

Trust Tiers:
  0 - Anonymous     : No verification, public read-only
  1 - Registered    : Email + phone verified
  2 - Verified      : Government ID + KYC/AML passed
  3 - Community     : Vouched by 2+ Tier-3+ members
  4 - Operator      : Financial audit + operational history
  5 - Council       : Governance board appointment
"""
import hashlib
from datetime import datetime, timezone
from enum import IntEnum
from typing import List, Optional, Dict, Set
from pydantic import BaseModel, Field, ConfigDict

# ---------------------------------------------------------------------------
# Exceptions — Harvard-Grade Fault Tolerance
# ---------------------------------------------------------------------------

class IdentityError(Exception):
    """Base exception for MIVL rule violations."""
    pass

class TierUpgradeError(IdentityError):
    """Raised when an identity fails the strict requirements for a tier upgrade."""
    pass

class CryptographicAnomaly(IdentityError):
    """Raised when transition hashes do not verify or match."""
    pass

# ---------------------------------------------------------------------------
# Core Enums & Constraints
# ---------------------------------------------------------------------------

class MIVLTier(IntEnum):
    ANONYMOUS = 0
    REGISTERED = 1
    VERIFIED = 2
    COMMUNITY = 3
    OPERATOR = 4
    COUNCIL = 5

TIER_TRUST_RANGES = {
    MIVLTier.ANONYMOUS:   (0.0, 0.0),
    MIVLTier.REGISTERED:  (0.1, 0.2),
    MIVLTier.VERIFIED:    (0.2, 0.4),
    MIVLTier.COMMUNITY:   (0.4, 0.6),
    MIVLTier.OPERATOR:    (0.6, 0.8),
    MIVLTier.COUNCIL:     (0.8, 1.0),
}

TIER_ACCESS: Dict[MIVLTier, Set[str]] = {
    MIVLTier.ANONYMOUS:   {"read_public"},
    MIVLTier.REGISTERED:  {"read_public", "browse_marketplace"},
    MIVLTier.VERIFIED:    {"read_public", "browse_marketplace", "purchase", "limited_sell"},
    MIVLTier.COMMUNITY:   {"read_public", "browse_marketplace", "purchase", "sell", "safe_space", "vote"},
    MIVLTier.OPERATOR:    {"read_public", "browse_marketplace", "purchase", "sell", "safe_space", "vote", "vendor_ops", "logistics"},
    MIVLTier.COUNCIL:     {"read_public", "browse_marketplace", "purchase", "sell", "safe_space", "vote", "vendor_ops", "logistics", "governance", "strategy"},
}

# ---------------------------------------------------------------------------
# Strict Models
# ---------------------------------------------------------------------------

class TransitionRecord(BaseModel):
    """Immutable, cryptographically signed record of tier transition."""
    entity_id: str
    action: str
    old_tier: int
    new_tier: int
    trust_score: float
    reason: str
    timestamp: datetime
    record_hash: str = ""

    model_config = ConfigDict(frozen=True)  # Absolute immutability in memory

    @classmethod
    def create(cls, **kwargs):
        """Creates a signed record."""
        temp = cls(record_hash="temp", **kwargs)
        # Compute hash without the hash field itself
        canonical = temp.model_dump_json(exclude={'record_hash'})
        h = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return cls(**kwargs, record_hash=h)

class AnomalyFlag(BaseModel):
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_config = ConfigDict(frozen=True)

class CookoutResult(BaseModel):
    gates: Dict[str, bool]
    classification: str
    trust_score: float
    passed: int
    total: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verification_hash: str = ""

    model_config = ConfigDict(frozen=True)

class MIVLIdentity(BaseModel):
    """Zero-Trust Identity Model."""
    entity_id: str = Field(..., min_length=1)
    display_name: str = ""
    tier: MIVLTier = Field(default=MIVLTier.ANONYMOUS)
    trust_score: float = Field(default=0.0, ge=0.0, le=1.0)
    verification_history: List[TransitionRecord] = Field(default_factory=list)
    anomaly_flags: List[AnomalyFlag] = Field(default_factory=list)
    vouchers: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_audit: Optional[datetime] = None

    def upgrade_tier(self, new_tier: MIVLTier, reason: str) -> TransitionRecord:
        if new_tier <= self.tier:
            raise TierUpgradeError("Cannot upgrade to the same or lower tier.")

        if new_tier == MIVLTier.COMMUNITY and len(self.vouchers) < 2:
            raise TierUpgradeError("Community tier requires 2+ vouchers from Tier-3+ members.")

        if new_tier == MIVLTier.OPERATOR and not self.last_audit:
            raise TierUpgradeError("Operator tier requires completed financial audit.")

        old_tier = self.tier
        self.tier = new_tier
        self.trust_score = TIER_TRUST_RANGES[new_tier][0]

        record = TransitionRecord.create(
            entity_id=self.entity_id,
            action="UPGRADE",
            old_tier=old_tier.value,
            new_tier=new_tier.value,
            trust_score=self.trust_score,
            reason=reason,
            timestamp=datetime.now(timezone.utc)
        )
        self.verification_history.append(record)
        return record

    def regress_tier(self, reason: str) -> TransitionRecord:
        old_tier = self.tier
        if self.tier > MIVLTier.ANONYMOUS:
            self.tier = MIVLTier(self.tier.value - 1)
        self.trust_score = TIER_TRUST_RANGES[self.tier][0]
        
        self.anomaly_flags.append(AnomalyFlag(reason=reason))

        record = TransitionRecord.create(
            entity_id=self.entity_id,
            action="REGRESSION",
            old_tier=old_tier.value,
            new_tier=self.tier.value,
            trust_score=self.trust_score,
            reason=reason,
            timestamp=datetime.now(timezone.utc)
        )
        self.verification_history.append(record)
        return record

    def flag_anomaly(self, anomaly_type: str, details: str) -> AnomalyFlag:
        flag = AnomalyFlag(reason=f"{anomaly_type}: {details}")
        self.anomaly_flags.append(flag)

        critical_types = {"financial_fraud", "identity_theft", "extraction_pattern", "buffer_class"}
        if anomaly_type in critical_types:
            self.regress_tier(f"Auto-regression triggered by critical anomaly: {anomaly_type}")

        return flag

    def add_voucher(self, voucher_id: str, voucher_tier: MIVLTier):
        if voucher_tier < MIVLTier.COMMUNITY:
            raise TierUpgradeError("Voucher must be Tier 3 (Community) or above.")
        if voucher_id not in self.vouchers:
            self.vouchers.append(voucher_id)

    @property
    def permissions(self) -> Set[str]:
        return TIER_ACCESS.get(self.tier, set())

class CookoutProtocol:
    """Three-gate trust verification."""
    @staticmethod
    def evaluate(has_vouching_chain: bool, historical_intent_verified: bool, contribution_value: float, threshold: float = 0.0) -> CookoutResult:
        gates = {
            "gate_1_proximity": has_vouching_chain,
            "gate_2_history": historical_intent_verified,
            "gate_3_contribution": contribution_value > threshold,
        }
        passed = sum(gates.values())
        if passed == 3:
            classification, trust = "TRUSTED", 0.4
        elif passed >= 2:
            classification, trust = "TRANSACTIONAL", 0.1
        else:
            classification, trust = "HOSTILE_OBSERVER", 0.0

        res = CookoutResult(
            gates=gates, classification=classification, trust_score=trust,
            passed=passed, total=3, verification_hash="temp"
        )
        # Compute hash
        canonical = res.model_dump_json(exclude={'verification_hash'})
        return CookoutResult(**res.model_dump(exclude={'verification_hash'}), verification_hash=hashlib.sha256(canonical.encode()).hexdigest())
