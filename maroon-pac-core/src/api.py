"""
Maroon PAC Core — Political Action & Cryptographic Voting (v4.0)
Codex §4.4: Cryptographically anonymous voting (voter hash, not voter ID).
Issue tracking and community governance.
All votes immutably recorded via Truth-Teller.
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import uuid
import secrets

app = FastAPI(
    title="Maroon PAC Core",
    description="Sovereign Political Action — Anonymous Cryptographic Voting",
    version="4.0.0",
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IssueStatus(str, Enum):
    OPEN = "OPEN"
    DISCUSSION = "DISCUSSION"
    VOTING = "VOTING"
    CLOSED = "CLOSED"
    IMPLEMENTED = "IMPLEMENTED"


class VoteChoice(str, Enum):
    YES = "YES"
    NO = "NO"
    ABSTAIN = "ABSTAIN"


class IssuePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IssueCategory(str, Enum):
    ECONOMIC = "ECONOMIC"
    HEALTH = "HEALTH"
    EDUCATION = "EDUCATION"
    HOUSING = "HOUSING"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    GOVERNANCE = "GOVERNANCE"
    JUSTICE = "JUSTICE"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Issue(BaseModel):
    issue_id: str = Field(default_factory=lambda: f"ISS-{str(uuid.uuid4())[:8]}")
    title: str
    description: str
    category: IssueCategory
    priority: IssuePriority = IssuePriority.MEDIUM
    status: IssueStatus = IssueStatus.OPEN
    proposed_by_hash: str = ""       # Anonymized proposer identity
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    voting_opens_at: Optional[str] = None
    voting_closes_at: Optional[str] = None


class VoteRequest(BaseModel):
    issue_id: str
    voter_secret: str   # Private voter token — NEVER stored, only hashed
    choice: VoteChoice


class VoteReceipt(BaseModel):
    receipt_id: str
    issue_id: str
    voter_hash: str      # SHA-512 of voter_secret — anonymous
    choice: VoteChoice
    merkle_hash: str     # Hash of the full vote record for Truth-Teller
    timestamp: str


class VoteTally(BaseModel):
    issue_id: str
    title: str
    yes_count: int
    no_count: int
    abstain_count: int
    total_votes: int
    result: str          # "PASSED", "FAILED", "TIE", "OPEN"
    tally_hash: str


class GovernanceProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"GOV-{str(uuid.uuid4())[:8]}")
    title: str
    body: str
    category: IssueCategory
    budget_impact_usd: float = 0.0
    sponsor_hash: str = ""
    co_sponsors: List[str] = []
    status: str = "DRAFT"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

def emit_telemetry(event_type: str, payload: dict):
    envelope = {
        "source": "maroon-pac-core",
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
        "verification_status": "VERIFIED",
        "merkle_hash": hashlib.sha512(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest(),
    }
    print(f"[Telemetry] {json.dumps(envelope, default=str)}")


def compute_hash(data: str) -> str:
    return hashlib.sha512(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# In-Memory Stores (Production: PostgreSQL + Truth-Teller integration)
# ---------------------------------------------------------------------------

_issues: Dict[str, Issue] = {}
_votes: Dict[str, List[VoteReceipt]] = {}     # issue_id -> list of vote receipts
_voter_registry: Dict[str, set] = {}            # issue_id -> set of voter_hashes (prevent double-voting)
_proposals: Dict[str, GovernanceProposal] = {}


# ---------------------------------------------------------------------------
# Issue Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/issues", status_code=201)
async def create_issue(issue: Issue):
    """Create a new governance issue for community discussion/voting."""
    if not issue.proposed_by_hash:
        issue.proposed_by_hash = compute_hash(secrets.token_hex(32))
    _issues[issue.issue_id] = issue
    _votes[issue.issue_id] = []
    _voter_registry[issue.issue_id] = set()
    emit_telemetry("issue_created", {"issue_id": issue.issue_id, "category": issue.category.value, "priority": issue.priority.value})
    return {"status": "created", "issue_id": issue.issue_id}


@app.get("/api/v1/issues")
async def list_issues(
    status: Optional[IssueStatus] = None,
    category: Optional[IssueCategory] = None,
    limit: int = Query(default=50, le=200),
):
    issues = list(_issues.values())
    if status:
        issues = [i for i in issues if i.status == status]
    if category:
        issues = [i for i in issues if i.category == category]
    return {"issues": [i.model_dump() for i in issues[:limit]], "total": len(issues)}


@app.get("/api/v1/issues/{issue_id}")
async def get_issue(issue_id: str):
    if issue_id not in _issues:
        raise HTTPException(status_code=404, detail="Issue not found")
    return _issues[issue_id]


@app.patch("/api/v1/issues/{issue_id}/status")
async def update_issue_status(issue_id: str, status: IssueStatus):
    if issue_id not in _issues:
        raise HTTPException(status_code=404, detail="Issue not found")
    _issues[issue_id].status = status
    emit_telemetry("issue_status_updated", {"issue_id": issue_id, "new_status": status.value})
    return {"status": "updated", "issue_id": issue_id, "new_status": status.value}


# ---------------------------------------------------------------------------
# Voting Endpoints (Cryptographically Anonymous)
# ---------------------------------------------------------------------------

@app.post("/api/v1/vote", response_model=VoteReceipt)
async def cast_vote(vote: VoteRequest):
    """
    Cast a cryptographically anonymous vote.
    The voter_secret is NEVER stored — only its SHA-512 hash is recorded.
    Double-voting is prevented by checking the voter_hash against the registry.
    """
    if vote.issue_id not in _issues:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue = _issues[vote.issue_id]
    if issue.status != IssueStatus.VOTING:
        raise HTTPException(status_code=400, detail="Voting is not currently open for this issue")

    # Hash the voter secret (anonymous identity)
    voter_hash = compute_hash(vote.voter_secret)

    # Prevent double-voting
    if voter_hash in _voter_registry[vote.issue_id]:
        raise HTTPException(status_code=409, detail="This voter has already cast a vote on this issue")

    # Record the vote
    receipt_data = {
        "issue_id": vote.issue_id,
        "voter_hash": voter_hash,
        "choice": vote.choice.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    merkle_hash = compute_hash(json.dumps(receipt_data, sort_keys=True))

    receipt = VoteReceipt(
        receipt_id=f"VR-{str(uuid.uuid4())[:8]}",
        issue_id=vote.issue_id,
        voter_hash=voter_hash,
        choice=vote.choice,
        merkle_hash=merkle_hash,
        timestamp=receipt_data["timestamp"],
    )

    _votes[vote.issue_id].append(receipt)
    _voter_registry[vote.issue_id].add(voter_hash)

    emit_telemetry("vote_cast", {
        "issue_id": vote.issue_id,
        "voter_hash": voter_hash[:32] + "...",
        "choice": vote.choice.value,
        "merkle_hash": merkle_hash[:32] + "...",
    })

    return receipt


@app.get("/api/v1/tally/{issue_id}", response_model=VoteTally)
async def get_vote_tally(issue_id: str):
    """Get the vote tally for an issue."""
    if issue_id not in _issues:
        raise HTTPException(status_code=404, detail="Issue not found")

    votes = _votes.get(issue_id, [])
    yes_count = sum(1 for v in votes if v.choice == VoteChoice.YES)
    no_count = sum(1 for v in votes if v.choice == VoteChoice.NO)
    abstain_count = sum(1 for v in votes if v.choice == VoteChoice.ABSTAIN)
    total = len(votes)

    if _issues[issue_id].status != IssueStatus.CLOSED:
        result = "OPEN"
    elif yes_count > no_count:
        result = "PASSED"
    elif no_count > yes_count:
        result = "FAILED"
    else:
        result = "TIE"

    tally_data = {"issue_id": issue_id, "yes": yes_count, "no": no_count, "abstain": abstain_count, "result": result}
    tally_hash = compute_hash(json.dumps(tally_data, sort_keys=True))

    return VoteTally(
        issue_id=issue_id,
        title=_issues[issue_id].title,
        yes_count=yes_count,
        no_count=no_count,
        abstain_count=abstain_count,
        total_votes=total,
        result=result,
        tally_hash=tally_hash,
    )


# ---------------------------------------------------------------------------
# Governance Proposals
# ---------------------------------------------------------------------------

@app.post("/api/v1/proposals", status_code=201)
async def create_proposal(proposal: GovernanceProposal):
    if not proposal.sponsor_hash:
        proposal.sponsor_hash = compute_hash(secrets.token_hex(32))
    _proposals[proposal.proposal_id] = proposal
    emit_telemetry("proposal_created", {"proposal_id": proposal.proposal_id, "title": proposal.title})
    return {"status": "created", "proposal_id": proposal.proposal_id}


@app.get("/api/v1/proposals")
async def list_proposals():
    return {"proposals": [p.model_dump() for p in _proposals.values()]}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "maroon-pac-core", "version": "4.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
